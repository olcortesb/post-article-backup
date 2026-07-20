# AWS Lambda Self-Managed Code Storage: Adiós al límite de 75GB 🪣

## Contexto

En proyectos donde se despliegan muchas funciones Lambda y capas (*layers*) con dependencias pesadas, el límite de almacenamiento de código por región empieza a doler. El límite histórico era de **75GB por región por cuenta** que parece bastante pero sabemos que cada vez se necesitan grandes cantidades de datos en formato de código fuente o librerías, y ampliarlo implicaba abrir un ticket de soporte para solicitar un aumento de cuota. No es el proceso más ágil del mundo, (tampoco el más complicado!!!).

Sin embargo, el 17 de julio de 2026, AWS publicó en el Compute Blog los detalles de **self-managed code storage para AWS Lambda**. En este [*post*](https://aws.amazon.com/es/blogs/compute/introducing-self-managed-amazon-s3-buckets-for-aws-lambda-function-code/) exploro qué es, cómo funciona y cuándo tiene sentido usarla.

## ¿Qué es Lambda Self-Managed Code Storage?

Hasta ahora, cada vez que creabas o actualizabas una función Lambda o un *layer*, AWS copiaba tu paquete de despliegue a un almacenamiento gestionado por Lambda. Esa copia contaba contra el límite de 75GB.

Con **self-managed code storage**, Lambda referencia tu código directamente desde tu propio bucket de S3, **sin crear una copia intermedia**. Esto tiene varias consecuencias:

- **Sin límite de almacenamiento de código**: el límite pasa a ser el de tu bucket S3
- **Activación más rápida**: al eliminar el paso de copia, las funciones se activan antes. En pruebas de AWS con una función Python 3.13 de 200MB, el tiempo de creación fue ~5 segundos menor que con `COPY`
- **Control total de seguridad y compliance**: puedes aplicar tus propias políticas de cifrado, acceso, Object Lock y auditoría
- **Disaster recovery**: puedes usar S3 Cross-Region Replication para mantener copias de respaldo del código en otra región

> **Referencia oficial**: [AWS Lambda Developer Guide - Self-managed code storage](https://docs.aws.amazon.com/lambda/latest/dg/configuration-function-zip.html)

Adicionalmente, AWS subió el límite por defecto del almacenamiento gestionado por Lambda de **75GB a 300GB** por región por cuenta. Así que incluso si no adoptas self-managed storage, ya tienes más margen.

##  ¿Cómo funciona?

El parámetro clave es `S3ObjectStorageMode`. Tiene dos valores posibles:

| Valor | Comportamiento |
|-------|---------------|
| `COPY` | Comportamiento anterior: Lambda copia el paquete a su almacenamiento gestionado (default) |
| `REFERENCE` | Nuevo: Lambda referencia el objeto S3 directamente, sin copiar |

Para usar `REFERENCE`, hay un requisito de permisos: el *service principal* de Lambda necesita `s3:GetObject` y `s3:GetObjectVersion` sobre tu bucket.

##  Implementación

### Política del bucket S3

Primero, el bucket debe permitir que Lambda acceda al código. AWS recomienda usar la condición `aws:SourceArn` para seguir el principio de mínimo privilegio, y apuntar el `Resource` al objeto específico en lugar de un wildcard:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "LambdaSelfManagedCodeAccess",
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": [
        "s3:GetObject",
        "s3:GetObjectVersion"
      ],
      "Resource": "arn:aws:s3:::your-lambda-code-bucket/deployments/my-function.zip",
      "Condition": {
        "ArnLike": {
          "aws:SourceArn": "arn:aws:lambda:us-east-1:123456789012:function:my-function"
        }
      }
    }
  ]
}
```

> Si usas SSE-KMS con una clave gestionada por el cliente, el principal de Lambda también necesita `kms:Decrypt` sobre esa clave.

### Con AWS CLI

```bash
# Crear función con self-managed storage
aws lambda create-function \
  --function-name my-function \
  --runtime python3.13 \
  --role arn:aws:iam::123456789012:role/lambda-role \
  --handler app.handler \
  --code S3Bucket=your-lambda-code-bucket,S3Key=deployments/my-function.zip,S3ObjectVersion=abc123,S3ObjectStorageMode=REFERENCE

# Actualizar función existente a self-managed storage
aws lambda update-function-code \
  --function-name my-function \
  --s3-bucket your-lambda-code-bucket \
  --s3-key deployments/my-function.zip \
  --s3-object-version def456 \
  --s3-object-storage-mode REFERENCE
```

Nota que incluimos `S3ObjectVersion` en ambos comandos. Esto es importante: el versionado del bucket es **obligatorio** para usar `REFERENCE` mode (más sobre esto en las consideraciones).

### Con Terraform

> ⚠️ **Estado del soporte (19 de julio 2026)**: el argumento `s3_object_storage_mode` aún **no está implementado** en el provider `hashicorp/aws` de Terraform. La feature fue lanzada el 17 de julio de 2026 y el provider está pendiente de actualización. Puedes seguir el issue en el [repositorio del provider](https://github.com/hashicorp/terraform-provider-aws).

Por ahora, con Terraform puedes gestionar la infraestructura S3 (bucket, versioning, bucket policy, subida del zip) y delegar el despliegue de la función a CloudFormation o CLI:

```hcl
resource "aws_s3_bucket" "lambda_code" {
  bucket        = "your-lambda-code-bucket"
  force_destroy = true
}

resource "aws_s3_bucket_versioning" "lambda_code" {
  bucket = aws_s3_bucket.lambda_code.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_policy" "lambda_code" {
  bucket     = aws_s3_bucket.lambda_code.id
  depends_on = [aws_s3_bucket_versioning.lambda_code]

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "LambdaSelfManagedCodeStorage"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = ["s3:GetObject", "s3:GetObjectVersion"]
      Resource  = "${aws_s3_bucket.lambda_code.arn}/deployments/*"
      Condition = {
        StringEquals = {
          "aws:SourceAccount" = data.aws_caller_identity.current.account_id
        }
      }
    }]
  })
}

resource "aws_s3_object" "function_code" {
  bucket     = aws_s3_bucket.lambda_code.id
  key        = "deployments/my-function.zip"
  source     = "my-function.zip"
  etag       = filemd5("my-function.zip")
  depends_on = [aws_s3_bucket_versioning.lambda_code]
}

# Outputs para pasar a CloudFormation o CLI
output "bucket_name"       { value = aws_s3_bucket.lambda_code.id }
output "s3_key"            { value = aws_s3_object.function_code.key }
output "s3_object_version" { value = aws_s3_object.function_code.version_id }
```

Cuando el provider agregue soporte, bastará con añadir `s3_object_storage_mode = "REFERENCE"` al recurso `aws_lambda_function` existente.

### Con AWS CloudFormation

```yaml
MyFunction:
  Type: AWS::Lambda::Function
  Properties:
    FunctionName: my-function
    Runtime: python3.13
    Role: !GetAtt LambdaRole.Arn
    Handler: app.handler
    Code:
      S3Bucket: your-lambda-code-bucket
      S3Key: deployments/my-function.zip
      S3ObjectVersion: abc123
      S3ObjectStorageMode: REFERENCE
```

> Al momento de escribir este artículo, AWS confirma soporte vía **CLI y CloudFormation**. El provider de Terraform está pendiente de actualización. Verifica la documentación de SAM y SDKs para el estado actualizado de soporte.

##  Costos

No hay cargos adicionales de Lambda por usar self-managed storage. Solo pagas:

- **Almacenamiento S3 estándar** por los objetos en tu bucket
- **Requests S3** por cada acceso que Lambda hace al objeto
- **Transferencia de datos cross-region** si el bucket está en una región diferente a la función (esto es importante tenerlo en cuenta)

Comparado con el modelo anterior donde Lambda gestionaba el almacenamiento sin costo explícito, ahora pagas el S3 directamente. Para la mayoría de los casos el costo es mínimo, pero si tienes muchos *layers* pesados con dependencias de ML, vale la pena hacer el cálculo.

## 📊 Comparación: COPY vs REFERENCE

| Aspecto | `COPY` (default) | `REFERENCE` (nuevo) |
|---------|-----------------|---------------------|
| Almacenamiento cuenta contra cuota Lambda | ✅ Sí | ❌ No |
| Límite de almacenamiento | 300GB (antes 75GB) | Límite del bucket S3 |
| Tiempo de activación | Mayor (incluye copia) | Menor (~5s menos en 200MB) |
| Fuente de verdad del código | Lambda-managed storage | Tu bucket S3 |
| Control de cifrado y compliance | ❌ No | ✅ Sí |
| Disaster recovery con CRR | ❌ No | ✅ Sí |
| Costo de almacenamiento | Incluido en Lambda | S3 estándar + requests |
| Versionado requerido | ❌ No | ✅ Sí (obligatorio) |
| Disponibilidad | Todas las regiones comerciales | Todas las regiones estándar (non-opt-in) |
| Edición de código en consola | ✅ Disponible | ❌ No disponible |

## 💡 Casos de Uso

### Pipelines de CI/CD
Con `REFERENCE`, tu pipeline sube el artefacto una sola vez a S3 y Lambda lo referencia directamente. Un único conjunto de lifecycle rules y controles de acceso cubre todos los artefactos. Los rollbacks se reducen a apuntar la función a una versión anterior del objeto S3.

### Arquitecturas multi-cuenta
Un patrón común en organizaciones con AWS Organizations es centralizar los artefactos en una cuenta de tooling y dar acceso cross-account a las cuentas de workload mediante bucket policies. Con `REFERENCE` esto encaja perfectamente: una sola fuente de verdad con políticas consistentes de cifrado, versionado y retención.

### Disaster Recovery
Como el objeto S3 es la copia canónica, puedes usar S3 Cross-Region Replication (CRR) para mantener copias en una región secundaria. Si la región primaria tiene problemas, actualizas las funciones para referenciar los objetos replicados.

### Cuándo quedarte con `COPY`:
- Tienes pocas funciones y el límite de 300GB es más que suficiente
- No quieres gestionar políticas adicionales en el bucket ni el versionado obligatorio
- Tu bucket de código está en una región diferente y quieres evitar costos de transferencia

## ⚠️ Consideraciones Importantes

### Versionado del bucket (obligatorio)
El versionado **no es opcional** en `REFERENCE` mode, es un requisito. Lambda necesita referenciar un artefacto específico e inmutable para protegerse contra sobreescrituras accidentales.

```bash
aws s3api put-bucket-versioning \
  --bucket your-lambda-code-bucket \
  --versioning-configuration Status=Enabled
```

### Disponibilidad del objeto es tu responsabilidad
En `REFERENCE` mode, si el objeto S3 se elimina, la bucket policy cambia, o la KMS key se deshabilita, **la función pasa al estado `Inactive`** y los cold starts fallarán. Para restaurarla hay que restablecer el acceso al objeto y luego actualizar la función. Esto es un cambio importante respecto al modelo `COPY` donde Lambda tenía su propia copia.

### Edición de código en la consola
En `COPY` mode, la consola de AWS Lambda permite editar el código directamente desde el editor web integrado (para funciones pequeñas). En `REFERENCE` mode **esta opción no está disponible** — el código vive en S3 y Lambda no tiene una copia editable. Cualquier cambio debe hacerse subiendo una nueva versión del objeto S3 y actualizando la función para referenciarla. Esto refuerza el modelo de despliegue basado en artefactos, pero elimina la posibilidad de hacer cambios rápidos desde la consola.

### Lifecycle policies para gestión de versiones
Con el versionado habilitado, las versiones antiguas de los objetos se acumulan. Conviene configurar lifecycle policies para gestionar el crecimiento:

```json
{
  "Rules": [{
    "ID": "DeleteOldDeploymentPackages",
    "Status": "Enabled",
    "Filter": { "Prefix": "deployments/" },
    "NoncurrentVersionExpiration": {
      "NoncurrentDays": 14,
      "NewerNoncurrentVersions": 2
    }
  }]
}
```

Esta regla mantiene las 2 versiones no-current más recientes (rollback path) y elimina todo lo anterior a 14 días.

### Permisos
El *service principal* `lambda.amazonaws.com` necesita acceso al bucket. Usa `aws:SourceArn` para limitar qué función puede acceder a qué objeto. Si usas SSE-KMS, el principal de Lambda también necesita `kms:Decrypt`.

### Cross-region
Self-managed storage soporta crear funciones cross-region dentro de una partición para regiones estándar (non-opt-in). Sin embargo, si el bucket está en una región diferente a la función, se aplican cargos de transferencia de datos y hay latencia adicional en la activación. Para workloads donde la velocidad de despliegue es crítica, mantén bucket y funciones en la misma región.

## 📋 Conclusiones

Esta *feature* resuelve un problema real que muchos equipos han enfrentado al escalar el número de funciones Lambda. Los puntos clave:

- **Elimina el límite práctico de almacenamiento de código**: ya no necesitas tickets de soporte para aumentar la cuota

- **Activación más rápida**: sin el paso de copia, las funciones están disponibles antes tras una actualización

- **Fuente de verdad en tu cuenta**: el código vive en tu bucket, bajo tu control y tus políticas

- **Compatible con las herramientas principales**: CLI y CloudFormation confirmados. Terraform pendiente de actualización del provider (`hashicorp/aws`). Verifica SAM y SDKs en documentación oficial.

- **Gestión adicional**: necesitas mantener el bucket, sus políticas y el versionado

- **Costo de S3**: mínimo en la mayoría de los casos, pero hay que considerarlo en arquitecturas con muchos *layers* pesados

- **Cross-region**: evitar tener el bucket en una región diferente a las funciones si la velocidad de despliegue es crítica

- **Disponibilidad del objeto**: en `REFERENCE` mode, si el objeto S3 no está accesible, la función queda `Inactive`

- **Sin editor en consola**: en `REFERENCE` mode no es posible editar el código desde la consola de AWS Lambda. Cualquier cambio requiere subir una nueva versión a S3 y actualizar la función.

El aumento del límite por defecto de 75GB a 300GB es también una buena noticia para quienes no quieran adoptar self-managed storage de inmediato. En cualquier caso, para equipos con pipelines de CI/CD maduros que ya suben artefactos a S3, adoptar `REFERENCE` es un cambio natural que simplifica el flujo y elimina una restricción operativa.

## 🔗 Referencias

- [AWS Lambda Developer Guide - Self-managed code storage](https://docs.aws.amazon.com/lambda/latest/dg/configuration-function-zip.html)
- [AWS Compute Blog - Introducing self-managed Amazon S3 buckets for AWS Lambda function code](https://aws.amazon.com/blogs/compute/introducing-self-managed-amazon-s3-buckets-for-aws-lambda-function-code/)
- [AWS Lambda announces self-managed code storage](https://aws.amazon.com/about-aws/whats-new/2026/07/aws-lambda-self-managed-code-storage/)
- [AWS Lambda Quotas](https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html)
- [S3 Lifecycle Configuration](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lifecycle-mgmt.html)
- [S3 Cross-Region Replication](https://docs.aws.amazon.com/AmazonS3/latest/userguide/replication.html)
- [Terraform AWS Lambda Function](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_function)
- [Código de ejemplo - aws-examples](https://github.com/olcortesb/aws-examples/tree/main/s3/lambda-self-managed-storage)

Gracias por leer.

¡Saludos!

Oscar Cortés

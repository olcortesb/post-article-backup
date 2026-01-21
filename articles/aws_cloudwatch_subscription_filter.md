# Agregando reactividad ⚡ a nuestras arquitecturas con AWS CloudWatch Subscription Filter

## Introducción

Uno de los principales desafíos al implementar sistemas basados en eventos es lograr la **reactividad** necesaria para que respondan automáticamente ante eventos específicos. Cuando integramos sistemas tradicionales de request-response con arquitecturas gestionadas por eventos, siempre surge la necesidad de agregar esta capacidad reactiva.

En esta búsqueda constante de soluciones robustas para agregar reactividad a los sistemas, hoy presento una prueba de concepto utilizando una de esas *features* que están "escondidas" dentro de los servicios de AWS. Exploraremos **AWS CloudWatch Subscription Filter** como una herramienta poderosa para agregar reactividad automática a nuestros sistemas. 

La intención de esta **POC** (Proof of Concept) es utilizar **AWS CloudWatch Subscription Filter** para procesar logs automáticamente y ejecutar acciones basadas en el contenido de los mismos. Crearemos una arquitectura serverless que captura logs específicos y los procesa en tiempo real.

## 🚀 ¿Qué es AWS CloudWatch Subscription Filter?

AWS CloudWatch Subscription Filter es una *feature* que permite **filtrar y procesar logs en "tiempo real"** desde CloudWatch Logs. Cuando los logs coinciden con un patrón específico, el filtro puede enviar automáticamente esos datos a destinos como Lambda, Kinesis Data Streams, o Amazon Data Firehose. En este *post* vamos a explorar la integración con AWS Lambda específicamente.

> [AWS CloudWatch Logs Subscription Filters](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/SubscriptionFilters.html)

## 🏗️ Arquitectura de la POC

Nuestra implementación sigue este flujo:

1. **API Gateway** → Recibe POST requests
2. **Lambda Controller** → Procesa el POST y loggea siempre
3. **CloudWatch Subscription Filter** → Captura logs con `enable=true` automáticamente
4. **Lambda Processor** → Procesa logs capturados y guarda en **DynamoDB**

![Architecture](/images/architecture-subscription-filter-1.png)

## 🛠️ Implementación

### Lambda Controller

La Lambda Controller recibe los POST requests y genera logs específicos que serán capturados por el subscription filter. Aquí es importante anotar que esta lambda podría ser cualquier log de nuestro sistema tradicional o reactivo que tenga la capacidad de escribir logs en CloudWatch.

```python
import json
from datetime import datetime

def handler(event, context):
    try:
        body = json.loads(event['body'])
        
        # Log específico para el subscription filter
        if body.get('enable', False):
            print(f"✅ ORIGINAL_POST: {json.dumps(body)}")
            response_message = "POST logged - subscription filter will process it"
        else:
            print(f"❌ POST received but enable=false: {json.dumps(body)}")
            response_message = "POST received but enable=false, not processed"
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': response_message,
                'received_data': body,
                'timestamp': datetime.utcnow().isoformat()
            })
        }
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}
```

### ⚙️ CloudWatch Subscription Filter

El filtro se configura para capturar únicamente logs que contengan el patrón `✅ ORIGINAL_POST`. Es importante destacar que este patrón lo agrego en la lambda cuando el post cumple las condiciones de `enable:true`. Destaco la manera cómo se configura el filtro; aunque hay límites en el número de filtros que se pueden configurar por log group ([Ref](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/cloudwatch_limits_cwl.html)), la forma de agregar filtros es muy simple.

```c
# Ejemplo en Terraform de cómo configurar un subscription filter
resource "aws_cloudwatch_log_subscription_filter" "posts_filter" {
  name            = "${var.project_name}-posts-filter"
  log_group_name  = aws_cloudwatch_log_group.controller_lambda_logs.name
  filter_pattern  = "✅ ORIGINAL_POST"
  destination_arn = aws_lambda_function.processor_lambda.arn
}
```

### Lambda Processor

La Lambda Processor recibe los logs filtrados, los descomprime y procesa el contenido. En este caso, a diferencia de la lambda controller, sí necesitamos esta lambda para que procese el log y se active ante el evento del subscription filter. 

```python
import json
import boto3
import gzip
import base64
import uuid
from datetime import datetime

def handler(event, context):
    try:
        table = boto3.resource('dynamodb').Table(os.environ['DYNAMODB_TABLE'])
        
        # Descomprimir datos de CloudWatch Logs
        # Este punto es importante: CloudWatch envía los datos codificados 
        # en base64, hay que decodificarlos primero antes de trabajarlos
        compressed_payload = base64.b64decode(event['awslogs']['data'])
        uncompressed_payload = gzip.decompress(compressed_payload)
        log_data = json.loads(uncompressed_payload)
        
        # Procesar cada evento de log
        for log_event in log_data['logEvents']:
            message = log_event['message']
            
            if '✅ ORIGINAL_POST:' in message:
                # Extraer JSON del POST original
                json_start = message.find('{')
                if json_start != -1:
                    original_post = json.loads(message[json_start:])
                    
                    # Guardar en DynamoDB
                    item = {
                        'id': str(uuid.uuid4()),
                        'original_post': original_post,
                        'timestamp': datetime.utcnow().isoformat(),
                        'processed_at': datetime.utcnow().isoformat()
                    }
                    
                    table.put_item(Item=item)
                    print(f"Saved to DynamoDB: {item['id']}")
        
        return {'statusCode': 200, 'body': 'Successfully processed logs'}
    except Exception as e:
        print(f"Error processing logs: {str(e)}")
        return {'statusCode': 500, 'body': f'Error: {str(e)}'}
```

## 🚀 Despliegue con Terraform

### Estructura del proyecto

```
aws-cloudwatch-subscription-filter/
├── src/
│   ├── controller_lambda.py
│   └── processor_lambda.py
├── main.tf
├── api_gateway.tf
├── lambda_functions.tf
├── cloudwatch_subscription_filter.tf
├── dynamodb_table.tf
├── iam_roles.tf
├── build_lambdas.sh
└── README.md
```

### Comandos de despliegue

```bash
# 1. Construir las Lambdas (zip y dependencias)
./build_lambdas.sh

# 2. Inicializar Terraform (credenciales previamente configuradas)
terraform init

# 3. Planificar el despliegue
terraform plan

# 4. Aplicar la infraestructura
terraform apply

# 5. Luego de las pruebas
terraform destroy
```

## 🧪 Pruebas y Validación

### POST que NO será procesado

Es importante tomar los outputs del Terraform y reemplazarlos en `{your-api-gateway-url}`

```bash
curl -X POST https://your-api-gateway-url/posts \
  -H "Content-Type: application/json" \
  -d '{
    "enable": false,
    "message": "Este mensaje no será procesado",
    "data": "algunos datos"
  }'
```

### POST que SÍ será procesado

```bash
curl -X POST https://your-api-gateway-url/posts \
  -H "Content-Type: application/json" \
  -d '{
    "enable": true,
    "message": "Este mensaje será procesado y guardado en DynamoDB",
    "data": "algunos datos importantes"
  }'
```


## 📊 Verificación de Resultados

### 1. CloudWatch Logs
Revisar los logs de la Lambda Controller para confirmar que se generan correctamente:

```

❌ POST received but enable=false: {"enable": false, "message": "Este mensaje no ser\u00e1 procesado", "data": "algunos datos"}
END RequestId: 
REPORT RequestId: 
Duration: 1.81 ms Billed Duration: 87 ms Memory Size: 128 MB Max Memory Used: 32 MB Init Duration: 84.44 ms

START RequestId:  Version: $LATEST
✅ ORIGINAL_POST: {"enable": true, "message": "Este mensaje ser\u00e1 procesado y guardado en DynamoDB", "data": "algunos datos importantes"}
END RequestId: 
REPORT RequestId:  
Duration: 1.46 ms Billed Duration: 2 ms 
Memory Size: 128 MB Max Memory Used: 32 MB
```

### 2. DynamoDB
Verificar que los datos se guardaron en la tabla:

```bash
aws dynamodb scan --table-name cloudwatch-subscription-filter-posts --limit 1 --region us-east-1
```

```json
// Response
{
    "Items": [
        {
            "original_post": {
                "M": {
                    "message": {
                        "S": "Este mensaje será procesado y guardado en DynamoDB"
                    },
                    "data": {
                        "S": "algunos datos importantes"
                    },
                    "enable": {
                        "BOOL": true
                    }
                }
            },
            "log_timestamp": {
                "N": "1768222052525"
            },
            "id": {
                "S": "51991cf6-23a5-463b-a8d1-dc2f047ab13c"
            },
            "processed_at": {
                "S": "2026-01-12T12:47:42.465810"
            },
            "timestamp": {
                "S": "2026-01-12T12:47:42.465790"
            }
        }
    ],
    "Count": 1,
    "ScannedCount": 1,
    "LastEvaluatedKey": {
        "id": {
            "S": "51991cf6-23a5-463b-a8d1-dc2f047ab13c"
        }
    }
}
```

### 3. CloudWatch Subscription Filter
Confirmar que el filtro se creó y está activo en la consola de AWS.

## 🔧 Características Técnicas

### Filtro de Patrones
- **Patrón**: `✅ ORIGINAL_POST` (He probado íconos porque me parece un punto crítico)
- **Sensible a mayúsculas**: Sí
- **Procesamiento**: máximo 30 segundos hasta que se persiste el registro en DynamoDB. 

### Compresión de Datos
CloudWatch Logs envía los datos **comprimidos con gzip** y **codificados en base64**:

```python
# Proceso de descompresión
compressed_payload = base64.b64decode(event['awslogs']['data'])
uncompressed_payload = gzip.decompress(compressed_payload)
log_data = json.loads(uncompressed_payload)
```

### Estructura de Datos
Los logs procesados incluyen:
- **ID único** generado con UUID
- **POST original** completo
- **Timestamps** de creación y procesamiento
- **Metadatos** del log event

## 💡 Casos de Uso Prácticos (Siempre como referencia, pero hay muchos más...)

### 1. Monitoreo de Errores
```python
# En la Lambda Controller
if error_occurred:
    print(f"🚨 ERROR_ALERT: {json.dumps(error_details)}")
```

### 2. Auditoría de Transacciones
```python
# Para transacciones críticas
if transaction_type == "payment":
    print(f"💰 PAYMENT_LOG: {json.dumps(transaction_data)}")
```

### 3. Análisis de Comportamiento
```python
# Para eventos de usuario
if user_action in ["login", "purchase", "signup"]:
    print(f"👤 USER_EVENT: {json.dumps(user_data)}")
```

## 📋 Conclusiones

Aproveché esta POC para validar el funcionamiento de **AWS CloudWatch Subscription Filter** identificando:

- **Automatización** del procesamiento de logs basado en patrones
- **Integración** despierta la lambda processor con una latencia razonable
- **Arquitectura serverless** escalable y costo-eficiente. Importante anotar que no se cobra por detectar los eventos sino por los datos enviados a la lambda o el Kinesis.
- **Filtrado inteligente** que procesa solo logs relevantes y se puede tener un control atómico de los eventos que se necesitan.

Esta implementación sirve como base para casos de uso más complejos como **monitoreo de errores**, **auditoría de transacciones**, **análisis de comportamiento de usuarios**, y **alertas en tiempo real**.

El código completo está disponible en [GitHub](https://github.com/olcortesb/aws-cloudwatch-subscription-filter) y listo para desplegar con Terraform, proporcionando una base sólida para proyectos que requieran procesamiento automático de logs en AWS.

## ⚠️ Consideraciones Importantes

### Límites del Servicio
- **Máximo 2 subscription filters** por log group
- **Filtros de hasta 1024 caracteres**
- **Rate limiting** en destinos Lambda

### Mejores Prácticas
- **Usar patrones específicos** para evitar ruido
- **Implementar retry logic** en el processor
- **Monitorear métricas** de CloudWatch
- **Configurar alertas** para errores


## 🔗 Referencias y Enlaces Útiles

- [AWS CloudWatch Logs Subscription Filters](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/SubscriptionFilters.html)
- [CloudWatch Logs Filter Pattern Syntax](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/FilterAndPatternSyntax.html)
- [AWS CloudWatch Limit And Quotas](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/cloudwatch_limits_cwl.html)
- [Lambda Function for CloudWatch Logs](https://docs.aws.amazon.com/lambda/latest/dg/services-cloudwatchlogs.html)
- [Terraform AWS CloudWatch Resources](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_log_subscription_filter)

Gracias por leer.

¡Saludos!

Oscar Cortés
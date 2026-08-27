# Post Article Backup

Repositorio para respaldar y gestionar artículos de blog con imágenes locales.

## 📁 Estructura del Proyecto

```
post-article-backup/
├── articles/                   # Artículos de blog
├── images/                     # Imágenes descargadas del CDN
├── scripts/                    # Scripts de automatización
├── workflows/                  # Workflows de CodeCatalyst (ejemplos)
└── README.md                   # Este archivo
```

## 📝 Artículos Disponibles

### `articles/european_cloud_providers_for_developers.md`
- Revisión técnica de 7 cloud providers europeos: OVHcloud, Scaleway, Hetzner, IONOS, Exoscale, STACKIT, UpCloud y gridscale
- Tabla comparativa de servicios, análisis de migración desde AWS y tres factores que los hyperscalers no mencionan
- Ficha por provider con links oficiales, Terraform provider, código de ejemplo y comentario general
- Datos técnicos comentados (<!-- -->) por provider para referencia futura

### `articles/is_agentcore_the_new_lambda.md`
- Investigación sobre Amazon Bedrock AgentCore como posible sucesor de Lambda
- Benchmark comparativo: Lambda Router + AgentCore vs Direct AgentCore vs Lambda-native
- 5 experimentos: Nova Lite AI, cómputo puro, SQS, S3 y DynamoDB
- Desplegado con Terraform, módulo reutilizable por agente

### `articles/aws_pid_lambda_durable_function.md`
- POC de controlador PID implementado con AWS Lambda Durable Functions
- Simulación de reactor con control de temperatura y estado persistente
- Comparativa de respuestas: sobreamortiguada, críticamente amortiguada y subamortiguada
- Desplegado con Terraform; incluye simulador Python local para ajuste de parámetros

### `articles/aws_appsync_dynamodb_cognito.md`
- POC de API GraphQL con AppSync conectado directamente a DynamoDB sin Lambda
- Resolvers VTL para createItem, getItem y listItems
- Autenticación con Cognito User Pools
- Desplegado completamente con Terraform

### `articles/s3rv3rl3ss_multi_cloud_update.md`
- Evolución de s3rv3rl3ss de dashboard solo AWS a comparación multi-cloud (AWS, GCP, Azure)
- 7 Lambdas con EventBridge Schedules escalonados, pipeline diario automático
- Vista de comparación en 13 categorías, eliminación de Git Layer por GitHub Contents API
- Single-table design en DynamoDB para persistencia de cambios, métricas y runtimes

### `articles/s3rv3rl3ss.md`
- Artículo original de s3rv3rl3ss: runtimes, límites, quotas y noticias de AWS serverless
- Cubre 15 servicios: Lambda, DynamoDB, API Gateway, SQS, SNS, EventBridge, Step Functions, AppSync, S3, Cognito, Secrets Manager, Kinesis, Fargate, Aurora Serverless, Bedrock
- Backend serverless con SAM, frontend Vue 3 + Vite + Tailwind desplegado en Amplify

### `articles/zig_lambda_runtime_migration.md`
- Migración del fork zig-lambda-runtime de Zig 0.12 a 0.16 en AWS Lambda
- Custom runtime con `provided.al2023` y arquitectura ARM64
- Cold start ~11ms, memoria 10MB, duración 1-2ms
- Documentación de cambios en build.zig, HTTP client, allocator y manejo de errores

### `articles/sqs_batch_processing_strategies.md`
- Estrategias de procesamiento por lotes con SQS
- Patrones de arquitectura serverless con AWS Lambda
- Ejemplos prácticos de configuración y uso

### `articles/connexus_system_desing.md`
- Sistema de trazabilidad para producción de café
- Diseño con AWS Lambda y DynamoDB, Single Table Design para DocumentDB
- Arquitectura serverless para agricultura

### `articles/aws_cloudwatch_subscription_filter.md`
- POC para agregar reactividad a sistemas con AWS CloudWatch Subscription Filter
- Arquitectura serverless con API Gateway, Lambda y DynamoDB
- Ejemplos prácticos de uso y configuración con Terraform

### `articles/aws_documentdb_streams.md`
- POC para capturar cambios en tiempo real con AWS DocumentDB Streams
- Arquitectura serverless con Lambda y EventBridge
- Ejemplos prácticos de configuración y uso

### `articles/aws_landing_zone.md`
- AWS Landing Zone y Control Tower: conceptos y contexto de arquitecturas multi-cuenta
- Evolución histórica y mejores prácticas
- Referencias oficiales de AWS

### `articles/iac_course.md`
- Material de curso empresarial de Infraestructura como Código (6 módulos)
- Comparativa Terraform / CloudFormation / Pulumi con ejemplos reales
- Buenas prácticas, CI/CD, gestión de secretos, drift detection y arquitecturas multi-cuenta

### `articles/kiro_mcp.md`
- Artículo sobre Kiro y Model Context Protocol
- Integración de IA con contexto de desarrollo
- Casos de uso y configuración

### `articles/codecatalist.md`
- Artículo original sobre AWS CodeCatalyst con imágenes locales
- Compatible con GitHub markdown
- Referencias: `../images/hashnode_image_X.png`

### `articles/codecatalyst_dev_to.md`
- Versión optimizada para dev.to del artículo de CodeCatalyst
- Incluye front matter con metadatos
- URLs de GitHub raw para imágenes

### `articles/codecatalyst_github_terraform.md`
- Artículo sobre integración CodeCatalyst + GitHub + Terraform
- Incluye workflow completo de CodeCatalyst
- Documentación de troubleshooting y mejores prácticas

---

## 🛠️ Scripts Configurados

### `scripts/download_images.py`
Descarga automáticamente imágenes del CDN de Hashnode desde archivos markdown.

```bash
cd scripts
pip install -r requirements.txt
python download_images.py
```

### `scripts/update_references.py`
Actualiza las referencias de imágenes en archivos markdown para usar rutas locales.

```bash
cd scripts
python update_references.py
```

## 📋 Dependencias

- `requests==2.31.0` — Para descargar imágenes

## 🎯 Propósito

- ✅ Respaldar artículos con imágenes locales
- ✅ Independencia de CDNs externos
- ✅ Compatibilidad con múltiples plataformas
- ✅ Automatización del proceso de descarga
- ✅ Versionado de contenido y recursos
- ✅ Organización clara por tipo de contenido

## 📚 Artículos Publicados

- [Probando AWS CodeCatalyst desde el AWS Builder ID](https://olcortesb.hashnode.dev/probando-aws-codecatalyst-desde-el-aws-builder-id)
- [Desplegar AWS Cognito y una aplicación cliente con Terraform](https://olcortesb.hashnode.dev/desplegar-aws-cognito-y-una-aplicacion-cliente-con-terraform)
- [Agregando reactividad con AWS CloudWatch Subscription Filter](https://github.com/olcortesb/aws-cloudwatch-subscription-filter)
- [s3rv3rl3ss (live)](https://s3rv3rl3ss.olcortesb.com/)

---
title: "s3rv3rl3ss ahora es multi-cloud: comparando serverless entre AWS, GCP y Azure"
description: "Cómo evolucionó s3rv3rl3ss de un dashboard solo AWS a una herramienta de comparación multi-cloud con datos actualizados diariamente"
pubDate: 2026-05-21T12:00:00.000Z
canonicalUrl: "https://olcortesb.hashnode.dev/s3rv3rl3ss-multi-cloud"
tags: ["aws", "gcp", "azure", "serverless", "lambda", "vue"]
draft: false
---

# s3rv3rl3ss ahora es multi-cloud: comparando serverless entre AWS, GCP y Azure



Hace unos dias empese aconstruír [s3rv3rl3ss](https://s3rv3rl3ss.olcortesb.com/), un dashboard que recopila quotas, límites, runtimes y noticias de servicios serverless de AWS, actualizado diariamente de forma automática. La pregunta natural era: ¿y los otros providers?

En esta actualización, el proyecto pasó de ser solo AWS a cubrir **3 providers** (AWS, GCP, Azure) con una vista de comparación lado a lado.

## Arquitectura actualizada

![alt text](../images/s3rv3rl3ss-update1.png)

El pipeline ahora tiene 4 Lambdas ejecutándose diariamente con EventBridge Schedules escalonados:

| Hora (UTC) | Lambda | Servicios |
|---|---|---|
| 06:00 | AWS Collector | 22 servicios |
| 06:15 | GCP Collector | 18 servicios |
| 06:30 | Azure Collector | 17 servicios |
| 06:45 | Comparisons Generator | Cross-provider |

Cada collector escribe su JSON a S3. Un evento `S3 ObjectCreated` dispara via EventBridge la función **CommitterFunction** que commitea el archivo al repo del frontend usando la GitHub Contents API. Amplify detecta el push y auto-deploya.

## Fuentes de datos por provider

### AWS
- **Quotas**: Service Quotas API
- **Pricing**: AWS Price List API
- **News**: AWS What's New RSS + blog feeds
- **Runtimes**: Scraping de docs de Lambda (markdown)
- **Limits**: Scraping de docs por servicio

### GCP
- **News**: GCP Release Notes RSS (Atom, por servicio)
- **Limits/Pricing/Runtimes**: Datos estáticos con referencias a docs

### Azure
- **Pricing**: Azure Retail Prices API (pública, sin auth)
- **News**: Azure Blog RSS filtrado por keywords
- **Limits/Runtimes**: Datos estáticos con referencias a docs

## Eliminando la Git Layer

El cambio más interesante en el backend fue eliminar la Lambda Layer con git. Antes, el committer necesitaba un binario de git empaquetado como layer para hacer clone/commit/push. Ahora usa directamente la **GitHub Contents API**:

```python
def commit_file(token, repo_path, content, message):
    sha = get_file_sha(token, repo_path)
    encoded = base64.b64encode(content.encode("utf-8")).decode("utf-8")

    payload = {
        "message": message,
        "content": encoded,
        "branch": GITHUB_BRANCH,
        "committer": {
            "name": "s3rv3rl3ss-bot",
            "email": "s3rv3rl3ss-bot@automated.dev",
        },
    }
    if sha:
        payload["sha"] = sha

    github_api("PUT", f"contents/{repo_path}", token, payload)
```

Ventajas:
- Sin layer de git (~50MB menos en el deploy)
- Sin necesidad de clonar el repo completo
- Cada archivo se commitea individualmente cuando cambia
- Solo usa `urllib` de la stdlib (sin dependencias extra)

## Lambda de comparaciones

La nueva `ComparisonsFunction` lee los 3 JSONs de providers desde S3 y genera un `comparisons.json` con mapeos verificados entre servicios equivalentes:

```python
CATEGORIES = [
    {
        "id": "functions",
        "name": "Functions",
        "services": {"aws": "lambda", "gcp": "cloud-run-functions", "azure": "azure-functions"},
        "limits": [
            {"label": "Max timeout", "aws": "Function timeout", "gcp": "Max function timeout (2nd gen)", "azure": "Max execution time (Consumption)"},
            {"label": "Max memory", "aws": "Function memory allocation", "gcp": "Max memory", "azure": "Max memory (Consumption)"},
            ...
        ],
    },
    ...
]
```

Hay 13 categorías: Functions, Containers, Kubernetes, NoSQL, Queues, etc. Cada una mapea los field names específicos de cada provider para que el frontend pueda mostrarlos lado a lado.

## Frontend: vista de comparación

En el frontend (Vue 3), la nueva vista `/compare` permite seleccionar una categoría y ver limits y pricing de los 3 providers en una tabla:

```javascript
function getLimitValue(provider, row) {
  // Primero busca valor estático (para datos sin API)
  const staticVal = row[`${provider}_value`]
  if (staticVal) return staticVal

  // Luego busca en los datos dinámicos del servicio
  const fieldName = row[provider]
  const svc = getService(provider)
  const limit = svc.limits.find(l => l.name === fieldName)
  return limit?.value
}
```

El patrón de `static_value` permite mezclar datos de APIs reales (AWS Service Quotas, Azure Retail Prices) con datos estáticos donde no hay API pública disponible.

## Template SAM

El `template.yaml` creció pero sigue siendo simple — 4 funciones, 1 bucket, EventBridge rules:

```yaml
Resources:
  DataBucket:
    Type: AWS::S3::Bucket
    Properties:
      NotificationConfiguration:
        EventBridgeConfiguration:
          EventBridgeEnabled: true

  CollectorFunction:
    Type: AWS::Serverless::Function
    Properties:
      Handler: handler.lambda_handler
      CodeUri: src/collector/
      Events:
        ScheduleEvent:
          Type: Schedule
          Properties:
            Schedule: cron(0 6 * * ? *)

  CommitterFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: src/committer/
      Events:
        S3Event:
          Type: EventBridgeRule
          Properties:
            Pattern:
              source: [aws.s3]
              detail-type: [Object Created]
              detail:
                bucket:
                  name: [!Ref DataBucket]
                object:
                  key:
                    - prefix: data/
                    - suffix: .json
```

El CommitterFunction se dispara con cualquier `.json` nuevo en `data/` — no importa qué collector lo escribió.

## Resultado

El sitio ahora muestra datos de 57 servicios serverless (22 AWS + 18 GCP + 17 Azure) con comparaciones verificadas en 13 categorías. Todo se actualiza diariamente sin intervención manual.

Live: [s3rv3rl3ss.olcortesb.com](https://s3rv3rl3ss.olcortesb.com/)

## Referencias

- [s3rv3rl3ss frontend](https://github.com/olcortesb/s3rv3rl3ss)
- [s3rv3rl3ss backend](https://github.com/olcortesb/s3rv3rl3ss-backend)
- [GitHub Contents API](https://docs.github.com/en/rest/repos/contents)
- [AWS Service Quotas API](https://docs.aws.amazon.com/servicequotas/2019-06-24/apireference/API_ListServiceQuotas.html)
- [Azure Retail Prices API](https://learn.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices)

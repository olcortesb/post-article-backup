# Ampliando las opciones de despliegue de nuestras cargas de trabajo en el Cloud: Cloud Providers Europeos

Llevo algunos años trabajando con AWS: Lambda, DynamoDB, API Gateway, CloudWatch; y también con Cloud Run, Azure Functions... el ecosistema de los Cloud Providers más conocidos. Estamos en un momento donde en algunas conversaciones de la comunidad técnica empiezan a surgir conceptos como: soberanía digital, GDPR, y preguntas como: **¿tenemos alternativas europeas a las que podamos migrar nuestras cargas de trabajo?**

Este artículo no es un manifiesto político ni un análisis soberano. Es una revisión personal y técnica de los principales cloud providers europeos, qué servicios ofrecen, dónde están sus límites, y si podríamos plantearnos migrar cargas de trabajo reales de nuestros clientes desde los grandes hyperscalers.

---

## Contexto

Hace poco incorporé a https://s3rv3rl3ss.olcortesb.com/ un nuevo proveedor, originalmente seguía noticias, límites y cuotas de los tres más conocidos, sin embargo, me interesaba conocer cómo se mueven estos cloud providers, su crecimiento, novedades técnicas, posibilidad de migraciones, integraciones, etc.

Después de estos análisis que aprovecho para compartir seguramente sumaremos más servicios a https://s3rv3rl3ss.olcortesb.com/

Dicho esto, vamos a lo técnico.

---

## Los jugadores principales

Siguiendo la lista de los más conocidos y algunos que ya conocía:

### OVHcloud (Francia) — Un viejo conocido


<!--
**Datos técnicos:**
- [API REST](https://developers.ovh.com) propia basada en OpenStack para Public Cloud — documentación en developers.ovh.com
- [Regiones](https://www.ovhcloud.com/en/public-cloud/regions-availability/): Europa (GRA, SBG, DE, UK, WAW, BHS), América (BHS, YYZ), Asia-Pacífico (SGP, SYD)
- [Managed Kubernetes](https://www.ovhcloud.com/en/public-cloud/kubernetes/): versiones 1.29, 1.30, 1.31 — integración con OpenStack networking
- [Object Storage](https://www.ovhcloud.com/en/public-cloud/object-storage/): compatible con S3 v4 y Swift (OpenStack)
- [Bases de datos gestionadas](https://www.ovhcloud.com/en/public-cloud/databases/): PostgreSQL, MySQL, Redis, MongoDB, Kafka, Cassandra, OpenSearch
- [Serverless Functions](https://www.ovhcloud.com/en/public-cloud/serverless-functions/) y [Serverless Tasks](https://www.ovhcloud.com/en/public-cloud/serverless-tasks/): incorporación reciente al catálogo
- Bare Metal: gestionado mediante API propia de OVHcloud, no mediante proyectos OpenStack
-->

OVHcloud es el provider europeo con mayor escala. Fundado en 1999 en Roubaix, Francia, opera más de 40 centros de datos en Europa, América y Asia-Pacífico. Es propiedad del grupo OVH SAS, empresa familiar francesa.

**Servicios destacados:**
- Instancias de cómputo (Public Cloud) basadas en OpenStack
- Object Storage compatible con S3
- Managed Kubernetes (OVHcloud Managed Kubernetes)
- Managed Databases: PostgreSQL, MySQL, Redis, MongoDB, Kafka
- Bare metal servers con alta densidad
- Anti-DDoS avanzado incluido en todos los planes
- Serverless Functions y Serverless Tasks (incorporación reciente)

**Lo que destaca:** Posiblemente lo que más me interesó es la compatibilidad con [OpenStack CLI](https://docs.ovhcloud.com/en/guides/public-cloud/cross-functional/compute-prepare-openstack-api-environment) en las instancias de Public Cloud, claramente es un punto a favor en equipos que ya trabajen con OpenStack y además quieran evitar vendor lock-in. Los servidores Bare Metal se gestionan mediante la API propia de OVHcloud, no mediante proyectos de OpenStack. Y para los que usamos infraestructura como código, el provider de Terraform está disponible y es funcional.

```hcl 
# Configuración del provider de OVHcloud para Terraform
terraform {
  required_providers {
    ovh = {
      source  = "ovh/ovh"
      version = "~> 0.40"
    }
  }
}

# Cluster de Kubernetes gestionado en la región GRA7 (Gravelines, Francia)
resource "ovh_cloud_project_kube" "my_cluster" {
  service_name = var.service_name
  name         = "my-k8s-cluster"
  region       = "GRA7"
  version      = "1.31"
}
```

**Links:**
🌐 [ovhcloud.com](https://www.ovhcloud.com)
📖 [Documentación API](https://developers.ovh.com)
🔧 [Terraform Provider](https://registry.terraform.io/providers/ovh/ovh/latest/docs)

---

### Scaleway (Francia) — El favorito de los developers por su orientación serverless 


<!--
**Datos técnicos:**
- Regiones: [París (fr-par), Ámsterdam (nl-ams), Varsovia (pl-waw)](https://www.scaleway.com/en/docs/console/account/reference-content/products-availability/)
- [Kubernetes Kapsule](https://www.scaleway.com/en/kubernetes-kapsule/): versiones 1.30, 1.31, 1.32 — CNI Cilium o Calico seleccionable
- [Serverless Functions](https://www.scaleway.com/en/serverless-functions/): Node.js 22, Python 3.12, Go 1.23, PHP 8.3, Rust 1.80
- [Object Storage](https://www.scaleway.com/en/object-storage/): compatible con S3 v4, endpoint por región (ej. s3.fr-par.scw.cloud)
- [Messaging](https://www.scaleway.com/en/messaging-and-queuing/): compatible con SQS y SNS (AWS SDK reutilizable cambiando endpoint)
- Bases de datos gestionadas: PostgreSQL 15/16, MySQL 8.0
-->

[Scaleway es parte del grupo Iliad](https://www.scaleway.com/en/about-us/) (el mismo detrás de Free, el operador de telecomunicaciones francés, hasta donde he podido averiguar). Tiene datacenters en París, Ámsterdam y Varsovia, y usa **energía 100% renovable**, y cuenta con [provider oficial de Terraform](https://www.scaleway.com/en/terraform/)!

**Servicios destacados:**
- Instancias de cómputo con precios muy competitivos
- Object Storage compatible con S3 (Scaleway Object Storage)
- Managed Kubernetes (Kapsule)
- Managed Databases: PostgreSQL, MySQL
- Serverless Functions y Serverless Containers
- Serverless Jobs (para batch processing)
- Messaging compatible con SQS/SNS (Scaleway Messaging and Queuing)
- IoT Hub

**Lo que destaca:** Scaleway tiene una oferta serverless que merece atención. Sus Serverless Functions soportan Node.js, Python, Go, PHP y Rust. El modelo de pricing es por invocación, similar a AWS Lambda. Y el servicio de mensajería es compatible con SQS y SNS — lo que significa que puedes reutilizar el AWS SDK cambiando solo el endpoint; este es un candidato para hacer alguna prueba de ejecutar algunas lambdas de las que ya tenemos en AWS.

```python
# Ejemplo de Serverless Function en Scaleway — misma firma que AWS Lambda
def handle(event, context):
    body = event.get("body", {})
    return {
        "statusCode": 200,
        "body": {
            "message": f"Hello from Scaleway, {body.get('name', 'world')}!"
        }
    }
```

```hcl
# Configuración del provider de Scaleway para Terraform
terraform {
  required_providers {
    scaleway = {
      source  = "scaleway/scaleway"
      version = "~> 2.40"
    }
  }
}

# Cluster de Kubernetes Kapsule en París
resource "scaleway_k8s_cluster" "my_cluster" {
  name    = "my-k8s-cluster"
  version = "1.32"
  region  = "fr-par"
  cni     = "cilium"
}
```

**Links:**
🌐 [scaleway.com](https://www.scaleway.com/en/)
📖 [Documentación API](https://www.scaleway.com/en/developers/)
🔧 [Terraform Provider](https://registry.terraform.io/providers/scaleway/scaleway/latest/docs)

---

### Hetzner (Alemania) — La opción precio/rendimiento, un clásico del cómputo

<!--
**Datos técnicos:**
- [API REST](https://docs.hetzner.cloud/) propia (no OpenStack) — documentada en docs.hetzner.cloud
- [Regiones](https://docs.hetzner.com/cloud/general/locations/): Núrembérg (nbg1), Falkenstein (fsn1), Helsinki (hel1), Ashburn EE.UU. (ash), Hillsboro EE.UU. (hil), Singapur (sin)
- [Kubernetes HKE](https://docs.hetzner.com/cloud/kubernetes/): gestionado vía hcloud CLI o Terraform, sin panel dedicado
- [Object Storage](https://docs.hetzner.com/storage/object-storage/overview/): compatible con S3 v4, endpoint fsn1.your-objectstorage.com
- [Servidores cloud](https://docs.hetzner.com/cloud/servers/overview/) desde €3.29/mes (CX22: 2 vCPU, 4 GB RAM)
- Sin managed databases nativas — recomiendan Hetzner + bases de datos self-managed o servicios externos
-->

Hetzner es probablemente el provider más conocido en la comunidad de developers europeos por una razón simple: **la relación precio/rendimiento es difícil de igualar**. Fundado en 1997 en Gunzenhausen, Alemania, opera datacenters en Nuremberg, Falkenstein (Alemania) y Helsinki (Finlandia).

**Servicios destacados:**
- Cloud Servers (VPS) con precios desde €3.29/mes
- Dedicated Servers con configuraciones de alto rendimiento
- Object Storage compatible con S3
- Managed Kubernetes (via kube-hetzner / k3s sobre instancias Cloud — no hay control plane gestionado nativo)
- Load Balancers
- Firewalls y redes privadas (VPC)
- Volumes (block storage)

**Lo que destaca:** La relación precio/rendimiento es difícil de igualar en Europa. Para workloads que necesitan cómputo puro, [servidores de aplicaciones, clusters de Kubernetes](https://community.hetzner.com/tutorials/setup-your-own-scalable-kubernetes-cluster), bases de datos self-managed — Hetzner es una opción seria. Muchos equipos lo usan para staging environments o para cargas de trabajo predecibles donde el costo importa. Además tiene provider de Terraform y ya empieza a ser común entre los que analizamos:

```bash
# Crear un servidor con hcloud CLI
hcloud server create \
  --name my-server \
  --type cx31 \
  --image ubuntu-24.04 \
  --location nbg1 \
  --ssh-key my-key
```

```hcl
# Configuración del provider de Hetzner para Terraform
# Referencia: https://community.hetzner.com/tutorials/setup-your-own-scalable-kubernetes-cluster
terraform {
  required_providers {
    hcloud = {
      source  = "hetznercloud/hcloud"
      version = "~> 1.56" # Versión estable actual, puede cambiar en el futuro
    }
  }
}

# Variable del token de API — se define en .tfvars y se marca como sensible
variable "hcloud_token" {
  sensitive = true # Requiere Terraform >= 0.14
}

# Configuración del provider con el token de Hetzner Cloud
provider "hcloud" {
  token = var.hcloud_token
}
```

**Links:**
🌐 [hetzner.com](https://www.hetzner.com)
📖 [Documentación API](https://docs.hetzner.cloud)
🔧 [Terraform Provider](https://registry.terraform.io/providers/hetznercloud/hcloud/latest/docs)

---

### IONOS Cloud (Alemania) — El enterprise europeo

<!--
**Datos técnicos:**
- [API REST](https://api.ionos.com/docs/) propia con SDKs oficiales para Go, Python, Java y Node.js
- Regiones: Alemania (de/txl, de/fra), España (es/vit), Reino Unido (gb/lhr), Francia (fr/par), EE.UU. (us/las, us/ewr)
- [Kubernetes](https://docs.ionos.com/cloud/managed-services/managed-kubernetes): versiones 1.29, 1.30, 1.31 — actualización de nodos en rolling update
- Object Storage: compatible con S3 v4
- [Bases de datos gestionadas](https://docs.ionos.com/cloud/databases/databases): PostgreSQL 12–16, MySQL 8.0, MongoDB 5/6
- [Data Center Designer](https://docs.ionos.com/cloud/compute-engine/data-center-designer): herramienta visual para diseñar topología de red y servidores antes de aprovisionar
-->

IONOS es parte del grupo United Internet, uno de los mayores proveedores de internet de Europa. Tiene presencia en Alemania, España, Reino Unido, Francia y EE.UU.

**Servicios destacados:**
- Virtual Servers y Dedicated Servers
- Managed Kubernetes
- Object Storage compatible con S3
- Managed Databases: PostgreSQL, MySQL, MongoDB
- Data Center Designer — interfaz visual para diseñar infraestructura
- Block Storage y NFS Storage

**Lo que destaca:** El Data Center Designer es genuinamente útil para equipos que necesitan visualizar y documentar su infraestructura antes de aprovisionar. No es algo que encuentres en otros providers europeos.

```hcl
# Configuración del provider de IONOS Cloud para Terraform
terraform {
  required_providers {
    ionoscloud = {
      source  = "ionos-cloud/ionoscloud"
      version = "~> 6.4"
    }
  }
}

# Cluster de Kubernetes gestionado en IONOS Cloud
resource "ionoscloud_k8s_cluster" "my_cluster" {
  name        = "my-k8s-cluster"
  k8s_version = "1.31"
}
```

**Links:**
🌐 [cloud.ionos.com](https://cloud.ionos.com)
📖 [Documentación API](https://api.ionos.com/docs/)
🔧 [Terraform Provider](https://registry.terraform.io/providers/ionos-cloud/ionoscloud/latest/docs)

---

### Exoscale (Suiza) — El especialista en seguridad

<!--
**Datos técnicos:**
- [API v2](https://openapi-v2.exoscale.com) propia (Exoscale API v2) — OpenAPI spec pública
- [Zonas](https://www.exoscale.com/datacenters/): Ginebra (ch-gva-2), Zúrich (ch-dk-2), Frankfurt (de-fra-1), Viena (at-vie-1), Sofía (bg-sof-1), Munich (de-muc-1)
- [Kubernetes SKS](https://www.exoscale.com/sks/): versiones 1.30, 1.31, 1.32 — CNI Calico, soporte para nodos GPU
- [Object Storage](https://www.exoscale.com/object-storage/): compatible con S3 v4, permisos granulares por bucket y por API key
- [Bases de datos gestionadas](https://www.exoscale.com/dbaas/): PostgreSQL, MySQL, Redis, Apache Kafka, OpenSearch, Grafana
- API keys con scope por servicio: se puede restringir a solo "compute", solo "storage", o a un bucket específico
-->

Exoscale es propiedad de A1, uno de los mayores operadores de telecomunicaciones de Austria. Opera desde Suiza, con datacenters en Ginebra, Zúrich, Frankfurt, Viena, Sofía y Munich.

**Servicios destacados:**
- Instancias de cómputo optimizadas (CPU, memoria, storage, GPU)
- Object Storage compatible con S3 con permisos granulares a nivel de bucket
- Managed Kubernetes (SKS - Scalable Kubernetes Service)
- Managed Databases: PostgreSQL, MySQL, Redis, Apache Kafka
- DNS y CDN
- API keys con permisos granulares por servicio

**Lo que destaca:** La granularidad de permisos en API keys es un punto diferenciador real para equipos con requisitos de seguridad estrictos. Puedes crear una API key que solo tenga acceso a un bucket específico de object storage — algo que en AWS requiere configurar IAM policies explícitas. También tienen provider de Terraform.

```hcl
# Configuración del provider de Exoscale para Terraform
terraform {
  required_providers {
    exoscale = {
      source  = "exoscale/exoscale"
      version = "~> 0.57"
    }
  }
}

# Cluster de Kubernetes SKS en Ginebra (zona ch-gva-2)
resource "exoscale_sks_cluster" "my_cluster" {
  zone    = "ch-gva-2"
  name    = "my-k8s-cluster"
  version = "1.32"
}
```

**Links:**
🌐 [exoscale.com](https://www.exoscale.com)
📖 [Documentación API](https://openapi-v2.exoscale.com)
🔧 [Terraform Provider](https://registry.terraform.io/providers/exoscale/exoscale/latest/docs)

---

### STACKIT (Alemania) — El nuevo pero completo y respaldado cloud corporativo

<!--
**Datos técnicos:**
- [API REST](https://docs.api.stackit.cloud/) propia con especificación OpenAPI disponible
- [Regiones](https://docs.stackit.cloud/): Alemania (eu-de-1, eu-de-2), Austria (eu-at-1)
- [Kubernetes SKE](https://docs.stackit.cloud/) (Scalable Kubernetes Engine): versiones 1.29, 1.30, 1.31
- Object Storage: compatible con S3 v4
- Bases de datos gestionadas: PostgreSQL, MySQL, Redis, MongoDB, RabbitMQ, Elasticsearch/OpenSearch (ELK stack)
- Certificaciones: ISO 27001, C5 (BSI Alemania), GDPR by design
-->

STACKIT es el cloud provider del grupo Schwarz, la empresa detrás de Lidl y Kaufland. Lanzado relativamente recientemente, opera datacenters en Alemania y Austria.

**Servicios destacados:**
- Object Storage compatible con S3
- Managed Kubernetes
- Block Storage
- Managed Databases: PostgreSQL, MySQL, Redis, MongoDB, RabbitMQ, ELK stack

**Lo que destaca:** Tiene el respaldo financiero de uno de los grupos empresariales más grandes de Europa. No va a desaparecer mañana, y su oferta de managed databases es de las más completas entre los providers europeos — incluyendo RabbitMQ y el stack ELK, que pocos ofrecen de forma gestionada. Sí, tiene [provider de Terraform](https://github.com/stackitcloud/terraform-provider-stackit).

```hcl
# Configuración del provider de STACKIT para Terraform
terraform {
  required_providers {
    stackit = {
      source  = "stackitcloud/stackit"
      version = "~> 0.36"
    }
  }
}

# Cluster de Kubernetes SKE en Alemania (eu-de-1)
resource "stackit_ske_cluster" "my_cluster" {
  project_id         = var.project_id
  name               = "my-k8s-cluster"
  kubernetes_version = "1.31"
  region             = "eu-de-1"
}
```

**Links:**
🌐 [stackit.com](https://stackit.com/en/)
📖 [Documentación API](https://docs.api.stackit.cloud/)
🔧 [Terraform Provider](https://registry.terraform.io/providers/stackitcloud/stackit/latest/docs)

---

### UpCloud (Finlandia) — El cloud europeo con alcance global

<!--
**Datos técnicos:**
- [API REST](https://developers.upcloud.com/1.3/) propia (UpCloud API 1.3) — autenticación HTTP Basic o tokens
- Regiones Europa: Frankfurt (de-fra1), Ámsterdam (nl-ams1), Londres (uk-lon1), Helsinki (fi-hel1/fi-hel2), Estocolmo (se-sto1), Varsovia (pl-waw1), Madrid (es-mad1)
- [Kubernetes](https://upcloud.com/products/managed-kubernetes): versiones 1.30, 1.31, 1.32 — actualización de control plane sin downtime
- [Block storage MaxIOPS](https://upcloud.com/products/block-storage): hasta 100.000 IOPS, upgradeable en caliente sin reiniciar el servidor
- Object Storage: compatible con S3 v4
- [Bases de datos gestionadas](https://upcloud.com/products/managed-databases): PostgreSQL 14/15/16, MySQL 8.0, Redis 7, OpenSearch 2.x
-->

UpCloud está headquartered en Helsinki, Finlandia, y opera **15 datacenters en 4 continentes** — lo que lo hace inusual entre los providers europeos, que típicamente se limitan a Europa. Tiene presencia en Frankfurt, Amsterdam, Londres, Helsinki, Estocolmo, Varsovia, Madrid, Chicago, Dallas, Nueva York, São Paulo, Singapur, Sydney y Tokio.

**Servicios destacados:**
- Virtual Servers con block storage de alto rendimiento (MaxIOPS)
- Object Storage compatible con S3
- Managed Kubernetes
- Managed Databases: PostgreSQL, MySQL, Redis, OpenSearch
- VPC y redes privadas
- Load Balancers
- Managed DNS

**Lo que destaca:** El block storage de UpCloud permite upgradear el tier de IOPS sin detener el servidor — para bases de datos o aplicaciones con I/O intensivo, esto es relevante. Además, es uno de los pocos providers europeos con presencia global real: 15 datacenters en 4 continentes. Útil para SaaS con usuarios distribuidos que necesitan cumplir GDPR pero no pueden sacrificar latencia.

```bash
# Crear servidor con upcloud CLI (upctl)
upctl server create \
  --hostname my-server \
  --zone de-fra1 \
  --plan 2xCPU-4GB \
  --os "Ubuntu Server 24.04 LTS (Noble Numbat)"
```

```hcl
# Configuración del provider de UpCloud para Terraform
terraform {
  required_providers {
    upcloud = {
      source  = "UpCloudLtd/upcloud"
      version = "~> 5.0"
    }
  }
}

# Servidor virtual en Frankfurt con block storage de alto rendimiento
resource "upcloud_server" "my_server" {
  hostname = "my-server"
  zone     = "de-fra1"
  plan     = "2xCPU-4GB"

  template {
    storage = "Ubuntu Server 24.04 LTS (Noble Numbat)"
    size    = 25
  }

  network_interface {
    type = "public"
  }
}
```

**Links:**
🌐 [upcloud.com](https://upcloud.com)
📖 [Documentación API](https://developers.upcloud.com/1.3/)
🔧 [Terraform Provider](https://registry.terraform.io/providers/UpCloudLtd/upcloud/latest/docs)

---

### gridscale (Alemania) — El especialista en bases de datos

<!--
**Datos técnicos:**
- [API REST](https://gridscale.io/en/api-documentation/v1/) propia (gridscale API v1) — autenticación por API key + User-UUID en headers
- Regiones: Colonia (de/cgn), Hamburgo (de/ham), Viena (at/vie), Zúrich (ch/zur), Ámsterdam (nl/ams)
- [Kubernetes](https://gridscale.io/en/cloud-server/): gestionado con actualizaciones automáticas de parches de seguridad
- Object Storage: compatible con S3 v4
- [Bases de datos gestionadas](https://gridscale.io/en/cloud-server/): PostgreSQL, Microsoft SQL Server, MariaDB, MySQL, Redis
- [Managed NFS](https://gridscale.io/en/cloud-server/): acceso ReadWriteMany (RWX) para múltiples pods en Kubernetes simultáneamente
- Energía: 100% renovable certificada en todos sus datacenters
-->

gridscale es un cloud provider alemán que opera con **energía 100% renovable** y tiene datacenters en Alemania, Austria, Suiza y Países Bajos. Es menos conocido fuera de la comunidad europea, pero tiene una propuesta técnica interesante.

**Servicios destacados:**
- Virtual Servers
- Managed Kubernetes
- Object Storage compatible con S3
- Load Balancers
- Managed NFS (Network File Storage) — para compartir datos entre nodos de Kubernetes
- Managed Databases: **PostgreSQL, Microsoft SQL Server, MariaDB, MySQL, Redis** (como caché y como storage)

**Lo que destaca:** Dos cosas. Primero, la variedad de bases de datos gestionadas es de las más amplias entre providers europeos — incluyendo Microsoft SQL Server, que no es común en este ecosistema. Segundo, el Managed NFS resuelve un problema real en clusters de Kubernetes con workloads stateful que necesitan storage compartido entre pods (ReadWriteMany / RWX). Para equipos que migran aplicaciones legacy que dependen de SQL Server y necesitan quedarse en Europa, gridscale es prácticamente la única opción hasta donde he podido averiguar.

```yaml
# PersistentVolume usando NFS de gridscale en Kubernetes
apiVersion: v1
kind: PersistentVolume
metadata:
  name: nfs-pv
spec:
  capacity:
    storage: 50Gi
  accessModes:
    - ReadWriteMany
  nfs:
    server: <gridscale-nfs-endpoint>
    path: /exports/shared-data
```

```hcl
# Configuración del provider de gridscale para Terraform
terraform {
  required_providers {
    gridscale = {
      source  = "gridscale/gridscale"
      version = "~> 1.20"
    }
  }
}

# Servidor virtual en Colonia con disco SSD de 20GB
resource "gridscale_server" "my_server" {
  name   = "my-server"
  cores  = 2
  memory = 4

  storage {
    capacity = 20
    name     = "my-storage"
  }
}
```

**Links:**
🌐 [gridscale.io](https://gridscale.io)
📖 [Documentación API](https://gridscale.io/en/api-documentation/v1/)
🔧 [Terraform Provider](https://registry.terraform.io/providers/gridscale/gridscale/latest/docs)

---

## Comparativa técnica rápida

| Servicio | OVHcloud | Scaleway | Hetzner | Exoscale | STACKIT | UpCloud | gridscale |
|---|---|---|---|---|---|---|---|
| Kubernetes gestionado | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ |
| Object Storage (S3-compatible) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Serverless Functions | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Managed PostgreSQL | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ |
| Managed Kafka | ✅ | ✅ | ❌ | ✅ | ✅ | ❌ | ❌ |
| Managed NFS | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Managed SQL Server | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| GPU instances | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Presencia global | ✅ | Parcial | ❌ | ❌ | ❌ | ✅ | ❌ |
| Terraform provider | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Energía renovable | Parcial | ✅ | ✅ | Parcial | Parcial | Parcial | ✅ |

> ❌ **Hetzner / Kubernetes**: No dispone de un servicio de Kubernetes con control plane gestionado nativo. La comunidad utiliza herramientas como [kube-hetzner](https://github.com/kube-hetzner/terraform-hcloud-kube-hetzner) o [k3s](https://k3s.io/) sobre instancias Cloud. El despliegue y mantenimiento del control plane es responsabilidad del equipo.

---

## ¿Podemos migrar desde AWS?

Depende de qué estés migrando. Hagamos un análisis rápido para no extender este post, pero seguro tendremos más posts similares:

### Workloads que migran bien ✅

**Kubernetes / Contenedores**
Si tu aplicación corre en Kubernetes, la migración es relativamente directa. Todos los providers listados tienen managed Kubernetes. El trabajo está en migrar los manifests, configurar el registry de imágenes y ajustar el networking.

**Object Storage**
Todos los providers tienen object storage compatible con S3. Si usas el SDK de AWS S3, en muchos casos solo necesitas cambiar el endpoint y las credenciales.

```python
import boto3
from botocore.config import Config

# Antes: AWS S3
s3 = boto3.client('s3', region_name='us-east-1')

# Después: Scaleway Object Storage (mismo SDK, diferente endpoint)
# Config con addressing_style necesario si el bucket name incluye puntos
s3 = boto3.client(
    's3',
    region_name='fr-par',
    endpoint_url='https://s3.fr-par.scw.cloud',
    aws_access_key_id='<scaleway-access-key>',
    aws_secret_access_key='<scaleway-secret-key>',
    config=Config(s3={'addressing_style': 'virtual'})
)
```

**Bases de datos relacionales**
PostgreSQL y MySQL gestionados están disponibles en todos los providers principales. La migración de datos es el trabajo real, no la infraestructura.

### Workloads que requieren trabajo ⚠️

**Serverless / Event-driven**
Si tu arquitectura usa Lambda + SQS + EventBridge + Step Functions, la migración no es trivial. Scaleway tiene serverless functions y un servicio de mensajería compatible con SQS/SNS, pero el ecosistema de orquestación no tiene equivalente directo. Tendríamos que reemplazar Step Functions con algo como Temporal o Conductor self-hosted.

**Servicios específicos de AWS**
DynamoDB, AppSync, Cognito, CloudWatch Logs Insights — no tienen equivalentes directos en providers europeos. Tendríamos que reemplazarlos con alternativas open source o cambiar el diseño de la arquitectura.

### Workloads que no migran fácilmente ❌

**Arquitecturas fuertemente acopladas a servicios propietarios de AWS**
Si tu sistema usa Kinesis Data Streams, AWS Glue, SageMaker, o servicios de ML/AI específicos de AWS, la migración implica rediseño significativo, no solo reconfiguración.

---

## Tres factores que los hyperscalers no mencionan

**1. Egress fees (costos de salida de datos)**
AWS, GCP y Azure cobran por transferir datos fuera de su red. OVHcloud y STACKIT ofrecen egress gratuito; Hetzner y Scaleway incluyen una cantidad generosa de tráfico en sus precios o cobran tarifas mínimas. Para aplicaciones con alto volumen de transferencia, esto puede cambiar significativamente el costo total.

**2. Previsibilidad de costos**
Los providers europeos tienden a usar tarifas planas o precios más predecibles. Con el modelo de pricing de AWS ya sabemos lo que puede ocurrir en la factura si no tenemos alertas configuradas correctamente.

**3. Jurisdicción legal real**
Un datacenter de AWS en Frankfurt sigue siendo operado por una empresa americana sujeta al CLOUD Act. Un datacenter de OVHcloud en Estrasburgo es operado por una empresa francesa sujeta exclusivamente a legislación europea. Para ciertos sectores, esta diferencia no es negociable.

---

## Conclusión

No creo que los cloud providers europeos sean un reemplazo completo para AWS hoy, y no pretendemos que lo sean, buscábamos alternativas. El ecosistema de servicios gestionados es más pequeño, la documentación y comunidad son crecientes.

Como dije, no creo que la conversación sea binaria.

Hay casos de uso donde los providers europeos son la opción correcta ahora mismo:
- Proyectos con requisitos estrictos de residencia de datos en Europa
- Workloads basados en Kubernetes donde el vendor lock-in es mínimo
- Aplicaciones que usan principalmente object storage y bases de datos relacionales
- Equipos que quieren reducir costos en infraestructura predecible

Y hay una tendencia clara: el ecosistema europeo está creciendo rápido. Todos los que hemos analizado para este artículo tienen Terraform provider. (Sí, creo que estoy un poco pesado con lo de Terraform, ¡pero es un punto importante!) Scaleway está expandiendo su oferta serverless. STACKIT tiene el respaldo financiero para crecer. OVHcloud está invirtiendo en servicios gestionados. UpCloud está expandiendo su red global manteniendo su base europea. gridscale está apostando por nichos técnicos específicos como NFS y SQL Server que los demás ignoran.

Si estás empezando un proyecto nuevo y los datos deben quedarse en Europa, vale la pena evaluar estos providers seriamente. Si tienes una arquitectura existente en AWS, la migración requiere planificación — pero no es imposible.

Lo que sí cambió es que ya no es una pregunta de "¿existe algo europeo?" sino de "¿cuál de providers europeos se adapta mejor a mi caso de uso?". 
---

## Referencias

- [European Cloud Providers Compared 2026](https://european.cloud/) — Comparativa independiente actualizada
- [European Alternatives - Cloud Computing](https://european-alternatives.eu/category/cloud-computing-platforms) — Directorio de alternativas europeas
- [EU Cloud Sovereignty: Why Businesses Are Moving Away from US Providers](https://asee.io/blog/eu-cloud-sovereignty-businesses-leaving-us-providers/) — ASEE, Abril 2026
- [Europe wants sovereign cloud – but now it needs somewhere to put it](https://www.onnecgroup.com/2026/07/06/europe-wants-sovereign-cloud/) — Onnec Group, Julio 2026
- [Commission Advances Cloud Sovereignty Through Strategic Procurement](https://commission.europa.eu/news-and-media/news/commission-advances-cloud-sovereignty-through-strategic-procurement-2026-04-17_en) — European Commission, Abril 2026
- [Entre la soberanía digital y el ajuste normativo](https://www.computerworld.es/article/4207852/entre-la-soberania-digital-y-el-ajuste-normativo-este-es-el-marco-legal-en-la-nube-de-la-union-europea.html) — Computerworld ES
- [A basic look at pricing of European Cloud vendors](https://european.cloud/2025/06/a-basic-look-at-pricing-of-european-cloud-vendors/) — European Cloud, Junio 2025

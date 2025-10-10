---
title: "4 Estrategias para Procesar Mensajes SQS en Lotes con AWS Lambda"
published: false
description: "Comparación práctica de 4 estrategias diferentes para procesar mensajes SQS en lotes: eliminación directa, reenvío a cola, visibility timeout y Dead Letter Queue"
tags: aws, sqs, lambda, serverless, devops
---

Durante una charla de sincronización con un compañero de trabajo, sobre un cliente que necesita una estrategia para gestionar una cola de eventos a través de procesamiento por lotes, surgió la duda de cuál es la estrategia que más le convenía, y cuál era el estado del arte de las colas SQS en estos momentos.

Basado en lo que sacamos de esa charla, en este *post* exploraremos **4 estrategias diferentes** para procesar mensajes de Amazon SQS en lotes usando AWS Lambda (como único consumidor, esto es importante para el análisis). Cada estrategia tiene sus propios casos de uso, ventajas y consideraciones de rendimiento que analizaremos con ejemplos prácticos.

## 🚀 ¿Por qué procesar mensajes SQS en lotes?

Amazon SQS permite procesar hasta **10 mensajes por llamada** usando `receive_message()` (Python), lo que es más eficiente que procesar mensajes uno por uno. Sin embargo, no todos los mensajes pueden procesarse exitosamente en el primer intento, por lo que necesitamos diferentes estrategias para manejar los fallos.

### ⚠️ Validación del Límite de 10 Mensajes

AWS SQS **estrictamente limita** el parámetro `MaxNumberOfMessages` entre 1 y 10. Si intentas usar un valor mayor, obtienes este error:

```json
{
  "error": "An error occurred (InvalidParameterValue) when calling the ReceiveMessage operation: Value 20 for parameter MaxNumberOfMessages is invalid. Reason: Must be between 1 and 10, if provided."
}
```

Este límite aplica tanto para **colas Standard como FIFO**, confirmando que el procesamiento en lotes está limitado a máximo 10 mensajes por operación `receive_message()`.

> Colas estándar vs Colas FIFO: [Ref](https://docs.aws.amazon.com/es_es/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-queue-types.html) 

## 🏗️ Arquitectura del Proyecto

> **⚠️ Importante**: Este análisis y casos de uso están basados en un **consumidor único** por cola. Con **múltiples consumidores concurrentes**, el comportamiento y las consideraciones de cada estrategia pueden ser significativamente más complejas, especialmente en términos de duplicados, orden de procesamiento y gestión de fallos.

El proyecto implementa 4 funciones Lambda diferentes, cada una con una estrategia distinta para manejar mensajes que no cumplen ciertos criterios (en nuestro caso, números menores a 50). Partiendo de un script que genera 100 mensajes aleatorios con números entre 1 y 100 (el script pueden encontrarlo en el GitHub):

> https://github.com/olcortesb/aws-examples

A continuación, las dos colas que utilizaremos en las pruebas:

```yaml
Resources:
  MessagesQueue:
    Type: AWS::SQS::Queue
    Properties:
      VisibilityTimeoutSeconds: 30
      MessageRetentionPeriod: 1209600

  DeadLetterQueue:
    Type: AWS::SQS::Queue
    Properties:
      MessageRetentionPeriod: 1209600
```

## 📋 Las 4 Estrategias Implementadas

### 1. Estrategia Simple: Eliminar Todos los Mensajes

**Función**: `GetMessagesFunction`

```python
def lambda_handler(event, context):
    response = sqs.receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=10,  # Máximo permitido por AWS
        WaitTimeSeconds=5
    )
    
    messages = response.get('Messages', [])
    
    for msg in messages:
        # Procesar mensaje
        processed_messages.append({
            "messageId": msg['MessageId'],
            "body": msg['Body']
        })
        
        # Eliminar siempre
        sqs.delete_message(
            QueueUrl=queue_url,
            ReceiptHandle=msg['ReceiptHandle']
        )
```

**Características:**
- ✅ **Simplicidad**: Lógica directa y fácil de entender
- ✅ **Rendimiento**: No hay operaciones adicionales
- ❌ **Pérdida de datos**: Los mensajes fallidos se pierden permanentemente

**Caso de uso**: Procesamiento donde la pérdida ocasional de mensajes es aceptable.

### 2. Estrategia de Reenvío: Devolver Mensajes a la Cola

**Función**: `ProcessMessagesFunction`

```python
def lambda_handler(event, context):
    for msg in messages:
        message_number = int(msg['Body'])
        
        if message_number < threshold:
            # Reenviar a la misma cola
            sqs.send_message(
                QueueUrl=queue_url,
                MessageBody=msg['Body']
            )
        
        # Eliminar mensaje original
        sqs.delete_message(
            QueueUrl=queue_url,
            ReceiptHandle=msg['ReceiptHandle']
        )
```

**Características:**
- ✅ **Sin pérdida**: Los mensajes fallidos se reenvían
- ✅ **Flexibilidad**: Permite modificar el mensaje antes del reenvío (creo que es lo único positivo que tiene este caso de uso, pero lo dejo porque alguna vez lo he tenido que usar 😂)
- ❌ **Duplicación**: Puede crear mensajes duplicados
- ❌ **Overhead**: Operaciones adicionales de escritura

**Caso de uso**: Cuando necesitas modificar (por ejemplo, sumar un número en nuestro caso de prueba) mensajes antes de reintentar un nuevo procesamiento.

### 3. Estrategia de Visibility Timeout: Dejar Reaparecer

**Función**: `ProcessWithVisibilityFunction`

```python
def lambda_handler(event, context):
    for msg in messages:
        message_number = int(msg['Body'])
        
        if message_number >= threshold:
            # Solo eliminar si cumple criterios
            sqs.delete_message(
                QueueUrl=queue_url,
                ReceiptHandle=msg['ReceiptHandle']
            )
        # Los mensajes no eliminados reaparecen automáticamente
```

**Características:**
- ✅ **Eficiencia**: Menos operaciones de escritura
- ✅ **Automático**: SQS maneja la reaparición
- ✅ **Sin duplicados**: No crea mensajes adicionales
- ❌ **Tiempo fijo**: Depende del visibility timeout configurado

**Caso de uso**: Ideal para reintentos automáticos sin lógica compleja.

### 4. Estrategia Dead Letter Queue: Segregar Mensajes Fallidos

**Función**: `ProcessWithDlqFunction`

```python
def lambda_handler(event, context):
    for msg in messages:
        message_number = int(msg['Body'])
        
        if message_number >= threshold:
            processed_messages.append(msg)
        else:
            # Enviar a Dead Letter Queue
            sqs.send_message(
                QueueUrl=dlq_url,
                MessageBody=msg['Body']
            )
        
        # Eliminar de cola original
        sqs.delete_message(
            QueueUrl=queue_url,
            ReceiptHandle=msg['ReceiptHandle']
        )
```

**Características:**
- ✅ **Segregación**: Mensajes fallidos en cola separada
- ✅ **Análisis**: Permite investigar patrones de fallo
- ✅ **Reprocesamiento**: Posibilidad de procesar DLQ posteriormente
- ❌ **Complejidad**: Requiere gestión de múltiples colas

**Caso de uso**: Sistemas críticos que requieren análisis de fallos y reprocesamiento.

## 🚀 Despliegue y Pruebas

### 1. Desplegar la Aplicación

```bash
sam build
sam deploy --guided --profile your-aws-profile
```

### 2. Enviar Mensajes de Prueba

```bash
cd scripts
python3 send_messages.py
```

El script envía 100 mensajes numerados del 1 al 100 para probar las diferentes estrategias (los que no tomamos como válidos son los menores a 50).

### 3. Probar Cada Estrategia

```bash
# Estrategia 1: Eliminar todos
aws lambda invoke --function-name bach-messages-GetMessagesFunction-XXXXX response1.json

# Estrategia 2: Reenvío
aws lambda invoke --function-name bach-messages-ProcessMessagesFunction-XXXXX response2.json

# Estrategia 3: Visibility Timeout
aws lambda invoke --function-name bach-messages-ProcessWithVisibilityFunction-XXXXX response3.json

# Estrategia 4: Dead Letter Queue
aws lambda invoke --function-name bach-messages-ProcessWithDlqFunction-XXXXX response4.json
```

## 📊 Comparación de Estrategias

| Estrategia | Pérdida de Datos | Duplicados | Operaciones Extra | Complejidad | Análisis de Fallos |
|------------|------------------|------------|-------------------|-------------|-------------------|
| **Simple** | ❌ Sí | ✅ No | ✅ Ninguna | ✅ Baja | ❌ No |
| **Reenvío** | ✅ No | ❌ Posible | ❌ Send | 🟡 Media | ❌ No |
| **Visibility** | ✅ No | ✅ No | ✅ Ninguna | ✅ Baja | ❌ Limitado |
| **DLQ** | ✅ No | ✅ No | ❌ Send | ❌ Alta | ✅ Completo |

## 🎯 Recomendaciones por Caso de Uso

### Usar **Estrategia Simple** cuando:
- Los mensajes no son críticos
- El rendimiento es prioritario
- La pérdida ocasional es aceptable

### Usar **Estrategia de Reenvío** cuando:
- Necesitas modificar mensajes antes del reintento
- Tienes lógica compleja de reintento
- Puedes manejar duplicados

### Usar **Visibility Timeout** cuando:
- Quieres reintentos automáticos simples
- El rendimiento es importante
- Los fallos son temporales

### Usar **Dead Letter Queue** cuando:
- Los mensajes son críticos
- Necesitas análisis de fallos
- Requieres reprocesamiento manual
- Tienes sistemas de monitoreo avanzados

## 🔧 Configuraciones Importantes

### Visibility Timeout
```yaml
MessagesQueue:
  Properties:
    VisibilityTimeoutSeconds: 30  # Tiempo antes de reaparecer
```

### Message Retention
```yaml
DeadLetterQueue:
  Properties:
    MessageRetentionPeriod: 1209600  # 14 días
```

### Lambda Timeout
```yaml
Globals:
  Function:
    Timeout: 3  # Debe ser menor que visibility timeout
```

## 📈 Métricas y Monitoreo

Para cada estrategia, monitorea:

- **Throughput**: Mensajes procesados por segundo
- **Error Rate**: Porcentaje de mensajes fallidos
- **Latency**: Tiempo de procesamiento por lote
- **Queue Depth**: Mensajes pendientes en cola
- **DLQ Messages**: Mensajes en Dead Letter Queue (estrategia 4)

Y luego identifica cuál es mejor para tu caso de uso.

## 🏁 Conclusiones

Cada estrategia tiene su lugar en diferentes arquitecturas:

1. **Simple**: Para casos no críticos con alta performance
2. **Reenvío**: Para lógica compleja de reintento
3. **Visibility Timeout**: Para reintentos automáticos eficientes
4. **Dead Letter Queue**: Para sistemas críticos con análisis de fallos

La elección depende de tus requisitos específicos de **confiabilidad**, **rendimiento** y **observabilidad**.

**Recuerda**: Estas recomendaciones aplican principalmente para **consumidores únicos**. En escenarios con **múltiples consumidores**, considera factores adicionales como concurrencia, orden de mensajes y coordinación entre procesos.

El código completo está disponible en el repositorio [aws-examples](https://github.com/olcortesb/aws-examples/tree/main/sqs/batch-messages) con todas las implementaciones y documentación detallada.

Gracias por leer, ¡Saludos!
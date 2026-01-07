# AWS DocumentDB Streams: Configuración y casos de uso

Entre finales del 2025 y principios del presente año, con el equipo de trabajo de ACKStorm nos enfrentamos a un desafío interesante. Necesitábamos diseñar una arquitectura serverless para una aplicación que necesitaba un manejo de un alto volumen de datos. En el proceso de diseño se identifico que el uso de una DynamoDB no era una buena opción. Con este escenario analizamos el costo de las distintas bases de datos que tenemos en AWS donde DocumentDB se presentó como la mejor opción.

Una de las mejores características, al menos desde mi parecer, que tiene DynamoDB es el [DynamoDB Streams](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Streams.html), feature que permite disparar eventos en base a las modificaciones que se realicen sobre la base e integrarlas con el ecosistema de eventos de AWS(lambda, eventbridge, etc). Bien, DocumentDB tiene streams heredados de MongoDB pero no es directamente integrable con el ecosistema. En este post pretendo mostrar cómo configurar DocumentDB streams e integrarlo al flujo de trabajo de AWS.

## ¿Qué es AWS DocumentDB Stream?

AWS DocumentDB Streams es una funcionalidad que permite capturar y procesar cambios en los datos de una base de datos DocumentDB en tiempo real. Esta característica es especialmente útil para aplicaciones que requieren sincronización de datos, auditoría o integración con otros servicios.

> **Referencia oficial**: [AWS DocumentDB Change Streams](https://docs.aws.amazon.com/documentdb/latest/developerguide/change_streams.html)

### Características principales:

- **Captura de cambios en tiempo real**: Detecta inserciones, actualizaciones y eliminaciones
- **Compatibilidad con MongoDB**: Utiliza la API de Change Streams de MongoDB 3.6+
- **Integración nativa**: Se puede conectar directamente con servicios AWS como Lambda, Kinesis y EventBridge
- **Filtrado granular**: Permite filtrar eventos por colección, operación o campos específicos
- **Durabilidad**: Los eventos se almacenan de forma persistente durante un período configurable

> **Documentación técnica**: [Working with Change Streams](https://docs.aws.amazon.com/documentdb/latest/developerguide/change_streams.html#change_streams-enabling)

## POC: Arquitectura propuesta

![Architecture](/images/dcdb-1.png)

Como muestra la figura, la arquitectura propuesta se basa en una lambda que permite escribir los documentos tomando lo que el API Gateway reciba como un POST desde el exterior, luego eso se envía al DocumentDB y del otro lado del dominio de la aplicación está el Event Bridge que está evaluando cada tiempo (1m para esta POC) si se insertó un nuevo documento.

## EL codigo:

Todo el codigo utilizada para esta POC esta ene este repositorio [Link](https://github.com/olcortesb/aws-documentdb-streams)

## Configuración de DocumentDB Streams

A diferencia de DynamoDB Streams, en DocumentDB es necesario configurarla. Para configurarla se puede hacer a nivel global de la base de datos o a nivel de colecciones; vamos a configurar a nivel de colecciones. También se puede configurar por la línea de comandos o a través de SDK, este segundo será nuestra opción.

```python
def lambda_handler(event, context):
    docdb_uri = os.environ['DOCDB_URI']
    client = None
    
    try:
        print(f"Connecting to DocumentDB...")
        
        # Conectar a DocumentDB con timeouts agresivos
        client = pymongo.MongoClient(
            docdb_uri,
            ssl=True,
            tlsCAFile='global-bundle.pem',
            retryWrites=False,
            connectTimeoutMS=5000,  # 5 segundos
            serverSelectionTimeoutMS=5000,  # 5 segundos
            socketTimeoutMS=10000,  # 10 segundos
            maxPoolSize=1,  # Conexión única
            waitQueueTimeoutMS=2000  # 2 segundos
        )
        
        # Verificar conexión rápidamente
        client.admin.command('ping')
        print("Connected successfully")
        
        db = client['demo_db']
        collection = db['users']
        
        # Habilitar change streams si no están habilitados
        try:
            client.admin.command("modifyChangeStreams", database="demo_db", collection="users", enable=True)
            print("Change streams enabled for collection")
        except Exception as e:
            print(f"Change streams already enabled or error: {e}")
        .... 
```

## Prueba de funcionamiento

Una vez configurado el DocumentDB Stream, nos queda realizar pruebas.

Primero realizamos un POST al API Gateway para agregar un nuevo documento a la DocumentDB.

```sh
~/workspace/aws-documentdb-streams/lambda/writer (main)$ curl -X POST https://umncz7md48.execute-api.us-east-1.amazonaws.com/dev/write   -H "Content-Type: application/json"   -d '{
    "user_id": "user_008",
    "name": "Elena Morales", 
    "email": "elena@example.com"
  }'
# {"message": "Document inserted successfully", "document_id": "695e6e66a68ca00398aeb3ca"}
```

Verificamos el log del lambda-writer:

Registro del Log completo: 

```sh
~/workspace/aws-documentdb-streams/lambda/writer (main)$ aws logs tail /aws/lambda/docdb-streams-demo-writer --since 1m --region us-east-1
## 2026-01-07T14:32:04.611000+00:00 2026/01/07/[$LATEST]8fe741cb1a354837b4c60dfd3ca55f7a INIT_START Runtime Version: python:3.11.v109      Runtime Version ARN: arn:aws:lambda:us-east-1::runtime:49f733259c7ce7e0deee75ff91c6afe35c7d58b04ed300f32701216263b4590c
## 2026-01-07T14:32:05.060000+00:00 2026/01/07/[$LATEST]8fe741cb1a354837b4c60dfd3ca55f7a START RequestId: 717faf29-0efd-470e-925f-12434921dc45 Version: $LATEST
## 2026-01-07T14:32:05.060000+00:00 2026/01/07/[$LATEST]8fe741cb1a354837b4c60dfd3ca55f7a Connecting to DocumentDB...
## 2026-01-07T14:32:05.061000+00:00 2026/01/07/[$LATEST]8fe741cb1a354837b4c60dfd3ca55f7a /var/task/lambda_function.py:14: UserWarning: You appear to be connected to a DocumentDB cluster. For more information regarding feature compatibility and support please visit https://www.mongodb.com/supportability/documentdb
## 2026-01-07T14:32:05.061000+00:00 2026/01/07/[$LATEST]8fe741cb1a354837b4c60dfd3ca55f7a client = pymongo.MongoClient(
## 2026-01-07T14:32:06.044000+00:00 2026/01/07/[$LATEST]8fe741cb1a354837b4c60dfd3ca55f7a Connected successfully
## 2026-01-07T14:32:06.064000+00:00 2026/01/07/[$LATEST]8fe741cb1a354837b4c60dfd3ca55f7a Change streams enabled for collection
## 2026-01-07T14:32:06.064000+00:00 2026/01/07/[$LATEST]8fe741cb1a354837b4c60dfd3ca55f7a Inserting document: {'user_id': 'user_008', 'name': 'Elena Morales', 'email': 'elena@example.com', 'timestamp': datetime.datetime(2026, 1, 7, 14, 32, 6, 64071), 'action': 'user_created'}
## 2026-01-07T14:32:06.074000+00:00 2026/01/07/[$LATEST]8fe741cb1a354837b4c60dfd3ca55f7a Document inserted with ID: 695e6e66a68ca00398aeb3ca
## 2026-01-07T14:32:06.087000+00:00 2026/01/07/[$LATEST]8fe741cb1a354837b4c60dfd3ca55f7a END RequestId: 717faf29-0efd-470e-925f-12434921dc45
## 2026-01-07T14:32:06.087000+00:00 2026/01/07/[$LATEST]8fe741cb1a354837b4c60dfd3ca55f7a REPORT RequestId: 717faf29-0efd-470e-925f-12434921dc45    Duration: 1026.52 ms    Billed Duration: 1470 msMemory Size: 128 MB     Max Memory Used: 58 MB  Init Duration: 443.42 ms
```

Registro específico del momento en que el documento se inserta: 

> Inserting document: {'user_id': 'user_008', 'name': 'Elena Morales', 'email': 'elena@example.com', 'timestamp': datetime.datetime(2026, 1, 7, 14, 32, 6, 64071), 'action': 'user_created'}

Luego verificamos el log del lambda-processor:

Registro del log completo: 

```sh
~/workspace/aws-documentdb-streams/lambda/processor (main)$ aws logs tail /aws/lambda/docdb-streams-demo-stream-processor --since 1m --region us-east-1
## 2026-01-07T14:33:46.795000+00:00 2026/01/07/[$LATEST]25947f9cb15441ee9e09c8af9d068dff INIT_START Runtime Version: python:3.11.v109 Runtime Version ARN: arn:aws:lambda:us-east-1::runtime:49f733259c7ce7e0deee75ff91c6afe35c7d58b04ed300f32701216263b4590c
## 2026-01-07T14:33:47.119000+00:00 2026/01/07/[$LATEST]25947f9cb15441ee9e09c8af9d068dff START RequestId: ba850df0-2e96-4c01-81cd-9e2109db3587 Version: $LATEST
## 2026-01-07T14:33:47.120000+00:00 2026/01/07/[$LATEST]25947f9cb15441ee9e09c8af9d068dff /var/task/lambda_function.py:17: UserWarning: You appear to be connected to a DocumentDB cluster. For more information regarding feature compatibility and support please visit https://www.mongodb.com/supportability/documentdb
## 2026-01-07T14:33:47.120000+00:00 2026/01/07/[$LATEST]25947f9cb15441ee9e09c8af9d068dff client = pymongo.MongoClient(docdb_uri,
## 2026-01-07T14:33:47.824000+00:00 2026/01/07/[$LATEST]25947f9cb15441ee9e09c8af9d068dff Starting change stream listener...
## 2026-01-07T14:33:15.296000+00:00 2026/01/07/[$LATEST]17e2004ee17143808e94c4bd6deb3376 Change detected: insert on document 695e6e66a68ca00398aeb3ca
## 2026-01-07T14:33:15.296000+00:00 2026/01/07/[$LATEST]17e2004ee17143808e94c4bd6deb3376 New document: {"_id": "695e6e66a68ca00398aeb3ca", "user_id": "user_008", "name": "Elena Morales", "email": "elena@example.com", "timestamp": "2026-01-07 14:32:06.064071", "action": "user_created"}
## 2026-01-07T14:33:15.299000+00:00 2026/01/07/[$LATEST]3e242f58567640818f62d8fdd3fb4f5a Change detected: insert on document 695e6e66a68ca00398aeb3ca
## 2026-01-07T14:33:15.299000+00:00 2026/01/07/[$LATEST]3e242f58567640818f62d8fdd3fb4f5a New document: {"_id": "695e6e66a68ca00398aeb3ca", "user_id": "user_008", "name": "Elena Morales", "email": "elena@example.com", "timestamp": "2026-01-07 14:32:06.064071", "action": "user_created"}
```

Registro específico del momento en que el stream detecta el nuevo documento:

> Change detected: insert on document 695e6e66a68ca00398aeb3ca
> New document: {"_id": "695e6e66a68ca00398aeb3ca", "user_id": "user_008", "name": "Elena Morales", "email": "elena@example.com", "timestamp": "2026-01-07 14:32:06.064071", "action": "user_created"}

## Conclusiones

La implementación de AWS DocumentDB Streams es una solución viable para capturar y procesar cambios en tiempo real en aplicaciones serverless de alto volumen cuando DynamoDB no es una opción. Sin embargo, hay que tener en cuenta:

### Ventajas identificadas:

✅ **Integración nativa con el ecosistema AWS**: Aunque requiere configuración adicional comparado con DynamoDB Streams, la integración con Lambda y EventBridge funciona de manera fluida. La desventaja en este punto es que el sistema en general no es reactivo por naturaleza; necesitamos EventBridge para poder detectar el evento. Sin embargo, una vez detectado, lo podemos integrar con el resto del ecosistema. 

✅ **Flexibilidad de configuración**: La posibilidad de habilitar streams a nivel de colección específica permite un control granular sobre qué cambios capturar.

✅ **Compatibilidad con MongoDB**: Al utilizar la API estándar de Change Streams de MongoDB, facilita la migración de aplicaciones existentes.

### Consideraciones importantes:

⚠️ **Configuración manual requerida**: A diferencia de DynamoDB, DocumentDB Streams requiere habilitación explícita por colección.

⚠️ **Gestión de conexiones**: Es crucial implementar timeouts y pooling de conexiones adecuados para evitar problemas de rendimiento.

⚠️ **Monitoreo**: Se recomienda implementar alertas para detectar fallos en el procesamiento de streams.

### Casos de uso recomendados (en el papel, pueden ser muchos más):

- **Sincronización de datos** entre microservicios
- **Auditoría en tiempo real** de cambios en documentos críticos
- **Triggers de notificaciones** basados en cambios de estado
- **Replicación selectiva** de datos a sistemas analíticos

### Importante antes de implementar esta solución en un ambiente productivo:

1. Implementar manejo de errores robusto con DLQ (Dead Letter Queues)
2. Configurar métricas personalizadas en CloudWatch
3. Evaluar el uso de Kinesis Data Streams para mayor throughput
4. Implementar filtros más específicos para optimizar el procesamiento

En resumen, DocumentDB Streams ofrece una alternativa sólida a DynamoDB Streams cuando se requiere flexibilidad de esquemas, volumen alto de datos y compatibilidad con MongoDB, aunque con un overhead de configuración adicional que debe considerarse en el diseño de la arquitectura.

---

Gracias por leer.

¡Saludos!

Oscar Cortés
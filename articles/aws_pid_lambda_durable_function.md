# Control PID con AWS Lambda Durable Functions: Simulando un reactor con estado persistente

## Introducción

Recordando conceptos básicos de mis años de Ing. Electrónica y cómo ha evolucionado, pensaba en cómo sería la implementación de un controlador PID completamente cloud, al menos a modo práctico, en la operativa posiblemente no sea aplicable a todos los sistemas de control. Los controladores PID (Proporcional-Integral-Derivativo) tradicionalmente requieren ejecución continua, estado persistente y ciclos de control precisos. ¿Cómo implementar esto en un entorno serverless donde las funciones son efímeras por naturaleza?

En este artículo presento una prueba de concepto que combina **control PID** con **AWS Lambda Durable Functions**, demostrando cómo crear sistemas de control de larga duración sin "pagar" por tiempo de espera entre iteraciones. La implementación simula un reactor con control de temperatura, utilizando las nuevas capacidades de Lambda para workflows con estado persistente.

## 🎯 ¿Qué es un Controlador PID?

Un controlador PID es un mecanismo de control por retroalimentación ampliamente utilizado en sistemas industriales. Calcula una señal de control basándose en tres elementos:

- **Proporcional (P)**: Responde proporcionalmente al error actual entre el setpoint (SP) y el valor del proceso (PV). Cuanto mayor es el error, mayor es la acción correctiva
- **Integral (I)**: Corrige el error acumulado en el tiempo, eliminando el error residual en estado estacionario
- **Derivativo (D)**: Anticipa cambios futuros basándose en la tasa de cambio del error, proporcionando amortiguación al sistema

La fórmula básica del PID es:

```
CV(t) = Kp·e(t) + Ki·∫e(t)dt + Kd·de(t)/dt
```

Donde:
- `CV`: Control Variable o salida del controlador normalmente en porcentaje (0-100%)
- `e(t)`: Error = SP - PV (Setpoint - Process Variable)
- `SP`: Setpoint o valor deseado
- `PV`: Process Variable o valor actual medido
- `Kp, Ki, Kd`: Constantes de ajuste o ganancias del controlador

**Tipos de respuesta:**

La relación entre las constantes y su aplicación sobre distintos sistemas puede producir tres tipos de respuestas conocidas: 

- **Subamortiguada (underdamped)**: Oscila antes de estabilizarse (overshoot + oscilaciones)
- **Críticamente amortiguada (critically damped)**: Converge lo más rápido posible sin overshoot
- **Sobreamortiguada (overdamped)**: Converge lentamente sin overshoot

## 🚀 ¿Qué son AWS Lambda Durable Functions?

AWS Lambda Durable Functions es una característica nativa que permite crear workflows de larga duración con estado persistente. A diferencia de las funciones Lambda tradicionales, las Durable Functions pueden:

- **Suspenderse sin costo**: `context.wait()` pausa la ejecución sin cargos de cómputo
- **Mantener estado**: Checkpointing automático en cada step
- **Recuperarse de fallos**: Reinicia desde el último checkpoint exitoso
- **Ejecutar por horas/días**: Sin mantener la Lambda activa continuamente

> **Referencia oficial**: [AWS Lambda Durable Functions](https://docs.aws.amazon.com/lambda/latest/dg/durable-getting-started.html)

### Primitivas Core del SDK

```python
from aws_durable_execution_sdk_python import (
    DurableContext,
    durable_execution,
    durable_step,
)
from aws_durable_execution_sdk_python.config import Duration

@durable_step
def my_step(step_context, arg):
    # Lógica con checkpointing automático
    return result

@durable_execution
def lambda_handler(event, context: DurableContext):
    result = context.step(my_step(arg))
    context.wait(Duration.from_seconds(60))  # SIN COSTO
    return result
```

## 🏗️ Arquitectura de la POC

Bueno, si has llegado leyendo hasta aquí ya es hora de jugarnos, construir e ir a la sustancia. Vamos a implementar una POC que nos permita simular en Lambda Durable Functions tanto un PID como un reactor, persistiendo sus estados internamente y gestionando el flujo con las primitivas del SDK.

El sistema sería el que se muestra en la imagen a continuación.

![Arquitectura con Lambda Durable Functions](https://raw.githubusercontent.com/olcortesb/post-article-backup/refs/heads/main/images/pid-9.png)


Bien, ahora, si tuviéramos que simular esto con la versión tradicional de Lambda, necesitaríamos un par de SQS al menos para gestionar el estado y la invocación de las lambdas. La implementación que proponemos sigue este flujo:

![Arquitectura tradicional con SQS](https://raw.githubusercontent.com/olcortesb/post-article-backup/refs/heads/main/images/pid-10.png)


### Componentes principales:

1. **API Gateway**: Recibe el setpoint deseado
2. **PID Controller Lambda**: Ejecuta el loop de control con estado persistente
3. **Reactor Simulator Lambda**: Simula el comportamiento físico del reactor
4. **CloudWatch Metrics**: Almacena métricas para visualización

## 🛠️ Implementación

### Lambda PID Controller

El controlador implementa el algoritmo PID completo usando Durable Functions. El código completo está disponible en el repositorio:

**📁 Código fuente:** [`terraform/src/pid_controller/app.py`](https://github.com/olcortesb/PID-control-with-lambda-durable/blob/main/terraform/src/pid_controller/app.py)

**Componentes principales:**

- **`@durable_step calculate_pid()`**: Implementa el algoritmo PID en forma paralela discreta
- **`@durable_step invoke_reactor()`**: Invoca la Lambda del reactor para obtener la nueva temperatura
- **`@durable_step publish_metrics()`**: Publica métricas a CloudWatch (SetpointTemperature, ActualTemperature, TemperatureError)
- **`@durable_execution lambda_handler()`**: Orquesta el loop de control con `context.step()` y `context.wait()`

**Ecuación PID implementada:**
```python
error = setpoint - current_temp
integral += error * SAMPLE_TIME
derivative = (error - last_error) / SAMPLE_TIME
cv = KP * error + KI * integral + KD * derivative
cv = max(0, min(100, cv))  # Limitar entre 0-100
```

### Lambda Reactor Simulator

El simulador implementa un modelo físico simplificado del reactor. El código completo está disponible en el repositorio:

**📁 Código fuente:** [`terraform/src/reactor_simulator/app.py`](https://github.com/olcortesb/PID-control-with-lambda-durable/blob/main/terraform/src/reactor_simulator/app.py)

**Componentes principales:**

- **`@durable_step simulate_reactor_step()`**: Simula el comportamiento térmico del reactor
- **`@durable_execution lambda_handler()`**: Recibe el control value y retorna la nueva temperatura

**Física del reactor implementada:**
```python
# Enfriamiento natural (Ley de enfriamiento de Newton)
cooling = (current_temp - AMBIENT_TEMP) * COOLING_RATE

# Calentamiento por control value (0-100)
heating = control_value * HEATING_EFFICIENCY

# Cambio de temperatura con inercia térmica
temp_change = heating - cooling
new_temp = current_temp + temp_change * (1 - THERMAL_INERTIA)
```

## 🚀 Despliegue con Terraform

Inicialmente el despliegue lo realizaría con AWS SAM, sin embargo encontré algunos issues con la integración del SDK con AWS SAM. La alternativa era agregarle una lambda layer, pero no quería probar Lambda Durable fuera de la configuración más básica, por lo tanto me mudé a Terraform para el despliegue.

### Configuración de Lambda Durable

En Terraform, las funciones durable requieren configuración específica:

```hcl
resource "aws_lambda_function" "pid_controller" {
  filename         = data.archive_file.pid_controller.output_path
  function_name    = "${var.project_name}-pid-controller"
  role             = aws_iam_role.pid_controller.arn
  handler          = "app.lambda_handler"
  runtime          = "python3.13"
  timeout          = 900
  memory_size      = 128
  publish          = true

  durable_config {
    execution_timeout = 3600  # 1 hora
    retention_period  = 7     # 7 días
  }

  logging_config {
    log_format = "JSON"
    log_group  = aws_cloudwatch_log_group.pid_controller.name
  }

  environment {
    variables = {
      REACTOR_FUNCTION_NAME = "${aws_lambda_function.reactor_simulator.function_name}:prod"
      KP                    = "0.50"
      KI                    = "0.0004"
      KD                    = "0.20"
      SAMPLE_TIME           = "60"
      MAX_ITERATIONS        = "40"
    }
  }
}
```

### IAM Policy para Durable Functions

```hcl
resource "aws_iam_role_policy_attachment" "pid_controller_durable" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicDurableExecutionRolePolicy"
  role       = aws_iam_role.pid_controller.name
}
```

## 🧪 Pruebas y Simulación

Cómo lo probamos: dejamos un valor esperado para que el PID use como referencia realizando un CURL al API Gateway y empezamos a ver cómo se comporta el sistema.

### Iniciar Control PID

```bash
curl -X POST https://xxxxx.execute-api.us-east-1.amazonaws.com/prod/setpoint \
  -H "Content-Type: application/json" \
  -d '{"setpoint": 75.0}'
```

Respuesta:
```json
{
  "message": "PID control completed - 40 iterations",
  "final_temperature": 74.82,
  "setpoint": 75.0,
  "iterations": 40
}
```

### ¿Cómo se ven los Steps?

![Ejecuciones Lambda Durable](https://raw.githubusercontent.com/olcortesb/post-article-backup/refs/heads/main/images/pid-6.png)

Una nueva pestaña (1) nos mostrará cómo se ven las ejecuciones de toda la Lambda Durable Function, indicando qué versión (2) está corriendo, indicando un ID (3) y el estado de la ejecución (4).

### La relación de las máquinas de estado de las dos lambdas

Una de las features más interesantes es que podemos aprovechar la persistencia del estado evitando colocar SQS, DynamoDB, S3 dependiendo del caso, y ahora podemos llamar a otra función directamente gracias a la gestión de la máquina de estado. 

![Interacciones entre steps y waits](https://raw.githubusercontent.com/olcortesb/post-article-backup/refs/heads/main/images/pid-7.png)

En la imagen arriba, 1 y 2 muestran las interacciones entre los steps y los waits, que indicamos antes en el presente artículo. Lo interesante es que se ve claramente el invoke_reactor que para nuestra simulación es invocar a otra Lambda Durable Function que permitirá simular el estado del reactor, guardando la temperatura y la inercia térmica del mismo.

![Ejecución del reactor simulator](https://raw.githubusercontent.com/olcortesb/post-article-backup/refs/heads/main/images/pid-8.png)

Ya dentro de la Lambda del reactor podemos ver cómo se ejecutan los pasos que recalculan el comportamiento del reactor respecto a la temperatura, simulando el comportamiento real de un reactor.

### La respuesta final:

Para visualizar de manera aproximada cómo se estudian las gráficas de los sistemas PID, creé un dashboard que pueden consultar en el código fuente:

[Código en Terraform del dashboard](https://github.com/olcortesb/PID-control-with-lambda-durable/blob/main/terraform/dashboard.tf)

![Dashboard CloudWatch](https://raw.githubusercontent.com/olcortesb/post-article-backup/refs/heads/main/images/pid-4.png)

Los valores configurados son para obtener una respuesta críticamente amortiguada que sería el objetivo a perseguir para un sistema de control tipo PID. Los valores los encontré realizando una simulación en Python que muestro a continuación. 

### Simulación Local

Sí, esto podría ser otro post, pero he disfrutado tanto haciendo este artículo que lo dejo por aquí. Como quería refrescar cómo funcionaba el PID, me creé un proyecto que es básicamente un simulador Python para probar diferentes configuraciones de PID. En base a esta simulación encontré los valores que colocamos al sistema simulado en la POC. 

```bash
cd simulation

# Configurar parámetros en .env
cat > .env << EOF
KP=0.50
KI=0.0004
KD=0.20
SETPOINT=75.0
SAMPLE_TIME=30
MAX_ITERATIONS=40
THERMAL_INERTIA=0.18
EOF

# Ejecutar simulación
python simulate_pid.py
```

### Resultados de Simulación

El simulador genera gráficas mostrando el comportamiento del sistema con diferentes configuraciones de PID. Todas las simulaciones utilizan:
- **Setpoint**: 75°C
- **Temperatura inicial**: 20°C
- **Sample time**: 30 segundos
- **Iteraciones**: 40
- **Inercia térmica**: 0.18

#### Configuración 1: Kp=0.20, Ki=0.0001, Kd=0.30 (Sobreamortiguada)

![Respuesta Sobreamortiguada](https://raw.githubusercontent.com/olcortesb/post-article-backup/refs/heads/main/images/pid_kp0.20_ki0.0001_kd0.30_ti0.18_st30_iter40_sp75.0.png)

**Características observadas:**
- Convergencia lenta y suave sin overshoot
- Tiempo de estabilización: ~20 minutos
- Temperatura final: ~74.5°C
- Error final: ~0.5°C
- Control Value máximo: ~15%
- **Comportamiento**: Sistema muy conservador, ideal cuando no se permiten sobrepasadas

#### Configuración 2: Kp=0.50, Ki=0.0004, Kd=0.20 (Críticamente amortiguada)

![Respuesta Críticamente Amortiguada](https://raw.githubusercontent.com/olcortesb/post-article-backup/refs/heads/main/images/pid_kp0.50_ki0.0004_kd0.20_ti0.18_st30_iter40_sp75.0.png)

**Características observadas:**
- Convergencia rápida sin overshoot significativo
- Tiempo de estabilización: ~15 minutos
- Temperatura final: ~74.8°C
- Error final: ~0.2°C
- Control Value máximo: ~30%
- **Comportamiento**: Balance óptimo entre velocidad y estabilidad

#### Configuración 3: Kp=1.2, Ki=0.002, Kd=0.1 (Subamortiguada)

![Respuesta Subamortiguada](https://raw.githubusercontent.com/olcortesb/post-article-backup/refs/heads/main/images/pid_kp1.2_ki0.002_kd0.1_ti0.18_st30_iter40_sp75.0.png)

**Características observadas:**
- Convergencia muy rápida con overshoot
- Overshoot máximo: ~2°C (alcanza ~77°C)
- Oscilaciones visibles antes de estabilizar
- Tiempo de estabilización: ~12 minutos
- Temperatura final: ~75.0°C
- Error final: ~0.05°C
- Control Value máximo: ~70%
- **Comportamiento**: Sistema agresivo, respuesta rápida pero con oscilaciones

## 📊 Verificación de Resultados

### CloudWatch Logs

Los logs muestran cada iteración del control:

```
{
  "timestamp": "2026-01-15T10:30:45.123Z",
  "level": "INFO",
  "message": "Iteration 15: Setpoint=75.00, Temp=72.34, CV=45.67"
}
```

### CloudWatch Metrics

Las métricas publicadas permiten visualizar:
- **SetpointTemperature**: Temperatura deseada (constante)
- **ActualTemperature**: Temperatura real del reactor
- **TemperatureError**: Error absoluto

Para visualizar en CloudWatch:
1. Ir a CloudWatch Console → Metrics
2. Buscar namespace "PIDControl-v2"
3. Crear dashboard con las tres métricas

### Logs del Reactor

```
{
  "timestamp": "2026-01-15T10:30:45.456Z",
  "level": "INFO",
  "message": "Reactor: CV=45.67, Temp=72.34, Ambient=20.0"
}
```

## 💡 Ventajas de Lambda Durable Functions

### ✅ Sin Costo Durante Esperas

El uso de `context.wait()` es una de las características más poderosas de Lambda Durable Functions. Según la [documentación oficial de AWS](https://docs.aws.amazon.com/lambda/latest/dg/durable-functions-how-it-works.html), cuando una función durable está en estado de espera usando `context.wait()`, **no se cobra por tiempo de cómputo**.

```python
# ❌ Antes: Lambda ejecutándose = $$$
time.sleep(60)  # Pagas por 60 segundos de ejecución

# ✅ Ahora: Lambda suspendida = $0
context.wait(Duration.from_seconds(60))  # Sin cargo durante la espera
```

**Ejemplo de ahorro de costos** para el caso de nuestro control PID con SAMPLE_TIME de 60 segundos y 40 iteraciones:
- **Sin Durable**: 40 minutos de ejecución continua = 2,400 segundos facturables
- **Con Durable**: ~5 segundos de ejecución real (solo cómputo activo) = 5 segundos facturables
- **Ahorro**: ~99.8% en costos de cómputo

> **Referencia**: [How Lambda Durable Functions work - AWS Documentation](https://docs.aws.amazon.com/lambda/latest/dg/durable-functions-how-it-works.html)

### ✅ Checkpointing Automático

Cada `context.step()` guarda el estado:

```python
# Si falla aquí, reinicia desde el último step exitoso
pid_result = context.step(calculate_pid(...))  # ✓ Checkpoint
reactor_data = context.step(invoke_reactor(...))  # ✓ Checkpoint
context.step(publish_metrics(...))  # ✓ Checkpoint
```

### ✅ Sin Infraestructura Extra

Comparación con arquitecturas tradicionales:

**Sin Durable Functions:**
- DynamoDB para estado
- SQS para coordinación
- EventBridge para scheduling
- Step Functions para workflow

**Con Durable Functions:**
- Solo Lambda (estado incluido)

### ✅ Código Más Simple

El código es más legible y mantenible:

```python
# Loop natural con estado persistente
for iteration in range(MAX_ITERATIONS):
    pid_result = context.step(calculate_pid(...))
    reactor_data = context.step(invoke_reactor(...))
    context.step(publish_metrics(...))
    context.wait(Duration.from_seconds(SAMPLE_TIME))
```

## 📋 Casos de Uso Prácticos

Según el [blog oficial de AWS](https://aws.amazon.com/es/blogs/aws/build-multi-step-applications-and-ai-workflows-with-aws-lambda-durable-functions/) y la [documentación técnica](https://docs.aws.amazon.com/lambda/latest/dg/durable-functions-use-cases.html), Lambda Durable Functions es especialmente útil para escenarios donde se requieren workflows de larga duración con estado persistente. Los casos de uso documentados incluyen: **workflows de aprobación humana** donde los procesos esperan aprobaciones sin mantener recursos activos; **procesamiento de datos por lotes** como ETL jobs que esperan entre etapas; **orquestación de microservicios** para coordinar múltiples servicios con estado; **monitoreo y polling** para sistemas que verifican condiciones periódicamente; y **workflows de IA y ML** para pipelines de entrenamiento y procesamiento de modelos. Estos patrones aprovechan la capacidad de `context.wait()` para suspender la ejecución sin cargos de cómputo, haciendo viable económicamente mantener workflows activos durante períodos prolongados.

> **Referencias**: [AWS Blog - Lambda Durable Functions](https://aws.amazon.com/es/blogs/aws/build-multi-step-applications-and-ai-workflows-with-aws-lambda-durable-functions/) | [Use Cases Documentation](https://docs.aws.amazon.com/lambda/latest/dg/durable-functions-use-cases.html)

## ⚠️ Consideraciones Importantes

### Límites del Servicio

Según la [documentación oficial de AWS Lambda Durable Functions](https://docs.aws.amazon.com/lambda/latest/dg/durable-functions-quotas.html):

- **Execution timeout**: Sin límite de tiempo total de ejecución (la función puede ejecutarse indefinidamente usando `context.wait()`)
- **Individual function timeout**: Máximo 15 minutos por invocación individual de función
- **Retention period**: Máximo 1 año (365 días) para estado persistente
- **Payload size**: Máximo 256 KB por step
- **Maximum concurrent executions**: Sujeto a las cuotas de concurrencia de Lambda de la cuenta

> **Nota importante**: Aunque no hay límite en el tiempo total de ejecución durable, cada invocación individual de la función Lambda está limitada a 15 minutos. El estado se persiste automáticamente entre invocaciones.

### Mejores Prácticas

1. **Usar steps granulares**: Cada step debe ser una unidad lógica de trabajo
2. **Limitar payload**: Pasar solo datos necesarios entre steps
3. **Implementar timeouts**: Configurar timeouts apropiados para cada función
4. **Monitorear métricas**: Usar CloudWatch para detectar problemas
5. **Manejar errores**: Implementar retry logic en steps críticos

### Cuándo NO usar Durable Functions

- **Latencia ultra-baja**: Si necesitas respuesta en milisegundos
- **Alto throughput**: Para miles de ejecuciones concurrentes
- **Workflows complejos**: Step Functions puede ser mejor opción
- **Estado muy grande**: Si el estado excede 256 KB

## 📊 Conclusiones (Para nuestro caso de prueba PID)

Esta POC intente validar que es posible implementar un sistema de control PID en arquitecturas serverless usando AWS Lambda Durable Functions. y lo que podemos identificar como concluciones, comparado con el uso de AWS lambda tradicional sin 'Durable Function' seria:

**Economía**: `context.wait()` elimina costos de tiempo de espera entre iteraciones

**Simplicidad**: Código más limpio sin necesidad de DynamoDB, SQS o Step Functions

**Resiliencia**: Checkpointing automático permite recuperación ante fallos

**Flexibilidad**: Fácil ajuste de parámetros PID y configuración del reactor

**Escalabilidad**: Cada control PID es independiente y puede escalar horizontalmente

### Limitaciones identificadas:

⚠️ **Latencia**: No apto para control en tiempo real (< 1 segundo)

⚠️ **Cold starts**: Primera invocación puede tardar 2-3 segundos

⚠️ **Debugging**: Más complejo que funciones Lambda tradicionales

### Aplicaciones potenciales:

- Control de temperatura en invernaderos
- Gestión de niveles en tanques de almacenamiento
- Regulación de pH en tratamiento de aguas
- Control de humedad en almacenes
- Sistemas HVAC con requisitos de latencia relajados

El código completo está disponible en [GitHub](https://github.com/olcortesb/PID-control-with-lambda-durable) con Terraform listo para desplegar, simulador Python para pruebas locales, y documentación detallada sobre Lambda Durable Functions.

## 🔗 Referencias y Enlaces Útiles

- [AWS Lambda Durable Functions - Quotas](https://docs.aws.amazon.com/lambda/latest/dg/durable-functions-quotas.html)
- [AWS Lambda Durable Functions - Blog Oficial](https://aws.amazon.com/es/blogs/aws/build-multi-step-applications-and-ai-workflows-with-aws-lambda-durable-functions/)
- [Documentación Oficial - Getting Started](https://docs.aws.amazon.com/lambda/latest/dg/durable-getting-started.html)
- [SDK Python - PyPI](https://pypi.org/project/aws-durable-execution-sdk-python/)
- [Developing with SAM](https://dev.to/aws/developing-aws-lambda-durable-functions-with-aws-sam-ga9)
- [Control PID - Wikipedia](https://es.wikipedia.org/wiki/Controlador_PID)
- [Regulación PID para Dummies - Fuji Electric](https://www.fujielectric.fr/es/blog/regulacion-pid-para-dummies-todo-lo-que-necesita-saber/)
- [Terraform AWS Lambda Resources](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_function)

---

Gracias por leer.

¡Saludos!

Oscar Cortés

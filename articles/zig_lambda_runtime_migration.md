---
title: "Migrando zig-lambda-runtime de Zig 0.12 a 0.16 en AWS Lambda"
description: "Experiencia migrando un runtime de AWS Lambda escrito en Zig de la versión 0.12 a 0.16, sin ser experto en el lenguaje"
pubDate: 2025-07-14T12:00:00.000Z
tags: ["zig", "aws", "lambda", "serverless"]
draft: false
---

![alt text](../images/zig_lambda_runtime.png)

# Migrando zig-lambda-runtime de Zig 0.12 a 0.16 en AWS Lambda

No soy experto en Zig, pero como me he divertido en esta prueba de concepto! Si han leído alguna vez algún artículo saben que lo que me interesa es probar cómo funciona Lambda en cualquier entorno posible, en esta oportunidad, con un lenguaje de bajo nivel como Zig dentro de AWS Lambda, aprovechando el runtime `provided.al2023` y la arquitectura ARM64. Este artículo documenta la migración del fork [zig-lambda-runtime](https://github.com/softprops/zig-lambda-runtime) que originalmente fue desarrollado por [softprops](https://github.com/softprops) de Zig 0.12 a 0.16.

## Por qué Zig en Lambda

Por estos números...

- Cold start promedio: 11ms
- Memoria: 10MB
- Duración promedio: 1-2ms

Zig compila a un binario estático sin dependencias externas. No necesitas capas, no necesitas Docker. Solo un binario llamado `bootstrap` dentro de un zip.

Aunque necesito hacer más pruebas y compararlo, por ejemplo, con Rust, que es un lenguaje con el mismo concepto de no recolector de basura y alta performance, la verdad que promete que puede ser interesante.

## Cambios principales en la migración

Y mientras aprendo un poco de Zig aquí los cambios que he hecho, que puede haber más y mejores pero la intención era hacerlo funcionar!

### build.zig.zon

En 0.12 el nombre del paquete era un string. En 0.16 es un enum literal y se requiere un `fingerprint`:

```zig
// 0.12
.name = "lambda",
.minimum_zig_version = "0.12.0",

// 0.16
.name = .lambda,
.minimum_zig_version = "0.16.0",
.fingerprint = 0xd39dff828a4fab32,
```

El fingerprint se obtiene omitiendo el campo y dejando que Zig te diga el valor correcto en el primer build.

### build.zig

La API de build cambió. Antes se usaba `createModule` + `modules.put`, ahora es `addModule` directo. Los ejecutables usan `root_module` en vez de `root_source_file`:

```zig
// 0.16
const lambda_module = b.addModule("lambda", .{
    .root_source_file = b.path("src/lambda.zig"),
    .link_libc = true,
});

const exe = b.addExecutable(.{
    .name = "bootstrap",
    .root_module = b.createModule(.{
        .root_source_file = b.path(example.src),
        .target = target,
        .optimize = optimize,
    }),
});
exe.root_module.addImport("lambda", lambda_module);
```

### HTTP Client

El cambio más grande. En 0.12 existía `client.fetch()` como método de conveniencia. En 0.16 el ciclo de vida del request es explícito para el polling de invocaciones, aunque `fetch` sigue disponible para requests simples como enviar respuestas:

```zig
// Polling de invocaciones (explícito)
var threaded: std.Io.Threaded = .init(alloc, .{});
const io = threaded.io();
var client: std.http.Client = .{ .allocator = alloc, .io = io };
defer client.deinit();

const uri = std.Uri.parse(next_url) catch return error.InvalidNextUri;
var req = try client.request(.GET, uri, .{});
defer req.deinit();
try req.sendBodiless();

var header_buf: [8 * 1024]u8 = undefined;
var response = try req.receiveHead(&header_buf);
var reader = response.reader(&.{});
const body = try reader.allocRemaining(alloc, .unlimited);
```

```zig
// Enviar respuesta (fetch sigue funcionando)
_ = try client.fetch(.{
    .location = .{ .url = url },
    .method = .POST,
    .payload = payload,
});
```

### GeneralPurposeAllocator

Cambio menor en la sintaxis de inicialización:

```zig
// 0.12
var gpa = std.heap.GeneralPurposeAllocator(.{}){};

// 0.16
var gpa: std.heap.GeneralPurposeAllocator(.{}) = .{};
```

### Env y manejo de errores

Se reemplazó el `.?` (que hace panic si es null) por `orelse` para manejo graceful:

```zig
// 0.12 - panic si no existe
const runtime_api = std.posix.getenv("AWS_LAMBDA_RUNTIME_API").?;

// 0.16 - retorna error
const runtime_api = getenv("AWS_LAMBDA_RUNTIME_API") orelse return error.MissingLambdaEnv;
```

## Deploy

El deploy usa SAM con un template mínimo:

```yaml
Resources:
  Function:
    Type: AWS::Serverless::Function
    Properties:
      Runtime: provided.al2023
      Architectures:
        - arm64
      MemorySize: 128
      CodeUri: "../lambda.zip"
      Handler: handler
      FunctionUrlConfig:
        AuthType: NONE
```

El flujo completo:

```bash
# Build para ARM64 Linux
zig build apigw-example -Dtarget=aarch64-linux --summary all

# Empaquetar
zip -jq lambda.zip zig-out/bin/bootstrap

# Deploy
cd infra && sam deploy
```

## Bugs corregidos en la migración

1. `remaining_time_ms` llamaba `deadline_ms` como función cuando es un campo, y el orden de la resta estaba invertido.
2. Variables indefinidas en el parsing de headers, reemplazadas por tipos nullable.
3. Lectura del body del response usando `reader().readAllAlloc()` en vez del patrón manual con ArrayList.

## Resultado

La Lambda despliega y responde correctamente. El binario compilado para ARM64 es pequeño y los tiempos de respuesta se mantienen en el rango de 1-2ms después de la migración.

```bash
curl -s $(aws lambda get-function-url-config \
  --function-name zig-demo \
  --region us-east-1 \
  --query 'FunctionUrl' \
  --output text)
 # {"message":"hello world"} 
```

Ejecuté 100 invocaciones con un script de benchmark y estos son los reportes de CloudWatch:

```
REPORT RequestId: e6c0c71c-...  Duration: 1.64 ms   Billed Duration: 2 ms   Memory Size: 128 MB  Max Memory Used: 13 MB
REPORT RequestId: 85c863bf-...  Duration: 1.57 ms   Billed Duration: 2 ms   Memory Size: 128 MB  Max Memory Used: 13 MB
REPORT RequestId: 9819ece8-...  Duration: 1.54 ms   Billed Duration: 2 ms   Memory Size: 128 MB  Max Memory Used: 13 MB
REPORT RequestId: 074f600b-...  Duration: 1.63 ms   Billed Duration: 2 ms   Memory Size: 128 MB  Max Memory Used: 13 MB
REPORT RequestId: da687f87-...  Duration: 10.08 ms  Billed Duration: 11 ms  Memory Size: 128 MB  Max Memory Used: 13 MB
REPORT RequestId: c7575544-...  Duration: 1.49 ms   Billed Duration: 2 ms   Memory Size: 128 MB  Max Memory Used: 14 MB
REPORT RequestId: e02e5bb4-...  Duration: 12.16 ms  Billed Duration: 13 ms  Memory Size: 128 MB  Max Memory Used: 14 MB
REPORT RequestId: 158b7657-...  Duration: 1.39 ms   Billed Duration: 2 ms   Memory Size: 128 MB  Max Memory Used: 14 MB
```

Resumen:
- Duration típica: ~1.5ms
- Picos ocasionales: 10-12ms (cold starts o micro-pauses del runtime)
- Memoria usada: 13-14 MB de 128 MB asignados
- Billed duration: 2ms en la mayoría de invocaciones

Posiblemente Zig no es un lenguaje que se esté usando masivamente, pero como ejercicio para entender cómo funciona un custom runtime en Lambda y qué tan lejos se puede llegar en performance, es interesante. La migración de 0.12 a 0.16 no fue trivial por los cambios en la stdlib (especialmente el HTTP client), pero el compilador te guía bastante bien con los errores.

## Referencias

- [AWS Lambda Runtime API](https://docs.aws.amazon.com/lambda/latest/dg/runtimes-api.html)
- [zig-lambda-runtime (softprops)](https://github.com/softprops/zig-lambda-runtime)
- [Zig 0.16.0 Release Notes](https://ziglang.org/download/0.16.0/release-notes.html)

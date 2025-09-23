# Kiro: Primeras impresiones y configuración de MCPs

![kiro_1](/images/kiro-1.png)

No soy un usuario avanzado de herramientas de IA, sin embargo en el último [AWS Meetup Madrid](https://www.meetup.com/madrid-amazon-web-services-meetup/events/310420236/?eventOrigin=group_past_events), nos acompañó [Alejandro Veliz Fernandes](https://www.linkedin.com/in/alevzfdez/) como uno de los ponentes. Durante su charla en demos interactivas nos mostró una visión general de cómo funciona [KIRO](https://kiro.dev/), entrando en detalles en la parte que más me interesa de la IA, los límites de la herramienta (Guard rail) y la seguridad de nuestra información. Después de escuchar y tener una charla interesante con Alejandro y coincidiendo que me llegó el código de acceso a probar KIRO, aprovecharemos este *post* para explorar **KIRO**, un asistente de IA especializado en desarrollo de software, revisaremos cómo configurar el **Model Context Protocol (MCP)** para extender sus capacidades (intentando usarlo para algo mas que un chatbot) y revisaremos su configuración básica.

## 🚀 En primer lugar ¿Qué es Kiro?

Mi opinión: **Kiro** es un IDE que en su esencia es un fork de VSCode (es igual...) soportado en su desarrollo por AWS, que permite el acceso a él sin tener una cuenta de AWS y orientado a un desarrollo basado en especificaciones. Kiro tiene una versión free y varias alternativas de pago que exploraremos más adelante en futuros posts.

Según la documentación oficial de AWS: Kiro es una herramienta que permite construir exactamente lo que quieres y está listo para compartir con tu equipo. Los agentes de Kiro te ayudan a resolver problemas desafiantes y automatizar tareas como generar documentación y pruebas unitarias.

> [Documentación oficial AWS - Kiro](https://docs.aws.amazon.com/signin/latest/userguide/builder_id-apps.html)

**Características principales:**

- **Desarrollo spec-driven**: Convierte prompts en especificaciones detalladas y código funcional
- **Agentes inteligentes**: Automatización de tareas complejas como documentación y testing
- **Autonomía configurable**: Modo Autopilot para cambios automáticos o modo Supervisado para revisión
- **Contexto inteligente**: Acceso a archivos (#File), carpetas (#Folder), problemas (#Problems), terminal (#Terminal) y diferencias de Git (#Git Diff)
- **Integración completa**: Puede leer, escribir, modificar archivos y ejecutar comandos del sistema 🚥 + ⚠️.
- **Extensibilidad**: Soporte para MCP (Model Context Protocol) para conectar herramientas externas

## ¿ Como instalarlo?

Al momento de escribir este post el acceso es a través de un *waitlist* y está en "Preview", pero se está liberando rápido: <https://kiro.dev/waitlist/>

![kiro_5](/images/kiro-5.png)

## ¿Qué tiene de novedoso? para mí...

Al abrir el panel de Kiro se despliega una barra lateral por defecto que tiene 4 elementos: Specs, Agent Hooks, Agent Steering, MCP Servers, en principio tengo pensado escribir un post de cada uno (este será sobre MCP), pero vamos a describirlos:

![kiro_6](/images/kiro-6.png)

### Specs (Especificaciones)

Las Specs son una forma estructurada de construir y documentar funcionalidades que quieres desarrollar con Kiro. Es básicamente una formalización del proceso de diseño e implementación que te permite:

- Iterar con el agente sobre requerimientos, diseño y tareas de implementación
- Desarrollo incremental de funcionalidades complejas con control y retroalimentación
- Documentar el proceso desde la concepción hasta la implementación
- Incluir referencias a archivos usando la sintaxis #[[file:<nombre_archivo_relativo>]] para incorporar specs de OpenAPI, GraphQL, etc.

## Steering (Dirección/Guía)

Steering te permite incluir contexto adicional e instrucciones que se aplican a todas o algunas de tus interacciones con Kiro. Se almacenan en .kiro/steering/*.md y pueden ser:

**Tipos de inclusión:**

- Siempre incluidos (comportamiento por defecto)
- Condicionales cuando se lee un archivo específico (usando front-matter con inclusion: fileMatch y fileMatchPattern: 'README*')
- Manuales cuando los proporcionas vía contexto con '#' en el chat (configurado con inclusion: manual)

## Agent Hooks (Automatización a la mano...)

Los Agent Hooks son la capacidad de Kiro para crear ejecuciones automáticas del agente que se activan cuando ocurre un evento específico (o cuando el usuario hace clic en un botón) en el IDE.

**Ejemplos de hooks:**

- Al guardar código: Cuando guardas un archivo de código, se activa automáticamente una ejecución para actualizar y ejecutar tests
- Al actualizar traducciones: Cuando modificas strings de traducción, se asegura de que otros idiomas también se actualicen
- Hook manual de spell-check: Cuando haces clic en un botón de 'revisión ortográfica', revisa y corrige errores gramaticales en tu archivo README

## 🔧 ¿Qué es el Model Context Protocol (MCP) - El 4 de las lista?

El **Model Context Protocol (MCP)** es un estándar que permite a aplicaciones de IA conectarse con herramientas y servicios externos, extendiendo significativamente sus capacidades más allá del desarrollo básico. En nuestro caso la aplicación de IA que queremos extender es Kiro.

**Beneficios del MCP:**

- **Extensibilidad**: Conecta con APIs, bases de datos, servicios cloud
- **Automatización**: Integra workflows complejos en tu flujo de desarrollo
- **Personalización**: Adapta Kiro a las necesidades específicas de tu proyecto

> [Documentación oficial MCP](https://modelcontextprotocol.io/)

## 📋 Configuración Inicial de MCP

### Paso 1: Estructura de configuración

Kiro utiliza archivos de configuración JSON para gestionar las conexiones MCP, tenemos dos opciones , configuración a nivel global y configuración a nivel de workspaces:

```bash
# Configuración a nivel de workspace
.kiro/settings/mcp.json

# Configuración global del usuario
~/.kiro/settings/mcp.json
```

### Paso 2: Instalación de dependencias

Para la mayoría de servidores MCP necesitarás **uv** y **uvx**:

```bash
# Instalación usando pip
pip install uv

# O usando homebrew (macOS)
brew install uv

# Verificar instalación
uvx --version
```

## 🛠️ Configuración de Servidores MCP

### Ejemplo 1: Servidor de Documentación AWS

Configuramos un servidor MCP para acceder a la documentación de AWS:

```json
{
  "mcpServers": {
    "aws-docs": {
      "command": "uvx",
      "args": ["awslabs.aws-documentation-mcp-server@latest"],
      "env": {
        "FASTMCP_LOG_LEVEL": "ERROR"
      },
      "disabled": false,
      "autoApprove": [],
      "disabledTools": []
    }
  }
}
```

Y podemos ver en el panel lateral específico de Kiro en la sección de MCP los que tenemos configurados y activos o desactivados, como muestra la imagen:

![kiro_4](/images/kiro-4.png)

### Ejemplo 2: Servidor de Sistema de Archivos

Para operaciones avanzadas con archivos y directorios:

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "uvx",
      "args": ["mcp-server-filesystem@latest"],
      "env": {
        "ALLOWED_DIRECTORIES": "/home/user/projects,/tmp"
      },
      "disabled": false,
      "autoApprove": ["list_directory", "read_file"],
      "disabledTools": ["delete_file"]
    }
  }
}
```

## 🧪 Casos de Uso Prácticos

### Caso 1: Consulta de Documentación AWS

Con el servidor AWS configurado, puedes preguntar directamente:

```text
"¿Cómo configuro un bucket S3 con cifrado?"
```

![kiro-2](/images/kiro-2.png)

![kiro-2](/images/kiro-3.png)

Kiro accederá automáticamente a la documentación oficial de AWS y te proporcionará información actualizada y precisa.

### Caso 2: Análisis de Logs del Sistema

```text
"Analiza los logs de error de la última hora en /var/log/application.log"
```

Con el servidor de filesystem, Kiro puede leer y analizar archivos de log directamente.

### Caso 3: Integración con APIs Externas

```json
{
  "mcpServers": {
    "github-api": {
      "command": "uvx",
      "args": ["mcp-server-github@latest"],
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      },
      "disabled": false,
      "autoApprove": ["get_repository", "list_issues"],
      "disabledTools": ["delete_repository"]
    }
  }
}
```

## ⚙️ Configuración Avanzada para el MCP

### Gestión de Permisos ( Fundamental )

**autoApprove**: Lista de herramientas que se ejecutan automáticamente sin confirmación

```json
"autoApprove": ["read_file", "list_directory", "get_documentation"]
```

**disabledTools**: Herramientas específicas que quieres deshabilitar

```json
"disabledTools": ["delete_file", "format_disk", "shutdown_system"]
```

### Variables de Entorno (Usar en local, nunca subir al repositorio)

Permite usar variables de entorno para configuraciones sensibles, usar responsablemente ⚠️: Sigo sin tener claro que podamos pasar a cualquier herramienta información sensible de cliente pero evaluaré qué ofrece Kiro en este aspecto a futuro.

> Recomendado a nivel de Workspace: .kiro/settings/mcp.json

```json
{
  "env": {
    "API_KEY": "${MY_API_KEY}",
    "DATABASE_URL": "${DB_CONNECTION_STRING}"
  }
}
```

## 🔗 Referencias y Enlaces Útiles

- [Documentación oficial de Kiro](https://kiro.ai/docs)
- [Model Context Protocol Specification](https://modelcontextprotocol.io/)
- [Instalación de uv](https://docs.astral.sh/uv/getting-started/installation/)
- [Repositorio MCP Servers](https://github.com/modelcontextprotocol/servers)
- [AWS MCP Server](https://github.com/awslabs/aws-documentation-mcp-server)
- [Kiro Steering Documentation](https://kiro.ai/docs/steering)
- [Kiro Hooks Guide](https://kiro.ai/docs/hooks)

## 📈 Conclusiones

- ✅ **Kiro** Es un fork de VSCode, esto maximiza la compatibilidad.
- ✅ **Kiro + MCP** Me pareció ágil de configurar.
- ✅ **Configuración flexible** me parece interesante que tenga configuración para cada contexto y se puedan tener MCP en cada proyecto de manera independiente.
- ✅ **Extensibilidad ilimitada** No soy experto en MCP, pero aparentemente si lo puedes configurar puedes usarlo.
- ✅ **Integración nativa** Es compatible con lo que la mayoría usamos todos los días VSCode.
- ✅ Es una alternativa interesante a [cursor](https://cursor.com/)
- ⚠️ Sigo sin usarlo para que me genere código de aplicaciones de manera directa para cliente final.

**Próximos pasos:**

- Explorar los SPECS y tratar de saltarlos/romperlos para ver cómo funcionan.
- Configurar hooks automáticos para tareas repetitivas, con esto puede estar interesante el proceso de mejorar nuestro desarrollo.
- Implementar steering rules para estándares de equipo
- Crear servidores MCP personalizados para APIs internas a largo plazo claro ☺️.

Gracias por leer, Saludos…

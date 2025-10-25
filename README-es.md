# MCP Forge Python - Plantilla de Servidor MCP Production-Ready

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Unlicense-blue.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://hub.docker.com)
[![CI](https://img.shields.io/github/actions/workflow/status/bercianor/mcp-forge-python/ci.yml)](https://github.com/bercianor/mcp-forge-python/actions)
[![Coverage](https://bercianor.es/mcp-forge-python/badges/coverage-badge.svg)](https://github.com/bercianor/mcp-forge-python/actions)
[![Template](https://img.shields.io/badge/template-MCP%20Forge%20Python-blue)](https://github.com/bercianor/mcp-forge-python)
[![Contributors](https://img.shields.io/github/contributors/bercianor/mcp-forge-python)](https://github.com/bercianor/mcp-forge-python/graphs/contributors)
[![Last Commit](https://img.shields.io/github/last-commit/bercianor/mcp-forge-python)](https://github.com/bercianor/mcp-forge-python)

Una plantilla completa y production-ready de servidor MCP (Model Context Protocol) construida con Python, con autenticación OAuth 2.0, validación JWT y opciones de despliegue seamless para desarrolladores creando aplicaciones impulsadas por IA.

## Características Principales de MCP Forge Python

## Implementación del Protocolo MCP

- Construido con la librería `mcp[cli]` de Python para soporte completo del protocolo MCP
- Implementación completa de herramientas, recursos y prompts
- Inicialización configurable del servidor con nombre y versión

## Transportes de Comunicación

- **Transporte Stdio**: Comunicación entrada/salida estándar para clientes IA locales como Claude Desktop
- **HTTP con SSE**: Eventos Server-Sent para comunicación web en tiempo real

## Herramientas MCP Integradas

- **hello_world**: Funcionalidad de saludo personalizado
- **whoami**: Exposición de información de usuario basada en JWT

## Seguridad y Middleware

- **Registro de Acceso**: Logging configurable de requests con redacción de cabeceras
- **Validación JWT**: Estrategias duales para autenticación de tokens
  - Validación local usando JWKS URI y expresiones CEL
  - Delegación a proxy externo (compatible con Istio)

## Integración OAuth 2.0 (RFC 8414 y RFC 9728)

- **Servidor de Autorización OAuth**: Proxy de configuración OpenID Connect
- **Metadata de Recurso Protegido**: Endpoints completos de discovery OAuth

## Configuración Flexible

- Sistema de configuración basado en TOML con secciones dedicadas para:
  - Configuración del servidor (nombre, versión, transporte)
  - Configuración de middleware (logging, JWT)
  - Integración OAuth (servidores de autorización, recursos protegidos)

## Despliegue Production-Ready

- Containerización completa con Dockerfile
- Chart de Kubernetes Helm para despliegue en la nube
- Guías de integración para Keycloak, Istio y Hashrouter

## Requisitos del Sistema

### Dependencias Externas

- **Python**: >= 3.11
- **uv**: Gestor de dependencias y entornos virtuales (instálalo desde [astral.sh/uv](https://astral.sh/uv))
- **just** (opcional): Ejecutor de comandos simplificado (instálalo desde [just.systems](https://just.systems/install.sh))
- **Docker** (opcional): Para construcción de imágenes

#### Requisitos por Estrategia JWT

- **Estrategia "local"**: Requiere un **servidor JWKS** (OAuth provider como Keycloak, Auth0) que proporcione endpoint JWKS para obtener claves públicas y validar tokens. Configúralo en `jwks_uri`.
- **Estrategia "externa"**: Requiere un **proxy upstream** (como Istio, Envoy o gateway API) que valide los JWTs y reenvíe claims en headers. No necesita JWKS en MCP, pero el proxy debe estar configurado para inyectar headers (ej. `X-Forwarded-User`).

### Requerimientos Locales

- **Dependencias de producción**:
  - `fastapi`: Framework web ASGI
  - `uvicorn[standard]`: Servidor ASGI con soporte SSE
  - `pydantic`: Validación de datos
  - `pydantic-settings`: Configuración desde archivos
  - `tomli`: Parser TOML para Python < 3.11
  - `mcp[cli]`: SDK MCP Python
  - `httpx`: Cliente HTTP asíncrono
  - `PyJWT`: Manejo de JWT
  - `requests`: Cliente HTTP síncrono

- **Dependencias de desarrollo**:
  - `ruff`: Linting y formateo
  - `pyright`: Type checking
  - `pytest`: Testing framework
  - `pytest-asyncio`: Soporte async para pytest
  - `coverage`: Cobertura de código

## Instalación y Configuración

```bash
# Instalar dependencias
uv sync

# Instalar paquete (habilita comandos directos)
uv pip install .

# Ejecutar servidor HTTP con SSE
uv run http

# Ejecutar servidor stdio
uv run stdio
```

> **Nota**: Para desarrollo, usa `uv pip install -e .` para instalación editable.

## Comandos para Desarrollo

```bash
# Testing & Calidad
just test                    # Ejecutar todos los tests
just cov                     # Ejecutar tests con reporte de cobertura
just bench                   # Ejecutar benchmarks
just lint                    # Linting y formateo de código
just typing                  # Verificación de tipos
just check-all              # Ejecutar todas las verificaciones de calidad

# Ciclo de Vida
just install                # Instalar/actualizar dependencias
just update                 # Actualizar dependencias a las últimas versiones
just clean                  # Remover todos los archivos temporales (.venv, caches, dist)
just clean-cache            # Limpiar caches únicamente (mantener .venv)
just fresh                  # Limpiar + instalación fresca

# Ejecución
just run                    # Ejecutar servidor HTTP
just run-stdio              # Ejecutar modo stdio
just dev-http               # Ejecutar servidor HTTP con MCP Inspector
just dev-stdio              # Ejecutar servidor stdio con MCP Inspector
```

### Transportes Soportados

- **HTTP + SSE**: Para clientes remotos como Claude Web. Endpoint `/mcp` con SSE. Ejecuta con `uv run http`.
- **Stdio**: Para clientes locales como Claude Desktop. Ejecuta con `uv run stdio`.

## Configuración JWT

El middleware JWT soporta dos estrategias de validación:

### Estrategia "local"

- Valida JWTs directamente en el servidor MCP.
- Descarga claves públicas desde un endpoint JWKS (configurado en `jwks_uri`).
- Soporta cache configurable y condiciones CEL para permisos avanzados.
- **Requisito**: Servidor OAuth con endpoint JWKS (ej. Keycloak).

### Estrategia "externa"

- Delega validación a un proxy upstream (Istio, Envoy, etc.).
- El JWT se reenvía en un header específico (`forwarded_header`).
- El proxy valida y extrae claims, inyectándolos en la request.
- **Requisito**: Proxy configurado para validación JWT y forwarding de headers.

Ejemplo en `config.toml`.

## Configuración

Ver `config.toml` para ejemplo de configuración.

### Configuración Auth

Para flujos OAuth, configura la sección auth:

```toml
[auth]
client_id = "your-client-id"
client_secret = "your-client-secret"
redirect_uri = "http://localhost:8080/callback"
```

### Configuración CORS

Configura Cross-Origin Resource Sharing:

```toml
[middleware.cors]
allow_origins = ["https://yourdomain.com", "http://localhost:3000"]
allow_credentials = true
allow_methods = ["GET", "POST", "PUT", "DELETE"]
allow_headers = ["*"]
```

### Exposición de Claims JWT

Controla qué claims JWT son accesibles para las herramientas MCP:

```toml
# Exponer todos los claims (no recomendado para producción)
jwt_exposed_claims = "all"

# O exponer solo claims específicos
jwt_exposed_claims = ["user_id", "email", "roles"]
```

Nota: Los claims `roles` y `scope` siempre se exponen para propósitos de autorización.

**Nota de seguridad**: Por defecto, el servidor se ejecuta en `127.0.0.1` para evitar exposiciones no deseadas. Configura el host y puerto en `config.toml` bajo `[server.transport.http]`. Cambia a `0.0.0.0` solo si es necesario y con las medidas de seguridad apropiadas.

## Consideraciones de Seguridad

Esta plantilla implementa varias medidas de seguridad para proteger contra vulnerabilidades comunes. Como plantilla, está diseñada para ser configurable para diferentes escenarios de despliegue.

### Exposición de Claims JWT

Para minimizar la exposición de datos, configura qué claims JWT son accesibles en el contexto:

```toml
[context]
jwt_exposed_claims = ["user_id", "roles"]  # Solo exponer claims específicos
# o
jwt_exposed_claims = "all"  # Exponer todos los claims (no recomendado para producción)
```

### Logging de Acceso

Los headers sensibles se redactan automáticamente en los logs:

```toml
[logging]
redacted_headers = ["Authorization", "X-API-Key", "Cookie"]
max_body_size = 1024  # Limitar el tamaño del body logueado
```

### Rate Limiting

Se implementa rate limiting básico para validación JWT para prevenir ataques de fuerza bruta.

### Validación de URIs

Las URIs de OAuth y JWKS se validan contra dominios en whitelist para prevenir ataques SSRF.

### Dependencias Seguras

Las dependencias se actualizan regularmente para abordar vulnerabilidades conocidas. Ejecuta `uv lock --upgrade` para actualizar a las versiones más recientes seguras.

### Lista de Verificación para Producción

- Usar estrategia JWT "external" con un proxy apropiado (Istio, Envoy)
- Configurar claims expuestos mínimos
- Habilitar logging de acceso con redacción
- Validar todas las URIs contra dominios confiables
- Mantener dependencias actualizadas
- Ejecutar tests de seguridad regularmente

### Validación de URIs

Las URIs de OAuth y JWKS se validan contra dominios en whitelist para prevenir ataques SSRF.

### Dependencias Seguras

Las dependencias se actualizan regularmente para abordar vulnerabilidades conocidas. Ejecuta `uv lock --upgrade` para actualizar a las versiones más recientes seguras.

### Lista de Verificación para Producción

- Usar estrategia JWT "external" con un proxy apropiado (Istio, Envoy)
- Configurar claims expuestos mínimos
- Habilitar logging de acceso con redacción
- Validar todas las URIs contra dominios confiables
- Mantener dependencias actualizadas
- Ejecutar tests de seguridad regularmente

## Documentación

- [Documentación Completa](docs/index.md) - Guía completa incluyendo desarrollo, configuración y contribución.
- [Guía de Desarrollo](DEVELOPMENT.md) - Cómo usar esto como plantilla.
- [Contribuyendo](CONTRIBUTING.md) - Guías para contribuidores.

## Arquitectura del Proyecto

```
src/mcp_app/
├── main.py          # Punto de entrada de la aplicación y configuración FastAPI
├── config.py        # Modelos de configuración Pydantic
├── context.py       # Gestión de contexto JWT para compartir claims de forma segura
├── handlers/        # Manejadores de endpoints OAuth (RFC 8414 & RFC 9728)
├── middlewares/     # Middlewares personalizados (JWT, logs de acceso, CORS)
└── tools/           # Herramientas MCP y router de registro
```

### Componentes Core

- **main.py**: Inicializa el servidor FastMCP, aplicación FastAPI, middlewares y endpoints OAuth
- **config.py**: Configuración basada en TOML con modelos Pydantic
- **context.py**: Compartición de contexto JWT async-safe entre middlewares y herramientas
- **handlers/**: Servidor de autorización OAuth y endpoints de metadata de recursos protegidos
- **middlewares/**: Validación JWT, logging de acceso y manejo CORS
- **tools/**: Implementaciones de herramientas MCP y sistema de registro

## Desarrollo

Para instrucciones detalladas de desarrollo, incluyendo cómo usar este proyecto como plantilla para tus propios servidores MCP, consulta [DEVELOPMENT.md](DEVELOPMENT.md).

## Contribuyendo

¡Aceptamos contribuciones! Por favor, consulta [CONTRIBUTING.md](CONTRIBUTING.md) para las guías sobre cómo contribuir a este proyecto.

## Changelog

Consulta [CHANGELOG.md](CHANGELOG.md) para una lista de cambios y releases.

## Licencia

Este proyecto está licenciado bajo Unlicense - consulta el archivo [LICENSE](LICENSE) para más detalles.

## Créditos

Esta es una implementación en Python del proyecto [MCP Forge](https://github.com/achetronic/mcp-forge) (Go), extendida con endpoints adicionales de flujos OAuth e implementaciones específicas de Python manteniendo estándares de seguridad.

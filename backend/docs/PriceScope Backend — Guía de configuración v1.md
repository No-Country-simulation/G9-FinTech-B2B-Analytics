# PriceScope Backend — Guía de configuración v1

Oct 22, 2026 · @Angel

## Objetivo de esta guía

Al terminar, cada backend tiene el proyecto corriendo en su máquina: API en el puerto 8000, base de datos y Redis en Docker, migraciones funcionando y lint y tests en verde. Esta v1 es solo configuración; los modelos y endpoints de negocio llegan en la v2.

Al final vas a poder abrir `http://localhost:8000/health` y ver que la API, PostgreSQL, TimescaleDB y Redis responden.

Convenciones:

- Todos los comandos se ejecutan **desde la carpeta `backend/`**, salvo que se indique otra cosa.
- Donde el comando cambia en Windows, se muestra en un bloque aparte para PowerShell.
- Los archivos marcados como *a mano* se crean en el editor con el contenido exacto que aparece.

## Stack del backend

Esta tabla es la referencia de todo lo que usa el backend. Lo marcado como *Pendiente de ADR* no se instala en esta guía: se agrega cuando el ADR correspondiente esté aprobado.

| Capa | Tecnología | Versión | Para qué la usamos | Estado |
| --- | --- | --- | --- | --- |
| Lenguaje | Python | 3.12 | Lenguaje de todo el backend | Se instala en esta guía |
| Gestión del proyecto | uv | Última estable | Instala Python, crea el entorno virtual y maneja dependencias | Se instala en esta guía |
| Framework web | FastAPI | Última estable | Define los endpoints REST y genera la documentación en `/docs` | Se instala en esta guía |
| Servidor | Uvicorn (`uvicorn[standard]`) | Última estable | Ejecuta la app FastAPI | Se instala en esta guía |
| Validación | Pydantic | Incluida con FastAPI | Valida el JSON que entra y sale de la API | Se instala en esta guía |
| Configuración | pydantic-settings | Última estable | Lee y valida las variables del `.env` | Se instala en esta guía |
| ORM | SQLAlchemy 2 (`sqlalchemy[asyncio]`) | 2.x | Modelos y consultas a la base desde Python | Se instala en esta guía |
| Driver de base | asyncpg | Última estable | Conexión asíncrona a PostgreSQL | Se instala en esta guía |
| Migraciones | Alembic | Última estable | Versiona los cambios del esquema; crea hypertables | Se instala en esta guía |
| Base de datos | PostgreSQL + TimescaleDB | PG 16 · TimescaleDB 2.26.1 | Series temporales de precios y cotizaciones | Se instala en esta guía (Docker) |
| Caché y colas | Redis | 7.4 | Caché del dashboard y broker de tareas | Se instala en esta guía (Docker) |
| Cliente HTTP | httpx | Última estable | Consumir DolarAPI y Bluelytics; tests de la API | Se instala en esta guía |
| Matching de productos | rapidfuzz | Última estable | Similitud de nombres entre tiendas | Se instala en esta guía |
| Contenedores | Docker + Docker Compose | Docker Desktop actual | Levantar base y Redis igual para todo el equipo | Requisito previo |
| Tests | pytest + pytest-asyncio | Última estable | Tests unitarios y de endpoints async | Se instala en esta guía (dev) |
| Lint y formato | Ruff | Última estable | Linter y formateador único del equipo | Se instala en esta guía (dev) |
| Scraping | Playwright o Scrapy | — | Extraer precios de los e-commerce | Pendiente de ADR |
| Tareas programadas | ARQ o Celery + Beat | — | Scrapers diarios e ingesta horaria de cotizaciones | Pendiente de ADR |
| Autenticación | PyJWT + pwdlib (argon2) | — | Login, tokens y hashing de contraseñas | Pendiente de ADR |
| Correo | aiosmtplib o fastapi-mail | — | Correo de bienvenida y recuperación de contraseña | Pendiente de ADR |
| APIs externas | DolarAPI, Bluelytics | — | Cotización oficial y blue con timestamp | Se usan en la v2 (no se instalan) |

Las versiones de las imágenes Docker se fijan a propósito: con `latest` cada persona podría terminar con una versión distinta. Fuente de la versión de TimescaleDB: [Docker Hub](https://hub.docker.com/r/timescale/timescaledb/tags).

## Requisitos previos

Antes del Paso 1, verificá que tengas esto instalado. Python **no** hace falta: lo instala uv.

| Herramienta | Verificación | Nota |
| --- | --- | --- |
| Git | `git --version` | Cualquier versión reciente |
| Docker Desktop | `docker --version` y `docker compose version` | Tiene que estar abierto mientras trabajás |
| Terminal | — | macOS/Linux: Terminal. Windows: PowerShell (no `cmd`) |
| VS Code (o tu editor) | — | Extensiones: **Python** (Microsoft) y **Ruff** (Astral) |

Si ya tenés PostgreSQL o Redis instalados localmente, detenelos o cambiá los puertos en el `.env` del Paso 5: van a chocar con los de Docker (5432 y 6379).

## Paso 1 · Instalar uv

macOS:

```bash
brew install uv
```

Linux (o macOS sin Homebrew):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Windows (PowerShell):

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Cerrá la terminal, abrí una nueva y verificá:

```bash
uv --version
```

Si ya lo tenías instalado, actualizalo con `uv self update` (o `brew upgrade uv`).

## Paso 2 · Crear el proyecto y fijar Python

Desde la raíz del repositorio de PriceScope:

```bash
mkdir backend
cd backend
uv init --app --name pricescope-backend --python 3.12
uv python pin 3.12
```

- `uv init` crea `pyproject.toml`, `.python-version` y `README.md`.
- `uv python pin 3.12` deja `3.12` en `.python-version`. Así todo el equipo usa la misma versión, aunque tenga otra instalada.
- Si `uv init` creó un `main.py` (o `hello.py`) en la raíz de `backend/`, **borralo**: el punto de entrada real va en `app/main.py` (Paso 8).
- Si no estabas dentro de un repositorio, `uv init` también crea `.git/`. Si el backend vive dentro del repo de PriceScope, no debería aparecer.

Abrí `pyproject.toml` y completá la descripción:

```toml
[project]
name = "pricescope-backend"
version = "0.1.0"
description = "API y pipeline de datos de PriceScope"
readme = "README.md"
requires-python = ">=3.12"
dependencies = []
```

## Paso 3 · `.gitignore` antes que cualquier secreto

El `.gitignore` va antes del `.env` para que nunca exista un momento en que las credenciales puedan subirse por accidente.

Creá (o reemplazá) `backend/.gitignore` *a mano*:

```gitignore
# Entorno virtual
.venv/

# Python
__pycache__/
*.pyc

# Herramientas
.pytest_cache/
.ruff_cache/
.coverage
htmlcov/

# Secretos locales
.env

# Sistema operativo y editor
.DS_Store
.vscode/*
!.vscode/extensions.json
```

Qué se sube y qué no:

| Archivo | ¿Se sube a Git? |
| --- | --- |
| `pyproject.toml`, `uv.lock`, `.python-version` | Sí |
| `docker-compose.yml`, `alembic.ini`, `migrations/` | Sí |
| `.env.example` | Sí (sin secretos reales) |
| `.env` | **Nunca** |
| `.venv/` | No (se reconstruye con `uv sync`) |

## Paso 4 · Instalar dependencias

Dependencias de la aplicación (un solo comando; las comillas evitan errores en `zsh`):

```bash
uv add fastapi "uvicorn[standard]" pydantic-settings "sqlalchemy[asyncio]" asyncpg alembic redis httpx rapidfuzz
```

Dependencias de desarrollo (no van a producción):

```bash
uv add --dev pytest pytest-asyncio ruff
```

- `uv add` escribe la librería en `pyproject.toml`, la instala en `.venv/` y fija la versión exacta en `uv.lock`.
- Las de `--dev` quedan en una sección aparte, `[dependency-groups]`.
- No se crea ni se activa ningún `venv` a mano: `uv` maneja `.venv/` y cada comando se ejecuta con `uv run`.

Si el editor marca los imports en rojo, elegí el intérprete del proyecto: paleta de comandos → **Python: Select Interpreter** → `./.venv/bin/python` (Windows: `.venv\Scripts\python.exe`).

## Paso 5 · Variables de entorno: una sola fuente de verdad

El `.env` lo leen **dos** programas: Docker Compose (para crear la base) y la app (para conectarse). Por eso las credenciales se escriben **una sola vez** y la URL de conexión se arma en código, no a mano. Así no pueden quedar desincronizadas.

Creá `backend/.env.example` *a mano* (este sí se sube a Git):

```bash
# --- Aplicación ---
ENVIRONMENT=local

# --- PostgreSQL / TimescaleDB ---
POSTGRES_USER=pricescope
POSTGRES_PASSWORD=cambiar_esta_clave
POSTGRES_DB=pricescope
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# --- Redis ---
REDIS_HOST=localhost
REDIS_PORT=6379
```

Copialo a tu `.env` local (este nunca se sube):

```bash
cp .env.example .env
```

Windows (PowerShell):

```powershell
Copy-Item .env.example .env
```

Reglas:

- Cambiá valores solo en `.env`. Si agregás una variable nueva, agregala también a `.env.example` con un valor de ejemplo.
- `POSTGRES_HOST=localhost` es porque la API corre en tu máquina. Cuando la API se dockerice, ese valor pasará a ser `timescaledb` (el nombre del servicio).
- Si cambiás la contraseña **después** de haber levantado la base por primera vez, la base conserva la anterior. Ver *Errores comunes*.

## Paso 6 · Base de datos y Redis con Docker Compose

No hace falta un `Dockerfile`: usamos imágenes oficiales ya armadas. Docker Compose lee el `.env` de la misma carpeta de forma automática, así que las credenciales salen de ahí.

Creá `backend/docker-compose.yml` *a mano*:

```yaml
name: pricescope

services:
  timescaledb:
    image: timescale/timescaledb:2.26.1-pg16
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
      TIMESCALEDB_TELEMETRY: "off"
    ports:
      - "${POSTGRES_PORT:-5432}:5432"
    volumes:
      - timescale_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $${POSTGRES_USER} -d $${POSTGRES_DB}"]
      interval: 5s
      timeout: 5s
      retries: 10

  redis:
    image: redis:7.4
    ports:
      - "${REDIS_PORT:-6379}:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 10

volumes:
  timescale_data:
  redis_data:
```

Qué hace cada parte:

- **Versiones fijas** (`2.26.1-pg16`, `7.4`): todos tienen exactamente lo mismo. Subir de versión es una decisión del equipo, no un accidente.
- **`${POSTGRES_USER}`**: Compose lo reemplaza con el valor del `.env`. No hay contraseñas escritas en este archivo.
- **`$${...}` en el healthcheck**: el doble `$` hace que la variable la resuelva el contenedor, no Compose.
- **`healthcheck`**: Docker sabe cuándo la base terminó de arrancar, no solo cuándo arrancó el contenedor.
- **Volúmenes**: los datos sobreviven a `docker compose down`. Solo se borran con `down -v`.

Levantá los servicios y verificá que estén sanos:

```bash
docker compose up -d
docker compose ps
```

En la columna `STATUS` ambos tienen que decir `healthy` (puede tardar unos segundos; la primera vez se descargan las imágenes). Prueba rápida:

```bash
docker compose exec timescaledb psql -U pricescope -d pricescope -c "SELECT extversion FROM pg_extension WHERE extname = 'timescaledb';"
docker compose exec redis redis-cli ping
```

Tenés que ver `2.26.1` y `PONG`.

## Paso 7 · Estructura mínima y configuración

En la v1 solo creamos lo necesario para arrancar. Las carpetas de modelos, schemas, endpoints, servicios, workers y scrapers se crean en la v2.

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py          <- Paso 8
│   └── core/
│       ├── __init__.py
│       ├── config.py    <- lee el .env
│       ├── database.py  <- motor de SQLAlchemy y Base de los modelos
│       └── cache.py     <- cliente de Redis
└── tests/
    └── test_app.py      <- Paso 10
```

Crear carpetas y archivos vacíos (macOS / Linux):

```bash
mkdir -p app/core tests
touch app/__init__.py app/main.py app/core/__init__.py app/core/config.py app/core/database.py app/core/cache.py tests/test_app.py
```

Windows (PowerShell):

```powershell
mkdir app/core, tests
New-Item -ItemType File app/__init__.py, app/main.py, app/core/__init__.py, app/core/config.py, app/core/database.py, app/core/cache.py, tests/test_app.py
```

Los `__init__.py` quedan vacíos: marcan cada carpeta como paquete importable (`from app.core.config import settings`).

### `app/core/config.py`

```python
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL

# backend/ (dos niveles arriba de app/core/config.py)
BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "PriceScope API"
    environment: str = "local"

    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    redis_host: str = "localhost"
    redis_port: int = 6379

    @property
    def database_url(self) -> URL:
        return URL.create(
            drivername="postgresql+asyncpg",
            username=self.postgres_user,
            password=self.postgres_password,
            host=self.postgres_host,
            port=self.postgres_port,
            database=self.postgres_db,
        )

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/0"


settings = Settings()
```

Tres decisiones que resuelven problemas reales:

- **`env_file=BASE_DIR / ".env"`**: ruta absoluta. El `.env` se encuentra aunque ejecutes un script desde otra carpeta.
- **`extra="ignore"`**: el `.env` puede tener variables que la app no usa. Sin esto, pydantic-settings falla con *Extra inputs are not permitted*.
- **`URL.create(...)`**: arma la URL de conexión desde las variables. Si la contraseña tiene caracteres como `@` o `#`, se escapan solos.

Si falta una variable obligatoria, la app no arranca y el error dice cuál falta.

### `app/core/database.py`

```python
from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

engine = create_async_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    """Clase base de todos los modelos (se usan en la v2)."""


async def get_session() -> AsyncIterator[AsyncSession]:
    """Dependencia de FastAPI: abre una sesión por request y la cierra al terminar."""
    async with SessionLocal() as session:
        yield session
```

- `engine` es el pool de conexiones; se crea una sola vez para toda la app.
- `Base` es la clase de la que van a heredar todos los modelos. Alembic la usa para detectar cambios.
- `get_session` se inyecta en los endpoints de la v2 con `Depends(get_session)`.

### `app/core/cache.py`

```python
from redis.asyncio import Redis

from app.core.config import settings

redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
```

Se llama `cache.py` y no `redis.py` a propósito: un archivo con el mismo nombre que una librería genera confusión al leer los imports.

## Paso 8 · Punto de entrada y endpoint `/health`

En vez de un «Hola Mundo», el primer endpoint es un chequeo de salud: confirma que la API, la base, TimescaleDB y Redis están conectados. Es el mismo endpoint que después usará el despliegue para saber si el servicio está vivo.

### `app/main.py`

```python
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.core.cache import redis_client
from app.core.config import settings
from app.core.database import engine


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Arranque: acá irá lo que deba ejecutarse al iniciar la app.
    yield
    # Apagado: cerramos las conexiones de forma ordenada.
    await redis_client.aclose()
    await engine.dispose()


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)


@app.get("/health", tags=["sistema"])
async def health() -> JSONResponse:
    checks: dict[str, str] = {}

    try:
        async with engine.connect() as conn:
            version = await conn.scalar(
                text("SELECT extversion FROM pg_extension WHERE extname = 'timescaledb'")
            )
        checks["database"] = "ok"
        checks["timescaledb"] = version or "no instalada"
    except Exception as exc:
        checks["database"] = f"error: {exc.__class__.__name__}"

    try:
        await redis_client.ping()
        checks["redis"] = "ok"
    except Exception as exc:
        checks["redis"] = f"error: {exc.__class__.__name__}"

    healthy = checks.get("database") == "ok" and checks.get("redis") == "ok"
    return JSONResponse(
        status_code=status.HTTP_200_OK if healthy else status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "status": "ok" if healthy else "degraded",
            "environment": settings.environment,
            **checks,
        },
    )
```

- **`lifespan`**: código que corre al arrancar y al apagar la app. Hoy solo cierra conexiones; en la v2 puede precargar datos.
- **Responde 503 si algo falla**, no 200 con un error adentro. Así un monitor o el despliegue lo detecta sin leer el JSON.

### Levantar la API

```bash
uv run uvicorn app.main:app --reload --port 8000
```

- `app.main:app` significa: carpeta `app/`, archivo `main.py`, variable `app`.
- `--reload` reinicia el servidor al guardar un archivo. Solo para desarrollo.
- Se detiene con `Ctrl+C`.

Abrí en el navegador:

- `http://localhost:8000/health`: tiene que devolver `"status": "ok"`.
- `http://localhost:8000/docs`: documentación interactiva (Swagger), generada sola.

Respuesta esperada de `/health`:

```json
{"status": "ok", "environment": "local", "database": "ok", "timescaledb": "2.26.1", "redis": "ok"}
```

## Paso 9 · Migraciones con Alembic

SQLAlchemy define las tablas, pero no cambia el esquema de una base existente. Alembic guarda cada cambio como un archivo versionado en Git, y cada persona aplica los mismos cambios en el mismo orden con un solo comando. Con tres backends tocando el esquema, es lo que evita que las bases locales diverjan.

> **Quién hace este paso:** la configuración inicial de Alembic (9.1 a 9.4) la hace **una sola persona** y la sube a Git. El resto solo ejecuta `uv run alembic upgrade head` (9.5).

### 9.1 · Inicializar con la plantilla async

```bash
uv run alembic init -t async migrations
```

Crea `alembic.ini` y la carpeta `migrations/` (con `env.py` y `versions/`).

### 9.2 · Ajustar `alembic.ini`

Abrí `alembic.ini` y cambiá dos líneas:

1. Buscá `sqlalchemy.url` y dejala vacía. La URL sale del `.env`, nunca de este archivo (que se sube a Git):

   ```ini
   sqlalchemy.url =
   ```
2. Buscá la línea comentada `# file_template = ...` y reemplazala por esta, para que las migraciones queden ordenadas por fecha:

   ```ini
   file_template = %%(year)d%%(month).2d%%(day).2d_%%(hour).2d%%(minute).2d-%%(rev)s_%%(slug)s
   ```

Dejá `prepend_sys_path = .` como está: es lo que permite que Alembic importe `app`.

### 9.3 · Reemplazar `migrations/env.py`

Borrá todo el contenido generado y pegá este:

```python
import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings
from app.core.database import Base

# v2: importar los modelos acá para que Alembic los detecte, por ejemplo:
# from app import models  # noqa: F401

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Genera el SQL sin conectarse a la base (alembic upgrade --sql)."""
    context.configure(
        url=settings.database_url.render_as_string(hide_password=False),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = create_async_engine(settings.database_url, poolclass=pool.NullPool)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

Qué cambia respecto del generado: la URL se toma de `settings` (no de `alembic.ini`), `target_metadata` apunta a `Base.metadata` y `compare_type=True` hace que Alembic detecte cambios de tipo de columna.

### 9.4 · Primera migración: habilitar TimescaleDB

```bash
uv run alembic revision -m "habilitar timescaledb"
```

Abrí el archivo nuevo en `migrations/versions/` y completá las dos funciones:

```python
def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb")


def downgrade() -> None:
    # No se elimina la extensión: borraría todas las hypertables.
    pass
```

La imagen de TimescaleDB ya suele traer la extensión creada; la migración garantiza que exista en cualquier base (local, staging o producción) y deja registrado que el proyecto depende de ella. En la v2, las hypertables de precios y cotizaciones se crean igual: con `op.execute("SELECT create_hypertable(...)")` dentro de una migración.

### 9.5 · Aplicar las migraciones

```bash
uv run alembic upgrade head
uv run alembic current
```

`current` tiene que mostrar el id de la migración seguido de `(head)`.

Comandos que vas a usar seguido:

| Quiero... | Comando |
| --- | --- |
| Aplicar todo lo pendiente | `uv run alembic upgrade head` |
| Crear una migración vacía | `uv run alembic revision -m "descripcion"` |
| Generarla desde los modelos (v2) | `uv run alembic revision --autogenerate -m "descripcion"` |
| Volver una migración atrás | `uv run alembic downgrade -1` |
| Ver el historial | `uv run alembic history` |

Reglas del equipo:

- Toda migración autogenerada **se revisa a mano** antes de commitearla: Alembic no detecta todo (por ejemplo, hypertables o índices especiales).
- Nunca se edita una migración que ya está en `main`. Se crea una nueva.
- Si dos personas crean migraciones en paralelo y aparecen dos *heads*, se resuelve con `uv run alembic merge heads -m "merge"`.

## Paso 10 · Calidad: Ruff y pytest

Ruff es el linter y formateador del equipo: todos formatean igual y los Code Reviews se enfocan en la lógica, no en el estilo. pytest corre los tests que después van a ampliar Bruno y Larisa desde QA.

### 10.1 · Configuración en `pyproject.toml`

Agregá al final de `pyproject.toml`:

```toml
[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
# E/F: errores básicos · I: orden de imports · B: bugs comunes · UP: sintaxis moderna
select = ["E", "F", "I", "B", "UP"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
markers = [
    "integracion: requiere Docker (base de datos y Redis) levantado",
]
```

- `asyncio_mode = "auto"`: los tests `async def` corren sin decorador extra.
- `pythonpath = ["."]`: los tests pueden hacer `from app.main import app`.
- El marcador `integracion` separa los tests que necesitan Docker de los que no.

### 10.2 · Primer test: `tests/test_app.py`

```python
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


async def test_documentacion_disponible() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/openapi.json")

    assert response.status_code == 200
    assert response.json()["info"]["title"] == "PriceScope API"


@pytest.mark.integracion
async def test_health_con_servicios_levantados() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
```

`ASGITransport` llama a la app directamente, sin levantar Uvicorn: los tests son rápidos y no ocupan el puerto 8000.

### 10.3 · Ejecutar

```bash
uv run ruff format .          # formatea
uv run ruff check . --fix     # lint y corrige lo automático
uv run pytest                 # todos los tests (Docker levantado)
uv run pytest -m "not integracion"   # solo los que no necesitan Docker
```

Con la extensión de Ruff en VS Code, conviene activar *Format on Save* para no tener que acordarse del comando. Antes de abrir un Pull Request, `ruff check` y `pytest` tienen que pasar sin errores.

## Paso 11 · Verificación final y primer commit

Estructura que tiene que quedar en `backend/`:

```
backend/
├── .env                 <- local, no se sube
├── .env.example
├── .gitignore
├── .python-version
├── README.md
├── alembic.ini
├── docker-compose.yml
├── pyproject.toml
├── uv.lock
├── .venv/               <- local, no se sube
├── app/
│   ├── __init__.py
│   ├── main.py
│   └── core/
│       ├── __init__.py
│       ├── cache.py
│       ├── config.py
│       └── database.py
├── migrations/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── <fecha>-<id>_habilitar_timescaledb.py
└── tests/
    └── test_app.py
```

Checklist (todo tiene que dar OK):

- [ ] `uv run python --version` muestra Python 3.12
- [ ] `docker compose ps` muestra `timescaledb` y `redis` como `healthy`
- [ ] `uv run alembic current` muestra la migración con `(head)`
- [ ] `http://localhost:8000/health` devuelve `"status": "ok"` con `timescaledb: 2.26.1`
- [ ] `http://localhost:8000/docs` abre Swagger
- [ ] `uv run ruff check .` termina sin errores
- [ ] `uv run pytest` pasa los 2 tests
- [ ] `git status` **no** muestra `.env` ni `.venv/`

Primer commit (lo hace quien armó la base; el resto clona):

```bash
git checkout -b feature/backend-setup
git add .
git status        # revisá que no aparezca .env
git commit -m "PSB2BA-XXX: configuración inicial del backend"
git push -u origin feature/backend-setup
```

Reemplazá `PSB2BA-XXX` por la clave del ticket de Jira correspondiente y abrí el Pull Request para Code Review.

## Rutina diaria y chuleta

### Primera vez (cuando clonás el repo ya configurado)

```bash
git clone <url-del-repositorio>
cd <repo>/backend
uv sync                      # crea .venv/ con las versiones exactas de uv.lock
cp .env.example .env         # Windows: Copy-Item .env.example .env
docker compose up -d
uv run alembic upgrade head
uv run pytest
```

### Cada día

```bash
git pull
uv sync                      # por si alguien agregó una librería
docker compose up -d
uv run alembic upgrade head  # por si alguien agregó una migración
uv run uvicorn app.main:app --reload --port 8000
```

Al terminar: `Ctrl+C` para la API y `docker compose stop` para apagar la base y Redis (los datos se conservan).

### Chuleta

| Quiero... | Comando |
| --- | --- |
| Instalar todo lo del proyecto | `uv sync` |
| Agregar una librería | `uv add nombre` |
| Agregar una librería de desarrollo | `uv add --dev nombre` |
| Quitar una librería | `uv remove nombre` |
| Ver el árbol de dependencias | `uv tree` |
| Levantar la API | `uv run uvicorn app.main:app --reload --port 8000` |
| Levantar base y Redis | `docker compose up -d` |
| Ver estado de los contenedores | `docker compose ps` |
| Ver logs de la base | `docker compose logs -f timescaledb` |
| Abrir una consola SQL | `docker compose exec timescaledb psql -U pricescope -d pricescope` |
| Apagar sin borrar datos | `docker compose stop` |
| Borrar todo, datos incluidos | `docker compose down -v` |
| Aplicar migraciones | `uv run alembic upgrade head` |
| Formatear y revisar | `uv run ruff format .` y `uv run ruff check . --fix` |
| Correr los tests | `uv run pytest` |

## Errores comunes

| Síntoma | Causa | Solución |
| --- | --- | --- |
| `command not found: uv` | La terminal no recargó el `PATH` | Abrí una terminal nueva. En macOS/Linux: `source $HOME/.local/bin/env` |
| `zsh: no matches found: uvicorn[standard]` | `zsh` interpreta los corchetes | Poné el paquete entre comillas: `"uvicorn[standard]"` |
| `No pyproject.toml found` | Estás fuera de `backend/` | `cd backend` |
| `ModuleNotFoundError: No module named 'app'` | Ejecutás desde otra carpeta | Ejecutá desde `backend/` con `uv run ...` |
| `ValidationError ... Field required` al arrancar | Falta el `.env` o una variable | `cp .env.example .env` y revisá que estén todas |
| `Extra inputs are not permitted` | Falta `extra="ignore"` en `config.py` | Copiá la configuración del Paso 7 tal cual |
| `Cannot connect to the Docker daemon` | Docker Desktop cerrado | Abrilo y esperá a que termine de iniciar |
| `port is already allocated` al levantar Docker | Otro Postgres o Redis usa el puerto | Detenelo, o cambiá `POSTGRES_PORT` / `REDIS_PORT` en el `.env` |
| `password authentication failed` | Cambiaste la contraseña después de crear el volumen | Si la base no tiene datos importantes: `docker compose down -v` y `docker compose up -d` |
| `/health` devuelve 503 | Docker apagado o servicio no `healthy` | `docker compose ps` y `docker compose logs timescaledb` |
| `timescaledb: "no instalada"` en `/health` | Falta aplicar la migración | `uv run alembic upgrade head` |
| Alembic: `Multiple head revisions are present` | Dos migraciones creadas en paralelo | `uv run alembic merge heads -m "merge"` |
| Imports en rojo en el editor | El editor no usa `.venv` | *Python: Select Interpreter* → `.venv` |
| `Address already in use` en el puerto 8000 | Quedó otra instancia de Uvicorn | Cerrala o usá `--port 8001` |

## Decisiones tomadas y qué viene en la v2

Estas decisiones quedaron tomadas el 22/10/2026. Se instalan y se usan en la guía v2:

| Tema | Decisión | Motivo | Cuándo se instala |
| --- | --- | --- | --- |
| Scraping | Playwright si la tienda renderiza con JavaScript; Scrapy si el HTML es estático | Se elige por tienda, según cómo esté hecha | Con la épica de extracción |
| Tareas programadas | ARQ | Async nativo, más liviano; usa el Redis que ya tenemos | v2 (`uv add arq`) |
| Autenticación | PyJWT para tokens y pwdlib con argon2 para contraseñas | passlib está poco mantenido | v2 (`uv add pyjwt "pwdlib[argon2]"`) |
| Correo | aiosmtplib | Async y sin dependencias extra | v2 (`uv add aiosmtplib`) |

La **v2** retoma desde el estado en que deja esta guía y cubre:

- Estructura completa: `models/`, `schemas/`, `api/v1/`, `services/`, `workers/` y `scrapers/`.
- Modelos de tiendas, productos canónicos, publicaciones, precios y cotizaciones, con sus hypertables.
- Primeros endpoints del backoffice (UX11) y de solicitudes de demo (UX02).
- Ingesta de cotizaciones desde DolarAPI y Bluelytics.
- Dockerizar la API (servicio `api` en `docker-compose.yml`).

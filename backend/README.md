# PriceScope — Backend

Todos los comandos se ejecutan desde la carpeta `backend/`.

## Requisitos

- [Docker](https://www.docker.com/) (con `docker compose`)
- [uv](https://docs.astral.sh/uv/getting-started/installation/) para manejar Python y las dependencias (Python 3.12 o superior)

## 1. Crear el `.env`

Mac / Linux:

```bash
cp .env.example .env
```

Windows (PowerShell):

```powershell
copy .env.example .env
```

Abre el `.env` y complétalo con los mismos campos que tiene `.env.example`
(como mínimo `POSTGRES_PASSWORD` y `JWT_SECRET`).

## 2. Levantar los servicios de Docker

```bash
docker compose up -d
```

Esto levanta:

| Servicio     | Puerto local | Uso                                     |
|--------------|--------------|-----------------------------------------|
| TimescaleDB  | 5432         | Base de datos (PostgreSQL 16 + Timescale) |
| Redis        | 6379         | Cola de trabajos (ARQ) y caché          |
| Mailpit      | 8025         | Bandeja de entrada de correos de prueba (http://localhost:8025) |

## 3. Instalar las dependencias

```bash
uv sync
```

## 4. Aplicar las migraciones

Crea las tablas y la extensión de TimescaleDB:

```bash
uv run alembic upgrade head
```

## 5. Crear el administrador y el catálogo de tiendas

```bash
uv run python -m scripts.seed
```

El script pide el email, nombre y contraseña del administrador. Para no ser interactivo, puedes
definir `SEED_ADMIN_EMAIL`, `SEED_ADMIN_NAME` y `SEED_ADMIN_PASSWORD` antes de ejecutarlo.
Es seguro correrlo más de una vez.

## 6. Levantar la API

```bash
uv run uvicorn app.main:app --reload
```

- Documentación interactiva: http://localhost:8000/docs
- Estado del sistema (base de datos y Redis): http://localhost:8000/health

## 7. Levantar el worker

En otra terminal:

```bash
uv run arq app.workers.tasks.WorkerSettings
```

El worker envía los correos (que aparecen en Mailpit: http://localhost:8025) y ejecuta la ingesta de
cotizaciones cada hora. Sin él, la API responde bien pero las tareas quedan encoladas en Redis y no
se procesan: ningún correo (alta de usuario, reenvío de acceso, restablecer contraseña) llega a
Mailpit. Al levantarlo, procesa lo que haya quedado en la cola.

## Día a día

Con los servicios de Docker arriba (`docker compose up -d`), dos terminales en `backend/`:

```bash
uv run uvicorn app.main:app --reload         # API
uv run arq app.workers.tasks.WorkerSettings  # worker de correos
```

## Tests

Los tests usan una base aparte llamada `pricescope_test`. Créala una sola vez (con los servicios de Docker arriba):

```bash
docker exec pricescope-timescaledb-1 psql -U pricescope -d pricescope -c "CREATE DATABASE pricescope_test"
```

Luego:

```bash
uv run pytest -q
```

Si tu `POSTGRES_USER` o el nombre del contenedor son distintos, ajusta el comando de `docker exec`.

# PriceScope — Backend

Todos los comandos se ejecutan desde la carpeta `backend/`.

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

## 2. Levantar Docker

```bash
docker compose up -d
```

## 3. Crear la base de datos de tests

```bash
docker exec pricescope-timescaledb-1 psql -U pricescope -d pricescope -c "CREATE DATABASE pricescope_test"
```

## 4. Correr los tests

```bash
uv run pytest -q
```

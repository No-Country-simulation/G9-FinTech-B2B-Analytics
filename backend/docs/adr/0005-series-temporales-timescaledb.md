# ADR-0005: Series temporales en TimescaleDB

- Estado: Aceptado
- Fecha: 2026-10-28
- Ticket: Spike: series temporales en TimescaleDB

## Contexto
Hay que guardar el historial de precios y cotizaciones y consultarlo por rango de fechas.

## Decisión
`cotizaciones` y `precios` son hypertables particionadas por su columna de tiempo (`cotizado_en`, `capturado_en`).
- La PK incluye la columna de tiempo (requisito de TimescaleDB).
- `create_hypertable` se ejecuta a mano en la migración: Alembic autogenerate no lo hace.
- `precios` guarda un snapshot de la cotización oficial y blue vigente y los precios en USD de ambas, sin FK a `cotizaciones`: no se puede apuntar con FK hacia una hypertable.
- Regla de promoción: hay promo si el precio tachado supera al actual. El regular es el tachado, o el actual si no hay promo; nunca se completa con una observación anterior. Sin precio actual no se guarda la observación.

## Consecuencias
- Los tests crean las tablas con `create_all`, así que en test son tablas normales y no se prueba el comportamiento de hypertable.
- Guardar el USD de ambas cotizaciones agrega columnas, pero evita convertir al consultar.
- Riesgo: si cambia la regla de promoción, el historial ya guardado no se recalcula.
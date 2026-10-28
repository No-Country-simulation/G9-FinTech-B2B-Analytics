# ADR-0004: Fuente de cotizaciones

- Estado: Aceptado
- Fecha: 2026-10-28
- Ticket: Spike: API de divisas

## Contexto
Hace falta la cotización oficial y la blue cada hora, con timestamp, para convertir precios a USD.

## Opciones evaluadas
1. DolarAPI: un endpoint por tipo, sin clave, con `fechaActualizacion`.
2. Bluelytics: un JSON con oficial y blue y un único `last_update`, sin clave.
3. Open Exchange Rates: requiere clave y no informa la cotización blue.

## Decisión
DolarAPI como fuente principal y Bluelytics como respaldo. Open Exchange Rates queda descartada por no cubrir blue.

## Consecuencias
- Cada ingesta guarda oficial y blue con el mismo `cotizado_en` (cuándo consultamos) y la fecha de la fuente aparte (`fecha_fuente`).
- Si ninguna fuente responde, no se guarda nada y se registra el error: quien consuma usa la última fila y mide su antigüedad con `cotizado_en`.
- Riesgo: ambas son APIs públicas sin garantía de disponibilidad.
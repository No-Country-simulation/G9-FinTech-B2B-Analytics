# PriceScope — Monitor de Inflación Real Multimoneda

**FinTech / Inteligencia de Mercado (B2B Analytics) · Tablero de Inflación Real vs Divisa**

Sistema de monitoreo continuo de precios para una firma de analítica económica que provee informes
a cadenas minoristas, fondos de inversión y medios en mercados de alta volatilidad cambiaria.
Reemplaza el relevamiento manual (15 portales, 2 veces por semana, +10.000 productos) con scrapers
programados, ingesta de cotizaciones y un dashboard ejecutivo de actualización diaria.

## Problema

- Recolección manual de precios en e-commerce → retrasos de días y errores de tipeo.
- Conversión manual al tipo de cambio del día (oficial y paralelo) → pérdida de trazabilidad.
- Ofertas temporales y reduflación sin control → distorsionan la tasa de inflación.

## Arquitectura

```
Scrappers (Playwright/Scrapy)  ──►  Normalización  ──►  PostgreSQL + TimescaleDB  ──►  Dashboard
APIs de Divisas (horario)       ──►  Motor de FX     ──►  Series temporales         ──►  Alertas
```

| Componente | Descripción |
|---|---|
| **Pipeline de extracción** | Jobs diarios sobre 2–3 e-commerces: nombre, precio actual, precio tachado, disponibilidad y categoría |
| **Motor Divisas** | Ingesta horaria vía API (DolarAPI, Open Exchange Rates, Bluelytics) de cotización oficial y paralela/blue con timestamp |
| **Normalización** | Mapeo a producto canónico, detección de promo, precio regular vs. promo y alerta de reduflación si cambia el gramaje |
| **Series temporales** | Tabla `prices` con FK a producto canónico, tienda, `timestamp`, `precio_local`, `tipo_cambio_usado`, `precio_usd` |
| **Indicadores** | Inflación acumulada por categoría, variación % vs. devaluación, detección de picos y spread entre tiendas |
| **Dashboard** | Gráficos de líneas y dispersión: precios en moneda local vs. extranjera, índice inflación por categoría, filtros por período/tienda/categoría/moneda |
| **Alertas** | Productos cuyo aumento supera la tasa de devaluación en un período, hitos CyberWeek |

## Decisiones de diseño

1. **Identidad de productos**: modelo de *producto canónico* con alias por tienda (SKU, nombre normalizado,
   categoría) para comparar el mismo modelo entre competidores.
2. **Promos y reduflación**: flag de promoción + precio regular desagregados; el índice de inflación se
   calcula sobre precio regular, y el precio promocional se registra por separado. El cambio de gramaje/contenido
   neto dispara una alerta de reduflación en lugar de registrar una variación de precio.
3. **Sincronización cambiaria**: cada captura guarda su `timestamp` y el tipo de cambio de la vía más
   cercana a ese instante, garantizando un `precio_usd` reproducible aún con volatilidad intradía.

## Stack

- **Scraping / Pipeline**: Python (Playwright, Scrapy, BeautifulSoup) o Node.js (Puppeteer, Crawlee) + Celery / BullMQ
- **Backend**: FastAPI / Django o Express / NestJS
- **Base de datos**: PostgreSQL + TimescaleDB (series temporales)
- **Frontend**: React / Next.js / Vue con Chart.js, Recharts o Tremor
- **Divisas**: DolarAPI, Open Exchange Rates, Bluelytics


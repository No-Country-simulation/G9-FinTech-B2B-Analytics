# ADR-0006: Tiendas a extraer

- Estado: Aceptado
- Fecha: 2026-10-29
- Ticket: Spike: tiendas a extraer (E08)

## Contexto
Hay que elegir las 2-3 tiendas del MVP. El criterio principal es poder comparar el mismo producto entre tiendas (matriz de precios y spread), con acceso estable y bajo costo de mantenimiento. El proyecto es educativo.

## Cómo se evaluó
Sondeo con `scripts/probe_vtex.py` contra Jumbo, Carrefour, Frávega y Cetrogar, desde una IP de Argentina: 7 búsquedas por tienda (leche, yerba mate, aceite, arroz, fideos, heladera, televisor) de 50 productos cada una, lectura de `robots.txt` y una prueba de carga de 30 requests a 1 por segundo.

| Tienda | Plataforma | Acceso | robots.txt | Carga 30 req a 1/s | Relación precio de lista / precio | EAN | Vendedores |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Jumbo | VTEX | JSON público | Sin `Disallow` sobre api o catalog | 30 respuestas OK, sin 403 ni 429 | Placeholder: mediana 82,6, máximo 100 | Sí (350 distintos) | Propio |
| Carrefour | VTEX | JSON público | Sin `Disallow` sobre api o catalog | 30 respuestas OK | Mediana 1,23, p90 1,52, máximo 2,0 | Sí (344 distintos) | Mayormente propio; apareció un tercero (Newsan) |
| Frávega | VTEX | JSON público | Sin `Disallow` sobre api o catalog | 30 respuestas OK | Mediana 1,33, p90 1,82, máximo 2,9 | Pocos (108 distintos) | Marketplace: Glic, nocnoc, etc. |
| Cetrogar | VTEX | JSON público | **`Disallow: /api/`** | 30 respuestas OK | Mediana 1,11, máximo 1,6 | Sí (153 distintos) | Propio |

Solapamiento de EAN entre tiendas: Jumbo y Carrefour comparten 89 EAN sobre unos 350 por tienda. Frávega y Cetrogar comparten 4.

Limitaciones del sondeo: muestra chica, hecha desde una IP argentina. El filtro de `robots.txt` del script imprimió solo líneas con `api`, `catalog`, `crawl-delay`, `user-agent` o `sitemap`, así que otras reglas pueden existir.

## Términos de uso
Revisados a mano por el equipo. Jumbo tiene una cláusula de propiedad intelectual que limita el uso de la información del sitio a fines privados y no comerciales y prohíbe copiar, reproducir o explotar sus contenidos y bases de datos sin autorización. En las otras tres el equipo no encontró una prohibición explícita de acceso automatizado, pero la revisión fue manual y puede tener omisiones.

## Decisión
1. **Carrefour y Jumbo** son las tiendas del MVP. Son el único par con solapamiento comprobado y con vendedor propio. Ambas van con rubro `supermarket`.
2. **Acceso por el catálogo JSON de VTEX** (`/api/catalog_system/pub/products/search`) con `httpx`. No hace falta Playwright.
3. **Cetrogar queda descartada por ahora**: su `robots.txt` prohíbe `/api/`, que es la vía elegida.
4. **Frávega y Disco quedan de reserva.** Frávega es un marketplace con EAN escasos; Disco no se sondeó.
5. El equipo decide continuar con las tiendas elegidas, con carácter educativo y aceptando el riesgo de los términos de Jumbo.

Condiciones de operación para los scrapers: solo datos públicos y sin login, una corrida diaria por tienda, no más de 1 request por segundo, `User-Agent` identificable y sin redistribuir los datos fuera del proyecto. Si surge un reclamo, se reemplaza la tienda afectada por una de reserva.

## Consecuencias
- **Precio tachado de Jumbo inutilizable.** Su `ListPrice` es un valor ficticio (82,6 veces el precio en casi todos los productos). `record_observation` descarta un tachado mayor a 3 veces el precio actual (`MAX_STRIKETHROUGH_RATIO`). Resultado: en Jumbo no se detectan promociones por precio tachado. Hay que revisar si `PriceWithoutDiscount` o `Teasers` de la oferta sirven como alternativa.
- **Precio 0:** hay SKUs sin precio vigente (precio 0 y stock 0). Ya se descartan al registrar la observación.
- **Paginación:** VTEX corta en unos 2.550 productos por búsqueda (`_from` máximo 2500). Para catálogos completos hay que recorrer el árbol de categorías (`/api/catalog_system/pub/category/tree/3` y el filtro `fq=C:`).
- **Respuesta 206:** VTEX responde 206 al paginar. Los scrapers deben aceptar 200 y 206.
- **Vendedores:** puede haber ofertas de terceros incluso en Carrefour. El scraper debe quedarse con el vendedor propio de la tienda.
- **EAN:** conviene normalizarlo a 14 dígitos con ceros a la izquierda (Carrefour devuelve `07796962006527`, otras tiendas no usan el cero). Para la épica 09, el EAN permite resolver el producto canónico en muchos casos sin comparar nombres.
- **Riesgos:** términos de uso de Jumbo; un endpoint que es el del propio front pero no un contrato firmado; no verificado desde un servidor fuera de Argentina; muestra chica.
- Historias afectadas: Scrapers de 2-3 e-commerces (HTTP/JSON en vez de navegador) y Extracción diaria programada (2 tiendas). El esquema de `stores` no cambia.
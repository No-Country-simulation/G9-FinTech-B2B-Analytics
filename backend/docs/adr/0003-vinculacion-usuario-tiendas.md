# ADR-0003: Vinculación usuario – tiendas – scrapers

- Estado: Aceptado
- Fecha: 2026-10-27
- Ticket: PSB2BA-521

## Contexto
Cada cliente ve solo las tiendas que se le asignan. Una tienda se scrapea una sola vez aunque la vean varios clientes.

## Decisión
Relación muchos a muchos `usuario_tienda` (PK compuesta `usuario_id`, `tienda_id`). Tienda ↔ scraper 1 a 1 por `tiendas.scraper_clave` (el scraper es código, sin tabla). Toda consulta de precios filtra con `ids_tiendas_visibles(usuario)`; un admin ve todas. No se asignan tiendas a admins (400). Deshacer una vinculación borra la fila y no toca los precios. Esquema completo en `docs/pricescope-db-tablas.md`.

## Consecuencias
Un cliente sin tiendas recibe listas vacías. Borrar una tienda con vínculos está bloqueado (`ON DELETE RESTRICT`); se desactiva con `activa = false`.

# ADR-0002: Modelo de roles

- Estado: Aceptado
- Fecha: 2026-10-27
- Ticket: PSB2BA-285

## Contexto
El MVP distingue visitante (sin cuenta), cliente y administrador. Nadie se registra solo.

## Opciones evaluadas
1. Tabla de roles y permisos granulares: flexible, innecesario para el MVP.
2. Columna `usuarios.rol` con dos valores: simple.

## Decisión
Opción 2: `cliente` y `admin` en `usuarios.rol` (VARCHAR + CHECK). Estado del usuario: `pendiente`, `activo`, `bloqueado`, `baja`. Solo un usuario `activo` inicia sesión. Protección con las dependencias `UsuarioActual` y `AdminActual` (401 sin sesión, 403 sin permiso).

## Consecuencias
Si aparecen permisos más finos habrá que migrar a una tabla de permisos. Agregar un valor al CHECK requiere una migración.

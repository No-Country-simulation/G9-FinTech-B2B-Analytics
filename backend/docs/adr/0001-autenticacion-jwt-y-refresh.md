# ADR-0001: Autenticación con JWT de acceso corto y refresh token en base

- Estado: Aceptado
- Fecha: 2026-10-27
- Ticket: PSB2BA-286

## Contexto
Hace falta login con cierre de sesión real y expiración por inactividad (PSB2BA-325). El frontend es una SPA separada de la API.

## Opciones evaluadas
1. Sesión por cookie (servidor guarda todo): simple, pero cada request consulta la base y complica CORS con la SPA.
2. Solo JWT largo sin estado: no se puede cerrar sesión ni revocar.
3. JWT corto + refresh opaco guardado en base: costo de una consulta por request protegido, pero permite revocar.

## Decisión
Opción 3. JWT de 15 min (`sub`, `rol`, `sid`) en el header `Authorization`; refresh token aleatorio en cookie `httpOnly` (`ps_refresh`), guardado como SHA-256 en `sesiones` y rotado en cada renovación. Inactividad: 30 min. Duración máxima: 12 h. Librerías: PyJWT y pwdlib (argon2).

## Consecuencias
Cerrar sesión o bloquear a un usuario surte efecto en el siguiente request. El frontend debe renovar con `/auth/refresh` solo si hubo actividad y enviar `credentials: "include"`.

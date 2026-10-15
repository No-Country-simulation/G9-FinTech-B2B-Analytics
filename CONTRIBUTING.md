# Cómo contribuir al proyecto

## Regla principal

**Nadie hace push directo a `main`.** Todo cambio entra mediante Pull Request.

## Flujo

```bash
# 1. Actualizarte desde main (pull)
git checkout main
git pull origin main

# 2. Crear tu rama
git checkout -b tipo/nombre-corto

# 3. Trabajar y commitear con mensajes claros
git add .
git commit -m "feat: agregar gráfico de inflación por categoría"

# 4. Subir tu rama (push)
git push origin tipo/nombre-corto

# 5. Abrir PR contra main y completar la plantilla
```

## Tipos de rama

| Tipo | Para qué |
|---|---|
| `feature/` | Nueva funcionalidad |
| `fix/` | Corrección de bugs |
| `data/` | Migraciones, seeds, scrapers |
| `chore/` | Tareas: configs, dependencias, refactor |
| `docs/` | Documentación |

Ejemplos: `feature/dashboard-graficos`, `fix/filtro-fechas`, `data/migracion-precios`.

## Reglas de PR

1. Completar la plantilla (qué se hizo, qué cambió, cómo probarlo).
2. El título del PR sigue el mismo estilo de los commits: `tipo: descripción`.
3. Mencionar la issue si existe (`Closes #12`).
4. Si el cambio es grande, avisar al equipo antes de abrir el PR.

## Sobre fechas y versiones

No hace falta anotar horarios a mano: GitHub guarda fecha/hora en cada commit y PR.
Para saber qué es más nuevo, siempre mirar el historial del PR o `git log`.

## Merge

- Solo un maintainer aprueba y hace squash-merge en `main`.
- Después del merge, borrar la rama.
- Todos hacen `git pull origin main` antes de seguir trabajando.

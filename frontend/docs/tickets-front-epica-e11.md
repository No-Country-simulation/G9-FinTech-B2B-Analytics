# Tickets [FRONT] · E11 · Panel de administración v1

Épica: [PSB2BA-278 · E11 · Panel de administración v1](https://pricescope-b2b-analytics-s10-26-g9.atlassian.net/browse/PSB2BA-278)

Prototipo de referencia: [PriceScope · Prototipo de pantallas](https://claude.ai/artifact/R5gtqkAMK2T9ckYYJTgUyK) (Claude Design).

**El prototipo es un ejemplo de contenido y estructura, no la implementación.** La implementación se hace con shadcn/ui (ver [Stack de UI y referencias](#stack-de-ui-y-referencias)).

Prioridad 1 del proyecto. Release: MVP.

Flujo: el visitante pide una demo (E02) → el admin ve la solicitud en el panel → tras la llamada, el admin crea el usuario (E03 envía el correo de acceso) → el admin vincula al usuario con las tiendas/scrapers que le corresponden.

Alcance v1:

- Login de administrador y rutas protegidas por rol.
- Solicitudes de demo recibidas.
- Listar y buscar usuarios.
- Crear usuario (solo el botón por ahora, ver PSB2BA-519).
- Vincular usuario con tiendas/scrapers (baja prioridad, ver PSB2BA-524).

Lo demás (baja y bloqueo de cuentas, curaduría, operación, 2FA, empresas, planes) está en E12 · Panel de administración v2.

---

## Resumen

| Ticket | Título | Estado | Prioridad | Depende de (BACK / UX) | Pantalla de referencia |
|---|---|---|---|---|---|
| [PSB2BA-332](https://pricescope-b2b-analytics-s10-26-g9.atlassian.net/browse/PSB2BA-332) | [FRONT] Login de administrador | Tareas por hacer | Alta | BACK 333 (Finalizada) · UX 334 | [UX03 · Ingresar](https://claude.ai/artifact/R5gtqkAMK2T9ckYYJTgUyK#artboard-382858c59631) |
| [PSB2BA-436](https://pricescope-b2b-analytics-s10-26-g9.atlassian.net/browse/PSB2BA-436) | [FRONT] Listar y buscar usuarios | Tareas por hacer | Alta | BACK 437 (Finalizada) · UX 438 | [UX11 · Usuarios](https://claude.ai/artifact/R5gtqkAMK2T9ckYYJTgUyK#artboard-bb9275accf8b) |
| [PSB2BA-516](https://pricescope-b2b-analytics-s10-26-g9.atlassian.net/browse/PSB2BA-516) | [FRONT] Panel de solicitudes de demo | Tareas por hacer | Alta | BACK 502 (Finalizada) · UX 515 · Login 332 | [UX11 · Solicitudes de demo](https://claude.ai/artifact/R5gtqkAMK2T9ckYYJTgUyK#artboard-7d48db9afbd4) |
| [PSB2BA-519](https://pricescope-b2b-analytics-s10-26-g9.atlassian.net/browse/PSB2BA-519) | [FRONT] Crear usuario desde el panel | Tareas por hacer | Pendiente de decisión | BACK 315 (Finalizada) · UX 518 | Solo el botón "Crear usuario" |
| [PSB2BA-524](https://pricescope-b2b-analytics-s10-26-g9.atlassian.net/browse/PSB2BA-524) | [FRONT] Vincular usuario con tiendas | Tareas por hacer | Baja (más adelante) | BACK 522 (Finalizada) · UX 523 · Listado 436 | Pendiente |

Todos los tickets [FRONT] están asignados a angel villalba y tienen las etiquetas `frontend` y `mvp`.

---

## Stack de UI y referencias

### Decisiones

- **Sistema de componentes:** shadcn/ui. Todo lo nuevo del panel se construye con sus componentes, no con clases a mano.
- **Estilos:** Tailwind CSS 4 (ya está en el proyecto).
- **Gráficos:** Recharts 3 (ya está en `package.json`). Los componentes de charts de shadcn se apoyan en Recharts, por lo que encajan con el stack actual.
- **Estructura de referencia:** la plantilla AdminCN (shadcn) para el layout del backoffice: sidebar, header, tarjetas KPI, tablas con filtros y diálogos.
- **Datos:** los datos de ejemplo de la plantilla y del prototipo se reemplazan por datos reales de la API. Ningún dato ficticio llega a producción.
- **Pendiente de configuración:** el proyecto todavía no tiene `components.json` (no está inicializado shadcn). Hay que correr `npx shadcn init` antes del primer componente.

### Referencia 1: plantilla AdminCN (dashboard de ventas)

Fuente: [shadcn-nextjs-admincn-admin-template](https://shadcn-nextjs-admincn-admin-template.vercel.app/dashboard/sales).

**Layout** (lo que sí reutilizamos):

- Sidebar izquierdo colapsable, con navegación agrupada y botón para contraer.
- Header con botón de sidebar, buscador con ⌘K (abre command palette), selector de tema claro/oscuro y avatar de usuario.
- Área de contenido.
- Footer. No aplica al backoffice.

**Patrones útiles para E11:**

- **Tarjetas KPI con delta** (valor, variación con signo y porcentaje). Sirven para los indicadores de Usuarios: Activos, Pendientes de contraseña, Sin tiendas asignadas y Bloqueados o de baja.
- **Tabla de datos** con búsqueda, filtro por estado, selector de filas por página, paginación ("Mostrando 1 a 5 de 25") y botón de acción principal. Sirve para Usuarios (PSB2BA-436) y Solicitudes de demo (PSB2BA-516).
- **Diálogo de formulario** para crear un registro. Sirve para el alta de usuario, si se decide esa forma (PSB2BA-519).
- **Command palette (⌘K):** opcional para el backoffice. Queda fuera del alcance de E11.

**Partes que no usamos** (son contenido de demo de la plantilla):

- Rutas y pantallas de Finance, Logistics, Productivity, Campaign, Analytics, Payments, eCommerce, Orders, Mail, Chat, Kanban, Calendar, Contact, Pricing, FAQ.
- Tarjetas de ventas, ingresos, gastos, "Upgrade plan", "Payment details", "Event card" y el informe de ganancias.
- Tabla de facturas (invoices) con sus columnas.
- Footer y enlaces a la documentación de la plantilla.

**Limitación:** la descripción de la plantilla no confirma las librerías exactas ni el código fuente. Antes de copiar cualquier componente, revisar su código y su licencia.

### Referencia 2: gráficos de shadcn/studio

Fuente: [Charts Component (shadcn/studio)](https://shadcnstudio.com/blocks/dashboard-and-application/charts-component).

**Bloques disponibles** (según la página):

| Bloque | Etiquetas | Instalación (CLI) |
|---|---|---|
| Chart 47 | Basic, New | `npx shadcn add chart-component-47` |
| Chart 51 | Basic, New | `npx shadcn add chart-component-51` |
| Chart 6 | Basic | `npx shadcn add chart-component-06` |

- **Tipos de gráfico** que menciona la página: barras, líneas, torta (pie) y área, y series múltiples. No confirma qué tipo trae cada bloque.
- **Componentes shadcn que usan:** Card, Select, Tabs, Badge, Button y Tooltip.
- **Librería de gráficos:** la página dice que muchas implementaciones usan Recharts, pero no confirma que estos tres bloques lo usen. Antes de instalar, revisar el código del bloque.
- **Props y formato de datos:** no están documentados en la página. Hay que leerlos del código que instala el CLI.
- **Licencia:** el acceso completo está ligado a un plan de pago ("Get all access") y a un archivo de Figma. Las etiquetas "Basic" y "New" no dicen si el bloque es libre. Confirmar la licencia antes de usarlo.

**Relevancia para E11:** las pantallas de E11 (Usuarios, Solicitudes de demo, Login) no tienen gráficos. Los gráficos entran en el dashboard del cliente (UX04) y no están en este grupo de tickets.

### Referencia 3: bloque `dashboard-01` de shadcn

Comando: `npx shadcn@latest add dashboard-01` (todavía no ejecutado).

Es la base del layout de dashboard que ya trae shadcn. Se usa para E11 (backoffice) y para UX04 (dashboard del cliente).

**Qué trae** (según la captura del preview):

- Sidebar con logo, botón principal "Quick Create" y navegación (Dashboard, Lifecycle, Analytics, Projects, Team, Documents).
- Header con botón de contraer sidebar, título de la página y enlace.
- Cuatro tarjetas KPI con valor, badge de variación (+12.5%, -20%) y una línea de contexto.
- Gráfico de área con selector de rango (Last 3 months, Last 30 days, Last 7 days). Este gráfico es la parte que se relaciona con la Referencia 2.
- Tabla de datos debajo del gráfico (la captura se corta antes de verla completa).

**Cómo lo usamos:**

- **E11 (backoffice):** el shell del panel (sidebar + header) y el patrón de tarjetas KPI para el listado de usuarios (PSB2BA-436). Sus items de navegación se reemplazan por Solicitudes de demo, Usuarios, Curaduría y Operación (v2 con etiqueta).
- **UX04 (cliente):** el mismo shell, con los gráficos de precios e inflación reales. Los datos son de la API, no de ejemplo.
- **Antes de copiarlo:** revisar qué componentes instala (sidebar, chart, sheet, etc.) y si pisa archivos existentes (`globals.css`, `layout.tsx`, `button.tsx`). Conviene correrlo en una rama aparte para ver el diff.

**Estado de la instalación de componentes de E11:** solo existe `src/components/ui/button.tsx`. Los demás (input, label, card, table, badge, select, tabs, dialog, alert, pagination) no aparecen en el proyecto. Hay que verificar el comando antes de seguir.

### Otras reglas para la implementación

- `frontend/AGENTS.md` pide leer las guías de Next.js en `node_modules/next/dist/docs/` antes de escribir código. La versión de Next (16.4.1) puede tener cambios respecto de lo que se conoce.
- El login actual usa clases propias (`brand`, `ink`, `line`, `danger-bg`, `danger-ink`). Hay que mapear esos tokens a las variables de shadcn (en `globals.css`) para que el tema sea uno solo.

---

## PSB2BA-332 · [FRONT] Login de administrador

**Historia de usuario:** Como administrador quiero ingresar al backoffice con mi cuenta para gestionar la plataforma.

- **Épica:** E11 · Administrar accesos
- **Prioridad MoSCoW:** Must · Release: MVP · Origen: Extra aprobado
- **Entregable del Impact Map:** D15
- **Pantalla de referencia:** [UX03 · Ingresar](https://claude.ai/artifact/R5gtqkAMK2T9ckYYJTgUyK#artboard-382858c59631) (`Ingresar.dc.html`), como ejemplo. Implementar con shadcn/ui.

**Objetivo:** reemplazar el login que ya existe en el front por el login de la plataforma, implementado con shadcn/ui.

**Estado actual del código:** existe `frontend/src/app/ingresar/page.tsx` con `LoginForm.tsx` e `IngresarAside.tsx`.

- El formulario es una maqueta. Al enviar, siempre muestra el error "Correo o contraseña incorrectos." y no llama a ningún endpoint.
- Usa clases propias, no shadcn.
- Tiene un enlace "Crear cuenta" a `/registro`. Eso contradice la regla de que el alta la hace solo el equipo. Hay que decidir si `/registro` se elimina o se oculta.
- También existen `/demo` y `/registro` en el front. No pertenecen a E11.

**Alcance:**

- Formulario con correo y contraseña, con componentes de shadcn (Input, Label, Button, Alert).
- Botón para mostrar u ocultar la contraseña.
- Llamada al endpoint de login del backend (PSB2BA-333). Guardar el token según la estrategia de auth del backend.
- Error de credenciales con mensaje "Correo o contraseña incorrectos." (`role="alert"`) y campos marcados como inválidos.
- Aviso de sesión vencida por inactividad: "Tu sesión venció por inactividad. Volvé a ingresar."
- Estado de carga mientras se valida el acceso.
- Enlace "¿Olvidaste tu contraseña?" → recuperar acceso (fuera de este ticket).
- Texto de ayuda: "Las cuentas las crea el equipo de PriceScope después de la demo." No hay alta pública.
- Tras ingresar, el rol determina la pantalla de destino (backoffice para admin, app del cliente para cliente). Las rutas protegidas están en PSB2BA-336.

**Notas del prototipo:**

- El prototipo es una sola pantalla para cliente y admin. El ticket dice "login de administrador". Confirmar si el backoffice usa el mismo formulario o una pantalla aparte.
- Los botones "Cliente" y "Administrador" del prototipo son solo para navegar. No van a producción.
- El prototipo trae correo y contraseña precargados. No replicar eso.

**Criterio de terminado:**

- Reemplaza al login actual de `/ingresar`.
- Usa componentes de shadcn/ui.
- Funciona en escritorio y móvil.
- Muestra estados de carga, error y sesión vencida.
- El código está revisado en un pull request.

**Relacionados:** PSB2BA-334 (UX/UI), PSB2BA-335 (QA), PSB2BA-336 (BACK rutas protegidas por rol, Finalizada).

---

## PSB2BA-436 · [FRONT] Listar y buscar usuarios

**Historia de usuario:** Como administrador quiero listar, buscar y filtrar usuarios para encontrarlos rápido.

- **Épica:** E11 · Panel de administración
- **Prioridad MoSCoW:** Must · Release: MVP
- **Pantalla de referencia:** [UX11 · Usuarios](https://claude.ai/artifact/R5gtqkAMK2T9ckYYJTgUyK#artboard-bb9275accf8b) (`AdminUsuarios.dc.html`), como ejemplo. Implementar con shadcn/ui.

**Objetivo:** implementar en React la tabla de usuarios del panel admin.

**Alcance:**

- Encabezado con título "Usuarios" y descripción breve.
- Botón "Crear usuario" en el encabezado (solo el botón; el flujo se define en PSB2BA-519).
- Cuatro indicadores KPI: Activos, Pendientes de contraseña, Sin tiendas asignadas y Bloqueados o de baja.
- Búsqueda por nombre o correo.
- Filtro por rol: Todos, Clientes, Admins.
- Filtro por estado: Todos, Activo, Pendiente, Bloqueado, Baja.
- Tabla con columnas: Usuario (nombre y correo, enlaza al detalle), Empresa, Rol, Estado, Tiendas, Último acceso y Acciones ("Ver").
- Tiendas: muestra la cantidad de tiendas asignadas. "Sin tiendas" si es cero. "—" para admins.
- Estado vacío con "Limpiar filtros".
- Paginación con total de usuarios, Anterior y Siguiente.
- Estados de carga y error.

**Notas:**

- Un admin no puede bloquearse ni darse de baja a sí mismo. Aplica cuando llegue E12.
- El menú "Más acciones" (bloquear y dar de baja) es de E12, no de este ticket.
- Los indicadores no están en el ticket. Confirmar si el backend los entrega o si se calculan desde el listado.

**Criterio de terminado:**

- La pantalla usa componentes de shadcn/ui y coincide con la estructura de referencia.
- Funciona en escritorio y tablet.
- Búsqueda y filtros funcionan juntos.
- El código está revisado en un pull request.

**Relacionados:** PSB2BA-439 (QA). Este ticket es prerrequisito de PSB2BA-524.

---

## PSB2BA-516 · [FRONT] Panel de solicitudes de demo

**Historia de usuario:** Como administrador quiero ver las solicitudes de demo que llegan para contactar a los clientes interesados.

- **Épica:** E11 · Panel de administración
- **Prioridad MoSCoW:** Must · Release: MVP
- **Pantalla de referencia:** [UX11 · Solicitudes de demo](https://claude.ai/artifact/R5gtqkAMK2T9ckYYJTgUyK#artboard-7d48db9afbd4) (`AdminSolicitudes.dc.html`), como ejemplo. Implementar con shadcn/ui.

**Objetivo:** implementar en React el panel de solicitudes de demo.

**Alcance:**

- Encabezado con título "Solicitudes de demo" y descripción breve.
- Badge con la cantidad de solicitudes nuevas desde la última visita. Se calcula en el navegador, sin estado en el backend.
- Badge "Nueva" en las filas nuevas.
- Búsqueda por empresa o correo.
- Filtro por tipo de organización (Fondo, Medio, Minorista, Otro).
- Orden: más nuevas primero.
- Tabla con columnas: expandir comentario, Empresa y contacto, Correo, Organización, Preferencia (fecha y hora de la llamada), Recibida y Acción "Crear usuario".
- Comentario expandible por fila.
- Paginación con total, Anterior y Siguiente.
- Estados de carga, vacío y error.
- Consume el GET del ticket PSB2BA-502.

**Notas:**

- La única acción por fila es el botón "Crear usuario". Lo que pasa después queda para PSB2BA-519.
- El filtro "Tipo de organización" no tiene menú definido. Confirmar si es selector de una opción o multiselección.

**Criterio de terminado:**

- La pantalla usa componentes de shadcn/ui y coincide con la estructura de referencia.
- Funciona en escritorio y tablet.
- El código está revisado en un pull request.

**Relacionados:** PSB2BA-517 (QA).

---

## PSB2BA-519 · [FRONT] Crear usuario desde el panel

**Historia de usuario:** Como administrador quiero crear la cuenta de un cliente con los datos que completó tras la llamada para que pueda ingresar. El usuario nunca se registra solo.

- **Épica:** E11 · Panel de administración
- **Prioridad MoSCoW:** Must · Release: MVP

**Estado:** pendiente de decisión. Por ahora solo existe el botón "Crear usuario" en Solicitudes de demo y en Usuarios.

**Pendiente:** definir qué pasa al hacer clic (diálogo, página propia u otra forma). El prototipo tiene un diálogo como ejemplo, pero todavía no se decidió si se usa.

**Relacionados:** PSB2BA-520 (QA).

---

## PSB2BA-524 · [FRONT] Vincular usuario con tiendas

**Historia de usuario:** Como administrador quiero asignar a cada cliente las tiendas que se le monitorean para que solo vea sus datos.

- **Épica:** E11 · Panel de administración
- **Prioridad MoSCoW:** Must · Release: MVP

**Estado:** baja prioridad. Se desarrolla más adelante, con calma.

**Aclaración:** la asignación es manual. El admin asigna y quita tiendas con confirmación. No es automática. El prototipo tiene una pantalla "UX11 · Usuario y tiendas" (`project/AdminUsuarioDetalle.dc.html`), todavía sin revisar.

**Dependencias:**

- [UX/UI] Vincular usuario con tiendas (PSB2BA-523).
- [BACK] Vincular usuario con tiendas (PSB2BA-522). Ya finalizado.
- Listado de usuarios (PSB2BA-436).

**Relacionados:** PSB2BA-525 (QA).

---

## Pendientes para completar

- Decidir qué hace el botón "Crear usuario" (PSB2BA-519).
- Confirmar si el backoffice usa el mismo formulario de login que el cliente (PSB2BA-332).
- Decidir qué pasa con `/registro` y el enlace "Crear cuenta" del login actual (PSB2BA-332).
- Confirmar con el backend si los indicadores del listado vienen del servidor (PSB2BA-436).
- Confirmar el tipo de selector de "Tipo de organización" (PSB2BA-516).
- Inicializar shadcn/ui en `frontend/` (`components.json`) antes del primer componente.
- Confirmar la licencia de los bloques de shadcn/studio antes de instalarlos.
- Revisar la pantalla "Usuario y tiendas" del prototipo cuando se retome PSB2BA-524.

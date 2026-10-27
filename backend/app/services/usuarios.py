import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import EstadoUsuario, Rol, TipoToken, Usuario, UsuarioTienda
from app.schemas.usuarios import UsuarioCrear
from app.services import correo, tokens
from app.services.correo import ColaDeTareas
from app.services.errores import Conflicto, ErrorNegocio, NoEncontrado


async def obtener_usuario(db: AsyncSession, usuario_id: uuid.UUID) -> Usuario:
    usuario = await db.get(Usuario, usuario_id)
    if usuario is None:
        raise NoEncontrado("El usuario no existe")
    return usuario


async def contar_tiendas(db: AsyncSession, usuario_id: uuid.UUID) -> int:
    return await db.scalar(select(func.count()).where(UsuarioTienda.usuario_id == usuario_id)) or 0


async def crear_usuario(
    db: AsyncSession, cola: ColaDeTareas, datos: UsuarioCrear
) -> tuple[Usuario, bool]:
    """Crea el usuario en estado pendiente y encola el correo de bienvenida."""
    correo_normalizado = datos.correo.lower()
    if await db.scalar(select(Usuario.id).where(Usuario.correo == correo_normalizado)):
        raise Conflicto("Ya existe un usuario con ese correo")

    usuario = Usuario(
        nombre=datos.nombre, empresa=datos.empresa, correo=correo_normalizado, rol=datos.rol
    )
    db.add(usuario)
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise Conflicto("Ya existe un usuario con ese correo") from None

    token = await tokens.emitir_token(db, usuario.id, TipoToken.DEFINIR)
    await db.commit()
    await db.refresh(usuario)
    encolado = await correo.encolar_bienvenida(cola, usuario, token)
    return usuario, encolado


async def reenviar_acceso(db: AsyncSession, cola: ColaDeTareas, usuario_id: uuid.UUID) -> bool:
    usuario = await obtener_usuario(db, usuario_id)
    if usuario.estado != EstadoUsuario.PENDIENTE:
        raise ErrorNegocio("El usuario ya definió su contraseña")
    token = await tokens.emitir_token(db, usuario.id, TipoToken.DEFINIR)
    await db.commit()
    return await correo.encolar_bienvenida(cola, usuario, token)


async def solicitar_recuperacion(
    db: AsyncSession, cola: ColaDeTareas, correo_ingresado: str
) -> None:
    """Solo actúa si la cuenta existe y está activa. La respuesta HTTP es siempre la misma."""
    usuario = await db.scalar(select(Usuario).where(Usuario.correo == correo_ingresado.lower()))
    if usuario is None or usuario.estado != EstadoUsuario.ACTIVO:
        return
    token = await tokens.emitir_token(db, usuario.id, TipoToken.RESTABLECER)
    await db.commit()
    await correo.encolar_recuperacion(cola, usuario, token)


async def listar_usuarios(
    db: AsyncSession,
    *,
    q: str | None,
    rol: Rol | None,
    estado: EstadoUsuario | None,
    pagina: int,
    tamano: int,
) -> tuple[list[tuple[Usuario, int]], int]:
    filtros = []
    if q:
        patron = f"%{q.strip()}%"
        filtros.append(or_(Usuario.nombre.ilike(patron), Usuario.correo.ilike(patron)))
    if rol:
        filtros.append(Usuario.rol == rol)
    if estado:
        filtros.append(Usuario.estado == estado)

    total = await db.scalar(select(func.count()).select_from(Usuario).where(*filtros)) or 0

    cantidad = (
        select(func.count(UsuarioTienda.tienda_id))
        .where(UsuarioTienda.usuario_id == Usuario.id)
        .correlate(Usuario)
        .scalar_subquery()
    )
    filas = await db.execute(
        select(Usuario, cantidad.label("cantidad_tiendas"))
        .where(*filtros)
        .order_by(Usuario.creado_en.desc())
        .offset((pagina - 1) * tamano)
        .limit(tamano)
    )
    return [(usuario, cant) for usuario, cant in filas.all()], total

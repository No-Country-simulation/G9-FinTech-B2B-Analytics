import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Rol, Tienda, Usuario, UsuarioTienda
from app.services.errores import Conflicto, ErrorNegocio, NoEncontrado
from app.services.usuarios import obtener_usuario


async def listar_catalogo(db: AsyncSession) -> list[Tienda]:
    filas = await db.scalars(select(Tienda).where(Tienda.activa.is_(True)).order_by(Tienda.nombre))
    return list(filas)


async def tiendas_de_usuario(db: AsyncSession, usuario_id: uuid.UUID) -> list[Tienda]:
    filas = await db.scalars(
        select(Tienda)
        .join(UsuarioTienda, UsuarioTienda.tienda_id == Tienda.id)
        .where(UsuarioTienda.usuario_id == usuario_id)
        .order_by(Tienda.nombre)
    )
    return list(filas)


async def ids_tiendas_visibles(db: AsyncSession, usuario: Usuario) -> list[uuid.UUID]:
    """Tiendas cuyos datos puede ver el usuario. Lo van a usar dashboard, matriz y alertas."""
    if usuario.rol == Rol.ADMIN:
        return list(await db.scalars(select(Tienda.id)))
    return list(
        await db.scalars(
            select(UsuarioTienda.tienda_id).where(UsuarioTienda.usuario_id == usuario.id)
        )
    )


async def asignar_tienda(
    db: AsyncSession, usuario_id: uuid.UUID, tienda_id: uuid.UUID, admin_id: uuid.UUID
) -> None:
    usuario = await obtener_usuario(db, usuario_id)
    if usuario.rol == Rol.ADMIN:
        raise ErrorNegocio("Las tiendas solo se asignan a clientes")
    tienda = await db.get(Tienda, tienda_id)
    if tienda is None or not tienda.activa:
        raise NoEncontrado("La tienda no existe")
    if await db.get(UsuarioTienda, (usuario_id, tienda_id)):
        raise Conflicto("La tienda ya está asignada a este usuario")
    db.add(UsuarioTienda(usuario_id=usuario_id, tienda_id=tienda_id, asignada_por=admin_id))
    await db.commit()


async def quitar_tienda(db: AsyncSession, usuario_id: uuid.UUID, tienda_id: uuid.UUID) -> None:
    resultado = await db.execute(
        delete(UsuarioTienda).where(
            UsuarioTienda.usuario_id == usuario_id, UsuarioTienda.tienda_id == tienda_id
        )
    )
    if resultado.rowcount == 0:
        raise NoEncontrado("La tienda no estaba asignada a este usuario")
    await db.commit()

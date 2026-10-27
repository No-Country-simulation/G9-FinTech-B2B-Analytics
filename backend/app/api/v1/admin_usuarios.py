import uuid
from typing import Annotated

from fastapi import APIRouter, Query, status

from app.api.deps import AdminActual, Cola, SesionDB
from app.models import EstadoUsuario, Rol, Usuario
from app.schemas.comunes import Mensaje, Pagina
from app.schemas.tiendas import AsignarTiendaEntrada, TiendaSalida
from app.schemas.usuarios import UsuarioCreadoSalida, UsuarioCrear, UsuarioSalida
from app.services import tiendas, usuarios

router = APIRouter(prefix="/admin/usuarios", tags=["admin · usuarios"])


def _salida(usuario: Usuario, cantidad_tiendas: int) -> UsuarioSalida:
    return UsuarioSalida.model_validate(usuario).model_copy(
        update={"cantidad_tiendas": cantidad_tiendas}
    )


@router.get("", response_model=Pagina[UsuarioSalida])
async def listar_usuarios(
    db: SesionDB,
    _admin: AdminActual,
    q: Annotated[str | None, Query(max_length=100, description="Busca en nombre y correo")] = None,
    rol: Rol | None = None,
    estado: EstadoUsuario | None = None,
    pagina: Annotated[int, Query(ge=1)] = 1,
    tamano: Annotated[int, Query(ge=1, le=100)] = 20,
) -> Pagina[UsuarioSalida]:
    filas, total = await usuarios.listar_usuarios(
        db, q=q, rol=rol, estado=estado, pagina=pagina, tamano=tamano
    )
    return Pagina[UsuarioSalida](
        items=[_salida(u, c) for u, c in filas], total=total, pagina=pagina, tamano=tamano
    )


@router.post("", response_model=UsuarioCreadoSalida, status_code=status.HTTP_201_CREATED)
async def crear_usuario(
    datos: UsuarioCrear, db: SesionDB, cola: Cola, _admin: AdminActual
) -> UsuarioCreadoSalida:
    usuario, encolado = await usuarios.crear_usuario(db, cola, datos)
    return UsuarioCreadoSalida(usuario=_salida(usuario, 0), correo_encolado=encolado)


@router.get("/{usuario_id}", response_model=UsuarioSalida)
async def obtener_usuario(
    usuario_id: uuid.UUID, db: SesionDB, _admin: AdminActual
) -> UsuarioSalida:
    usuario = await usuarios.obtener_usuario(db, usuario_id)
    return _salida(usuario, await usuarios.contar_tiendas(db, usuario_id))


@router.post(
    "/{usuario_id}/reenviar-acceso", response_model=Mensaje, status_code=status.HTTP_202_ACCEPTED
)
async def reenviar_acceso(
    usuario_id: uuid.UUID, db: SesionDB, cola: Cola, _admin: AdminActual
) -> Mensaje:
    encolado = await usuarios.reenviar_acceso(db, cola, usuario_id)
    if not encolado:
        return Mensaje(mensaje="No pudimos enviar el correo. Probá de nuevo en unos minutos.")
    return Mensaje(mensaje="Enviamos un nuevo correo de acceso.")


@router.get("/{usuario_id}/tiendas", response_model=list[TiendaSalida])
async def tiendas_del_usuario(
    usuario_id: uuid.UUID, db: SesionDB, _admin: AdminActual
) -> list[TiendaSalida]:
    await usuarios.obtener_usuario(db, usuario_id)  # 404 si no existe
    return [
        TiendaSalida.model_validate(t) for t in await tiendas.tiendas_de_usuario(db, usuario_id)
    ]


@router.post(
    "/{usuario_id}/tiendas", response_model=list[TiendaSalida], status_code=status.HTTP_201_CREATED
)
async def asignar_tienda(
    usuario_id: uuid.UUID, datos: AsignarTiendaEntrada, db: SesionDB, admin: AdminActual
) -> list[TiendaSalida]:
    await tiendas.asignar_tienda(db, usuario_id, datos.tienda_id, admin.id)
    return [
        TiendaSalida.model_validate(t) for t in await tiendas.tiendas_de_usuario(db, usuario_id)
    ]


@router.delete("/{usuario_id}/tiendas/{tienda_id}", status_code=status.HTTP_204_NO_CONTENT)
async def quitar_tienda(
    usuario_id: uuid.UUID, tienda_id: uuid.UUID, db: SesionDB, _admin: AdminActual
) -> None:
    await tiendas.quitar_tienda(db, usuario_id, tienda_id)

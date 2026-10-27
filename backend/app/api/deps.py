import uuid
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.seguridad import decodificar_access_token
from app.models import EstadoUsuario, Rol, Sesion, Usuario
from app.services.correo import ColaDeTareas

SesionDB = Annotated[AsyncSession, Depends(get_session)]

_bearer = HTTPBearer(auto_error=False)


def get_cola(request: Request) -> ColaDeTareas:
    return request.app.state.arq


Cola = Annotated[ColaDeTareas, Depends(get_cola)]


async def get_usuario_actual(
    request: Request,
    db: SesionDB,
    credenciales: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> Usuario:
    no_autenticado = HTTPException(
        status.HTTP_401_UNAUTHORIZED, "No autenticado", headers={"WWW-Authenticate": "Bearer"}
    )
    if credenciales is None:
        raise no_autenticado
    try:
        payload = decodificar_access_token(credenciales.credentials)
        usuario_id = uuid.UUID(payload["sub"])
        sesion_id = uuid.UUID(payload["sid"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise no_autenticado from None

    usuario = await db.scalar(
        select(Usuario)
        .join(Sesion, Sesion.usuario_id == Usuario.id)
        .where(Usuario.id == usuario_id, Sesion.id == sesion_id, Sesion.revocada_en.is_(None))
    )
    if usuario is None or usuario.estado != EstadoUsuario.ACTIVO:
        raise no_autenticado

    request.state.sesion_id = sesion_id  # lo usa /auth/logout
    return usuario


UsuarioActual = Annotated[Usuario, Depends(get_usuario_actual)]


async def requiere_admin(usuario: UsuarioActual) -> Usuario:
    if usuario.rol != Rol.ADMIN:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "No tenés permisos para esta acción")
    return usuario


AdminActual = Annotated[Usuario, Depends(requiere_admin)]

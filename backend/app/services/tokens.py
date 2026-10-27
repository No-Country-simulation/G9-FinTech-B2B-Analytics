import asyncio
import uuid
from datetime import UTC, datetime, timedelta
from typing import Literal

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.seguridad import generar_token_opaco, hash_token, hashear_password
from app.models import EstadoUsuario, Sesion, TipoToken, TokenAcceso, Usuario
from app.services.errores import ErrorNegocio

DURACION = {
    TipoToken.DEFINIR: timedelta(hours=settings.token_definir_horas),
    TipoToken.RESTABLECER: timedelta(minutes=settings.token_restablecer_minutos),
}


async def emitir_token(db: AsyncSession, usuario_id: uuid.UUID, tipo: TipoToken) -> str:
    """Invalida los enlaces anteriores del mismo tipo y crea uno nuevo. No hace commit."""
    ahora = datetime.now(UTC)
    await db.execute(
        update(TokenAcceso)
        .where(
            TokenAcceso.usuario_id == usuario_id,
            TokenAcceso.tipo == tipo,
            TokenAcceso.usado_en.is_(None),
        )
        .values(usado_en=ahora)
    )
    token, token_hash = generar_token_opaco()
    db.add(
        TokenAcceso(
            usuario_id=usuario_id,
            tipo=tipo,
            token_hash=token_hash,
            expira_en=ahora + DURACION[tipo],
        )
    )
    return token


async def estado_token(
    db: AsyncSession, token: str
) -> tuple[Literal["valido", "vencido", "invalido"], TipoToken | None]:
    registro = await db.scalar(
        select(TokenAcceso).where(TokenAcceso.token_hash == hash_token(token))
    )
    if registro is None or registro.usado_en is not None:
        return "invalido", None
    if registro.expira_en <= datetime.now(UTC):
        return "vencido", registro.tipo
    return "valido", registro.tipo


async def consumir_token(db: AsyncSession, token: str, password: str) -> None:
    """Define o restablece la contraseña. Activa al usuario pendiente y cierra sus sesiones."""
    ahora = datetime.now(UTC)
    registro = await db.scalar(
        select(TokenAcceso).where(TokenAcceso.token_hash == hash_token(token)).with_for_update()
    )
    if registro is None or registro.usado_en is not None:
        raise ErrorNegocio("El enlace no es válido. Pedí uno nuevo al equipo de PriceScope.")
    if registro.expira_en <= ahora:
        raise ErrorNegocio("El enlace venció. Pedí uno nuevo.")

    usuario = await db.get(Usuario, registro.usuario_id)
    if usuario is None or usuario.estado in (EstadoUsuario.BLOQUEADO, EstadoUsuario.BAJA):
        raise ErrorNegocio("El enlace no es válido. Pedí uno nuevo al equipo de PriceScope.")

    usuario.password_hash = await asyncio.to_thread(hashear_password, password)
    if usuario.estado == EstadoUsuario.PENDIENTE:
        usuario.estado = EstadoUsuario.ACTIVO
    registro.usado_en = ahora
    await db.execute(
        update(Sesion)
        .where(Sesion.usuario_id == usuario.id, Sesion.revocada_en.is_(None))
        .values(revocada_en=ahora)
    )
    await db.commit()

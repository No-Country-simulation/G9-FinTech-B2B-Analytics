import asyncio
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.seguridad import (
    HASH_FALSO,
    crear_access_token,
    generar_token_opaco,
    hash_token,
    verificar_password,
)
from app.models import EstadoUsuario, Sesion, Usuario


async def autenticar(db: AsyncSession, correo: str, password: str) -> Usuario | None:
    """Devuelve el usuario si puede ingresar. Mismo resultado (None) para todos los fallos."""
    usuario = await db.scalar(select(Usuario).where(Usuario.correo == correo.lower()))
    if usuario is None or usuario.password_hash is None:
        await asyncio.to_thread(verificar_password, password, HASH_FALSO)
        return None
    valida = await asyncio.to_thread(verificar_password, password, usuario.password_hash)
    if not valida or usuario.estado != EstadoUsuario.ACTIVO:
        return None
    return usuario


async def abrir_sesion(
    db: AsyncSession, usuario: Usuario, user_agent: str | None
) -> tuple[str, str]:
    """Devuelve (access_token, refresh_token)."""
    ahora = datetime.now(UTC)
    refresh, refresh_hash = generar_token_opaco()
    sesion = Sesion(
        id=uuid.uuid4(),
        usuario_id=usuario.id,
        refresh_hash=refresh_hash,
        ultimo_uso_en=ahora,
        expira_en=ahora + timedelta(hours=settings.sesion_duracion_max_horas),
        user_agent=(user_agent or "")[:255] or None,
    )
    db.add(sesion)
    usuario.ultimo_acceso = ahora
    await db.commit()
    return crear_access_token(usuario.id, usuario.rol, sesion.id), refresh


async def renovar_sesion(db: AsyncSession, refresh: str) -> tuple[Usuario, str, str] | None:
    """Rota el refresh token. Devuelve (usuario, access nuevo, refresh nuevo) o None si venció."""
    ahora = datetime.now(UTC)
    sesion = await db.scalar(
        select(Sesion).where(Sesion.refresh_hash == hash_token(refresh)).with_for_update()
    )
    if sesion is None or sesion.revocada_en is not None:
        return None

    usuario = await db.get(Usuario, sesion.usuario_id)
    inactiva = (
        sesion.ultimo_uso_en + timedelta(minutes=settings.sesion_inactividad_minutos) <= ahora
    )
    if (
        inactiva
        or sesion.expira_en <= ahora
        or usuario is None
        or usuario.estado != EstadoUsuario.ACTIVO
    ):
        sesion.revocada_en = ahora
        await db.commit()
        return None

    nuevo, nuevo_hash = generar_token_opaco()
    sesion.refresh_hash = nuevo_hash
    sesion.ultimo_uso_en = ahora
    await db.commit()
    return usuario, crear_access_token(usuario.id, usuario.rol, sesion.id), nuevo


async def cerrar_sesion(db: AsyncSession, sesion_id: uuid.UUID) -> None:
    await db.execute(
        update(Sesion)
        .where(Sesion.id == sesion_id, Sesion.revocada_en.is_(None))
        .values(revocada_en=datetime.now(UTC))
    )
    await db.commit()

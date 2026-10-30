import asyncio
import uuid
from datetime import UTC, datetime, timedelta
from typing import Literal

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import generate_opaque_token, hash_password, hash_token
from app.models import AccessToken, TokenType, User, UserSession, UserStatus
from app.services.errors import BusinessError

DURATIONS = {
    TokenType.SET_PASSWORD: timedelta(hours=settings.set_password_token_hours),
    TokenType.RESET_PASSWORD: timedelta(minutes=settings.reset_token_minutes),
}


async def issue_token(db: AsyncSession, user_id: uuid.UUID, token_type: TokenType) -> str:
    """Invalidates previous links of the same type and creates a new one. Does not commit."""
    now = datetime.now(UTC)
    await db.execute(
        update(AccessToken)
        .where(
            AccessToken.user_id == user_id,
            AccessToken.type == token_type,
            AccessToken.used_at.is_(None),
        )
        .values(used_at=now)
    )
    token, token_hash = generate_opaque_token()
    db.add(
        AccessToken(
            user_id=user_id,
            type=token_type,
            token_hash=token_hash,
            expires_at=now + DURATIONS[token_type],
        )
    )
    return token


async def token_status(
    db: AsyncSession, token: str
) -> tuple[Literal["valid", "expired", "invalid"], TokenType | None, User | None]:
    """The owner is returned only for a valid link, so the page can greet them."""
    record = await db.scalar(select(AccessToken).where(AccessToken.token_hash == hash_token(token)))
    if record is None or record.used_at is not None:
        return "invalid", None, None
    if record.expires_at <= datetime.now(UTC):
        return "expired", record.type, None
    return "valid", record.type, await db.get(User, record.user_id)


async def consume_token(db: AsyncSession, token: str, password: str) -> None:
    """Sets or resets the password. Activates a pending user and closes their sessions."""
    now = datetime.now(UTC)
    record = await db.scalar(
        select(AccessToken).where(AccessToken.token_hash == hash_token(token)).with_for_update()
    )
    if record is None or record.used_at is not None:
        raise BusinessError("El enlace no es válido. Pedí uno nuevo al equipo de PriceScope.")
    if record.expires_at <= now:
        raise BusinessError("El enlace venció. Pedí uno nuevo.")

    user = await db.get(User, record.user_id)
    if user is None or user.status in (UserStatus.BLOCKED, UserStatus.DEACTIVATED):
        raise BusinessError("El enlace no es válido. Pedí uno nuevo al equipo de PriceScope.")

    user.password_hash = await asyncio.to_thread(hash_password, password)
    if user.status == UserStatus.PENDING:
        user.status = UserStatus.ACTIVE
    record.used_at = now
    await db.execute(
        update(UserSession)
        .where(UserSession.user_id == user.id, UserSession.revoked_at.is_(None))
        .values(revoked_at=now)
    )
    await db.commit()

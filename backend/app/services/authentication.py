import asyncio
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    FAKE_HASH,
    create_access_token,
    generate_opaque_token,
    hash_token,
    verify_password,
)
from app.models import User, UserSession, UserStatus


async def authenticate(db: AsyncSession, email: str, password: str) -> User | None:
    """Returns the user if they can log in. Same result (None) for every failure."""
    user = await db.scalar(select(User).where(User.email == email.lower()))
    if user is None or user.password_hash is None:
        await asyncio.to_thread(verify_password, password, FAKE_HASH)
        return None
    valid = await asyncio.to_thread(verify_password, password, user.password_hash)
    if not valid or user.status != UserStatus.ACTIVE:
        return None
    return user


async def open_session(db: AsyncSession, user: User, user_agent: str | None) -> tuple[str, str]:
    """Returns (access_token, refresh_token)."""
    now = datetime.now(UTC)
    refresh, refresh_hash = generate_opaque_token()
    session = UserSession(
        id=uuid.uuid4(),
        user_id=user.id,
        refresh_hash=refresh_hash,
        last_used_at=now,
        expires_at=now + timedelta(hours=settings.session_max_hours),
        user_agent=(user_agent or "")[:255] or None,
    )
    db.add(session)
    user.last_access_at = now
    await db.commit()
    return create_access_token(user.id, user.role, session.id), refresh


async def refresh_session(db: AsyncSession, refresh: str) -> tuple[User, str, str] | None:
    """Rotates the refresh token. Returns (user, new access, new refresh) or None if expired."""
    now = datetime.now(UTC)
    session = await db.scalar(
        select(UserSession).where(UserSession.refresh_hash == hash_token(refresh)).with_for_update()
    )
    if session is None or session.revoked_at is not None:
        return None

    user = await db.get(User, session.user_id)
    inactive = session.last_used_at + timedelta(minutes=settings.session_inactivity_minutes) <= now
    if inactive or session.expires_at <= now or user is None or user.status != UserStatus.ACTIVE:
        session.revoked_at = now
        await db.commit()
        return None

    new, new_hash = generate_opaque_token()
    session.refresh_hash = new_hash
    session.last_used_at = now
    await db.commit()
    return user, create_access_token(user.id, user.role, session.id), new


async def close_session(db: AsyncSession, session_id: uuid.UUID) -> None:
    await db.execute(
        update(UserSession)
        .where(UserSession.id == session_id, UserSession.revoked_at.is_(None))
        .values(revoked_at=datetime.now(UTC))
    )
    await db.commit()

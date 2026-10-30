import uuid
from datetime import UTC, datetime

from sqlalchemy import func, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    AccessToken,
    EmailChange,
    Role,
    TokenType,
    User,
    UserSession,
    UserStatus,
    UserStore,
)
from app.schemas.users import UserCreate
from app.services import mail, tokens
from app.services.errors import BusinessError, ConflictError, ForbiddenError, NotFoundError
from app.services.mail import TaskQueue


async def get_user(db: AsyncSession, user_id: uuid.UUID) -> User:
    user = await db.get(User, user_id)
    if user is None:
        raise NotFoundError("El usuario no existe")
    return user


async def count_stores(db: AsyncSession, user_id: uuid.UUID) -> int:
    return await db.scalar(select(func.count()).where(UserStore.user_id == user_id)) or 0


async def create_user(db: AsyncSession, queue: TaskQueue, data: UserCreate) -> tuple[User, bool]:
    """Creates the user in pending status and enqueues the welcome email."""
    normalized_email = data.email.lower()
    if await db.scalar(select(User.id).where(User.email == normalized_email)):
        raise ConflictError("Ya existe un usuario con ese correo")

    user = User(name=data.name, company=data.company, email=normalized_email, role=data.role)
    db.add(user)
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise ConflictError("Ya existe un usuario con ese correo") from None

    token = await tokens.issue_token(db, user.id, TokenType.SET_PASSWORD)
    await db.commit()
    await db.refresh(user)
    queued = await mail.enqueue_welcome(queue, user, token)
    return user, queued


async def resend_access(db: AsyncSession, queue: TaskQueue, user_id: uuid.UUID) -> bool:
    user = await get_user(db, user_id)
    if user.status != UserStatus.PENDING:
        raise BusinessError("El usuario ya definió su contraseña")
    token = await tokens.issue_token(db, user.id, TokenType.SET_PASSWORD)
    await db.commit()
    return await mail.enqueue_welcome(queue, user, token)


async def _lock_user(db: AsyncSession, user_id: uuid.UUID) -> User:
    user = await db.scalar(
        select(User)
        .where(User.id == user_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if user is None:
        raise NotFoundError("El usuario no existe")
    return user


async def _invalidate_links(db: AsyncSession, user_id: uuid.UUID) -> None:
    """Invalidates pending access links and email change requests. Does not commit."""
    now = datetime.now(UTC)
    await db.execute(
        update(AccessToken)
        .where(AccessToken.user_id == user_id, AccessToken.used_at.is_(None))
        .values(used_at=now)
    )
    await db.execute(
        update(EmailChange)
        .where(EmailChange.user_id == user_id, EmailChange.used_at.is_(None))
        .values(used_at=now)
    )


async def _close_access(db: AsyncSession, user_id: uuid.UUID) -> None:
    """Revokes every session and pending link of the user. Does not commit."""
    await db.execute(
        update(UserSession)
        .where(UserSession.user_id == user_id, UserSession.revoked_at.is_(None))
        .values(revoked_at=datetime.now(UTC))
    )
    await _invalidate_links(db, user_id)


async def block_user(db: AsyncSession, user_id: uuid.UUID, admin_id: uuid.UUID) -> User:
    user = await _lock_user(db, user_id)
    if user.id == admin_id:
        raise ForbiddenError("No podés bloquear tu propia cuenta")
    if user.status == UserStatus.BLOCKED:
        raise ConflictError("El usuario ya está bloqueado")
    if user.status == UserStatus.DEACTIVATED:
        raise BusinessError("El usuario está dado de baja")
    user.status = UserStatus.BLOCKED
    await _close_access(db, user.id)
    await db.commit()
    await db.refresh(user)
    return user


async def unblock_user(db: AsyncSession, user_id: uuid.UUID) -> User:
    """Restores access. A user who never set a password goes back to pending."""
    user = await _lock_user(db, user_id)
    if user.status != UserStatus.BLOCKED:
        raise BusinessError("El usuario no está bloqueado")
    user.status = UserStatus.ACTIVE if user.password_hash else UserStatus.PENDING
    await db.commit()
    await db.refresh(user)
    return user


async def deactivate_user(db: AsyncSession, user_id: uuid.UUID, admin_id: uuid.UUID) -> User:
    """Deactivation is final: the account cannot log in again."""
    user = await _lock_user(db, user_id)
    if user.id == admin_id:
        raise ForbiddenError("No podés darte de baja a vos mismo")
    if user.status == UserStatus.DEACTIVATED:
        raise ConflictError("El usuario ya está dado de baja")
    user.status = UserStatus.DEACTIVATED
    await _close_access(db, user.id)
    await db.commit()
    await db.refresh(user)
    return user


async def change_email(
    db: AsyncSession, queue: TaskQueue, user_id: uuid.UUID, new_email: str
) -> tuple[User, bool]:
    """Changes the login email. Links sent to the old address stop working; a pending
    user gets a new access email at the new address."""
    user = await _lock_user(db, user_id)
    if user.status not in (UserStatus.ACTIVE, UserStatus.PENDING):
        raise BusinessError("Solo se puede cambiar el correo de usuarios activos o pendientes")
    normalized_email = new_email.lower()
    if normalized_email == user.email:
        raise BusinessError("El nuevo correo debe ser diferente del actual")
    if await db.scalar(select(User.id).where(User.email == normalized_email)):
        raise ConflictError("Ya existe un usuario con ese correo")

    user.email = normalized_email
    await _invalidate_links(db, user.id)
    token = None
    if user.status == UserStatus.PENDING:
        token = await tokens.issue_token(db, user.id, TokenType.SET_PASSWORD)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise ConflictError("Ya existe un usuario con ese correo") from None
    await db.refresh(user)
    queued = await mail.enqueue_welcome(queue, user, token) if token else False
    return user, queued


async def send_password_reset(db: AsyncSession, queue: TaskQueue, user_id: uuid.UUID) -> bool:
    user = await get_user(db, user_id)
    if user.status != UserStatus.ACTIVE:
        raise BusinessError("Solo se puede restablecer la contraseña de usuarios activos")
    token = await tokens.issue_token(db, user.id, TokenType.RESET_PASSWORD)
    await db.commit()
    return await mail.enqueue_recovery(queue, user, token)


async def request_password_reset(db: AsyncSession, queue: TaskQueue, entered_email: str) -> None:
    """Only acts if the account exists and is active. The HTTP response is always the same."""
    user = await db.scalar(select(User).where(User.email == entered_email.lower()))
    if user is None or user.status != UserStatus.ACTIVE:
        return
    token = await tokens.issue_token(db, user.id, TokenType.RESET_PASSWORD)
    await db.commit()
    await mail.enqueue_recovery(queue, user, token)


async def list_users(
    db: AsyncSession,
    *,
    q: str | None,
    role: Role | None,
    status: UserStatus | None,
    page: int,
    size: int,
) -> tuple[list[tuple[User, int]], int]:
    filters = []
    if q:
        pattern = f"%{q.strip()}%"
        filters.append(or_(User.name.ilike(pattern), User.email.ilike(pattern)))
    if role:
        filters.append(User.role == role)
    if status:
        filters.append(User.status == status)

    total = await db.scalar(select(func.count()).select_from(User).where(*filters)) or 0

    store_count = (
        select(func.count(UserStore.store_id))
        .where(UserStore.user_id == User.id)
        .correlate(User)
        .scalar_subquery()
    )
    rows = await db.execute(
        select(User, store_count.label("store_count"))
        .where(*filters)
        .order_by(User.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    return [(user, count) for user, count in rows.all()], total

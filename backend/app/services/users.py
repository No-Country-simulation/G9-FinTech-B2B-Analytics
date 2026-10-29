import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Role, TokenType, User, UserStatus, UserStore
from app.schemas.users import UserCreate
from app.services import mail, tokens
from app.services.errors import BusinessError, ConflictError, NotFoundError
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

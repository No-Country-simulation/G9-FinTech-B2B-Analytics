import asyncio
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import generate_opaque_token, hash_password, hash_token, verify_password
from app.models import AccessToken, EmailChange, Role, User, UserSession, UserStatus
from app.schemas.account import (
    ChangeEmailInput,
    ChangePasswordInput,
    DeactivateAccountInput,
    ProfileUpdate,
)
from app.services import mail
from app.services.errors import BusinessError, ConflictError, ForbiddenError
from app.services.mail import TaskQueue


async def update_profile(
    db: AsyncSession,
    user: User,
    data: ProfileUpdate,
) -> User:
    """Updates the name and company of the authenticated user."""

    changes = data.model_dump(exclude_unset=True)

    if not changes:
        raise BusinessError("Debés enviar al menos un dato para actualizar")

    if "name" in changes:
        user.name = changes["name"]

    if "company" in changes:
        user.company = changes["company"]

    await db.commit()
    await db.refresh(user)

    return user


async def change_password(
    db: AsyncSession,
    user: User,
    data: ChangePasswordInput,
) -> None:
    """Changes the password and revokes all of the user's sessions."""

    if user.password_hash is None:
        raise BusinessError("La cuenta no tiene una contraseña configurada")

    is_correct = await asyncio.to_thread(
        verify_password,
        data.current_password,
        user.password_hash,
    )

    if not is_correct:
        raise BusinessError("La contraseña actual es incorrecta")

    is_same = await asyncio.to_thread(
        verify_password,
        data.new_password,
        user.password_hash,
    )

    if is_same:
        raise BusinessError("La nueva contraseña debe ser diferente de la actual")

    user.password_hash = await asyncio.to_thread(
        hash_password,
        data.new_password,
    )

    now = datetime.now(UTC)

    await db.execute(
        update(UserSession)
        .where(
            UserSession.user_id == user.id,
            UserSession.revoked_at.is_(None),
        )
        .values(revoked_at=now)
    )

    await db.commit()


async def request_email_change(
    db: AsyncSession,
    user: User,
    data: ChangeEmailInput,
    queue: TaskQueue,
) -> bool:
    """Requests a change and sends a link to the new email."""

    account = await db.scalar(
        select(User)
        .where(User.id == user.id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )

    if account is None or account.status != UserStatus.ACTIVE:
        raise BusinessError("La cuenta no está activa")

    if account.password_hash is None:
        raise BusinessError("La cuenta no tiene contraseña configurada")

    valid = await asyncio.to_thread(
        verify_password,
        data.current_password,
        account.password_hash,
    )

    if not valid:
        raise BusinessError("La contraseña actual es incorrecta")

    new_email = data.new_email.lower()

    if new_email == account.email.lower():
        raise BusinessError("El nuevo correo debe ser diferente del actual")

    exists = await db.scalar(select(User.id).where(func.lower(User.email) == new_email))

    if exists is not None:
        raise ConflictError("El correo ya está registrado")

    now = datetime.now(UTC)

    # Voids the user's previous requests.
    await db.execute(
        update(EmailChange)
        .where(
            EmailChange.user_id == account.id,
            EmailChange.used_at.is_(None),
        )
        .values(used_at=now)
    )

    token, token_hash = generate_opaque_token()

    db.add(
        EmailChange(
            user_id=account.id,
            new_email=new_email,
            token_hash=token_hash,
            expires_at=now + timedelta(minutes=settings.email_change_token_minutes),
        )
    )

    await db.commit()

    return await mail.enqueue_email_change_confirmation(
        queue,
        account.name,
        new_email,
        token,
    )


async def confirm_email_change(
    db: AsyncSession,
    token: str,
) -> None:
    """Confirms the email and revokes existing sessions."""

    record = await db.scalar(select(EmailChange).where(EmailChange.token_hash == hash_token(token)))

    if record is None:
        raise BusinessError("El enlace no es válido")

    # Lock the user first to serialize their changes.
    user = await db.scalar(
        select(User)
        .where(User.id == record.user_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )

    if user is None or user.status != UserStatus.ACTIVE:
        raise BusinessError("La cuenta no está activa")

    # Re-read the locked record.
    record = await db.scalar(
        select(EmailChange)
        .where(EmailChange.id == record.id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )

    now = datetime.now(UTC)

    if record is None or record.used_at is not None:
        raise BusinessError("El enlace ya fue utilizado o no es válido")

    if record.expires_at <= now:
        raise BusinessError("El enlace de confirmación venció")

    exists = await db.scalar(
        select(User.id).where(
            func.lower(User.email) == record.new_email,
            User.id != user.id,
        )
    )

    if exists is not None:
        raise ConflictError("El correo ya está registrado")

    user.email = record.new_email

    # Invalidates all pending links of the user.
    await db.execute(
        update(EmailChange)
        .where(
            EmailChange.user_id == user.id,
            EmailChange.used_at.is_(None),
        )
        .values(used_at=now)
    )

    # Revokes all sessions.
    await db.execute(
        update(UserSession)
        .where(
            UserSession.user_id == user.id,
            UserSession.revoked_at.is_(None),
        )
        .values(revoked_at=now)
    )

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise ConflictError("El correo ya está registrado") from None


# ---DEACTIVATE ACCOUNT---
async def deactivate_account(
    db: AsyncSession,
    user: User,
    data: DeactivateAccountInput,
) -> None:
    """Deactivates a client account and revokes its access."""

    account = await db.scalar(
        select(User)
        .where(User.id == user.id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )

    if account is None or account.status != UserStatus.ACTIVE:
        raise BusinessError("La cuenta no está activa")

    if account.role != Role.CLIENT:
        raise ForbiddenError("Esta operación solo está disponible para clientes")

    if account.password_hash is None:
        raise BusinessError("La cuenta no tiene contraseña configurada")

    valid = await asyncio.to_thread(
        verify_password,
        data.current_password,
        account.password_hash,
    )

    if not valid:
        raise BusinessError("La contraseña actual es incorrecta")

    now = datetime.now(UTC)

    # Change the account status.
    account.status = UserStatus.DEACTIVATED

    # Revoke all its sessions.
    await db.execute(
        update(UserSession)
        .where(
            UserSession.user_id == account.id,
            UserSession.revoked_at.is_(None),
        )
        .values(revoked_at=now)
    )

    # Invalidate pending access tokens.
    await db.execute(
        update(AccessToken)
        .where(
            AccessToken.user_id == account.id,
            AccessToken.used_at.is_(None),
        )
        .values(used_at=now)
    )

    # Invalidate pending email change requests.
    await db.execute(
        update(EmailChange)
        .where(
            EmailChange.user_id == account.id,
            EmailChange.used_at.is_(None),
        )
        .values(used_at=now)
    )

    await db.commit()

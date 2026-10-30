import uuid
from typing import Annotated

from fastapi import APIRouter, Query, status

from app.api.deps import CurrentAdmin, DbSession, Queue
from app.models import Role, User, UserStatus
from app.schemas.common import Message, Page
from app.schemas.stores import AssignStoreInput, StoreOutput
from app.schemas.users import (
    UserCreate,
    UserCreatedOutput,
    UserEmailChangedOutput,
    UserEmailInput,
    UserOutput,
)
from app.services import stores, users

router = APIRouter(prefix="/admin/users", tags=["admin · users"])


def _output(user: User, store_count: int) -> UserOutput:
    return UserOutput.model_validate(user).model_copy(update={"store_count": store_count})


@router.get("", response_model=Page[UserOutput])
async def list_users(
    db: DbSession,
    _admin: CurrentAdmin,
    q: Annotated[str | None, Query(max_length=100, description="Searches name and email")] = None,
    role: Role | None = None,
    user_status: Annotated[UserStatus | None, Query(alias="status")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> Page[UserOutput]:
    rows, total = await users.list_users(
        db, q=q, role=role, status=user_status, page=page, size=size
    )
    return Page[UserOutput](
        items=[_output(u, c) for u, c in rows], total=total, page=page, size=size
    )


@router.post("", response_model=UserCreatedOutput, status_code=status.HTTP_201_CREATED)
async def create_user(
    data: UserCreate, db: DbSession, queue: Queue, _admin: CurrentAdmin
) -> UserCreatedOutput:
    user, queued = await users.create_user(db, queue, data)
    return UserCreatedOutput(user=_output(user, 0), email_queued=queued)


@router.get("/{user_id}", response_model=UserOutput)
async def get_user(user_id: uuid.UUID, db: DbSession, _admin: CurrentAdmin) -> UserOutput:
    user = await users.get_user(db, user_id)
    return _output(user, await users.count_stores(db, user_id))


@router.post(
    "/{user_id}/resend-access", response_model=Message, status_code=status.HTTP_202_ACCEPTED
)
async def resend_access(
    user_id: uuid.UUID, db: DbSession, queue: Queue, _admin: CurrentAdmin
) -> Message:
    queued = await users.resend_access(db, queue, user_id)
    if not queued:
        return Message(message="No pudimos enviar el correo. Probá de nuevo en unos minutos.")
    return Message(message="Enviamos un nuevo correo de acceso.")


@router.post(
    "/{user_id}/password-reset", response_model=Message, status_code=status.HTTP_202_ACCEPTED
)
async def send_password_reset(
    user_id: uuid.UUID, db: DbSession, queue: Queue, _admin: CurrentAdmin
) -> Message:
    queued = await users.send_password_reset(db, queue, user_id)
    if not queued:
        return Message(message="No pudimos enviar el correo. Probá de nuevo en unos minutos.")
    return Message(message="Enviamos un enlace para restablecer la contraseña.")


@router.patch("/{user_id}/email", response_model=UserEmailChangedOutput)
async def change_email(
    user_id: uuid.UUID, data: UserEmailInput, db: DbSession, queue: Queue, _admin: CurrentAdmin
) -> UserEmailChangedOutput:
    user, queued = await users.change_email(db, queue, user_id, data.email)
    return UserEmailChangedOutput(
        user=_output(user, await users.count_stores(db, user_id)), email_queued=queued
    )


@router.post("/{user_id}/block", response_model=UserOutput)
async def block_user(user_id: uuid.UUID, db: DbSession, admin: CurrentAdmin) -> UserOutput:
    user = await users.block_user(db, user_id, admin.id)
    return _output(user, await users.count_stores(db, user_id))


@router.post("/{user_id}/unblock", response_model=UserOutput)
async def unblock_user(user_id: uuid.UUID, db: DbSession, _admin: CurrentAdmin) -> UserOutput:
    user = await users.unblock_user(db, user_id)
    return _output(user, await users.count_stores(db, user_id))


@router.post("/{user_id}/deactivate", response_model=UserOutput)
async def deactivate_user(user_id: uuid.UUID, db: DbSession, admin: CurrentAdmin) -> UserOutput:
    user = await users.deactivate_user(db, user_id, admin.id)
    return _output(user, await users.count_stores(db, user_id))


@router.get("/{user_id}/stores", response_model=list[StoreOutput])
async def list_user_stores(
    user_id: uuid.UUID, db: DbSession, _admin: CurrentAdmin
) -> list[StoreOutput]:
    await users.get_user(db, user_id)  # 404 if it does not exist
    return [StoreOutput.model_validate(s) for s in await stores.stores_of_user(db, user_id)]


@router.post(
    "/{user_id}/stores", response_model=list[StoreOutput], status_code=status.HTTP_201_CREATED
)
async def assign_store(
    user_id: uuid.UUID, data: AssignStoreInput, db: DbSession, admin: CurrentAdmin
) -> list[StoreOutput]:
    await stores.assign_store(db, user_id, data.store_id, admin.id)
    return [StoreOutput.model_validate(s) for s in await stores.stores_of_user(db, user_id)]


@router.delete("/{user_id}/stores/{store_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_store(
    user_id: uuid.UUID, store_id: uuid.UUID, db: DbSession, _admin: CurrentAdmin
) -> None:
    await stores.remove_store(db, user_id, store_id)

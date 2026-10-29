from fastapi import APIRouter, HTTPException, Response, status

from app.api.deps import CurrentUser, DbSession, Queue
from app.schemas.account import (
    ChangeEmailInput,
    ChangePasswordInput,
    DeactivateAccountInput,
    ProfileOutput,
    ProfileUpdate,
)
from app.schemas.auth import TokenInput
from app.schemas.common import Message
from app.services import account

router = APIRouter(
    prefix="/account",
    tags=["account"],
)


@router.patch(
    "/profile",
    response_model=ProfileOutput,
    summary="Edit my profile",
    description="Lets the authenticated user update their name and their company name.",
)
async def edit_my_profile(
    data: ProfileUpdate,
    user: CurrentUser,
    db: DbSession,
) -> ProfileOutput:

    updated_user = await account.update_profile(
        db,
        user,
        data,
    )

    return ProfileOutput.model_validate(updated_user)


@router.patch(
    "/password",
    response_model=Message,
    summary="Change my password",
    description=(
        "Lets the authenticated user change their password and revokes their active sessions."
    ),  # noqa: E501
)
async def change_my_password(
    data: ChangePasswordInput,
    user: CurrentUser,
    db: DbSession,
    response: Response,
) -> Message:
    await account.change_password(
        db,
        user,
        data,
    )

    response.delete_cookie(
        "ps_refresh",
        path="/api/v1/auth",
    )

    return Message(message=("Contraseña actualizada correctamente. Iniciá sesión nuevamente."))


@router.post(
    "/email",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=Message,
    summary="Request an email change",
    responses={
        400: {"description": "Invalid request"},
        401: {"description": "Not authenticated"},
        409: {"description": "Email already registered"},
        503: {"description": "The email could not be queued"},
    },
)
async def request_my_email_change(
    data: ChangeEmailInput,
    user: CurrentUser,
    db: DbSession,
    queue: Queue,
) -> Message:
    queued = await account.request_email_change(
        db,
        user,
        data,
        queue,
    )

    if not queued:
        raise HTTPException(
            status_code=503,
            detail="No pudimos enviar el correo. Intentá nuevamente.",
        )

    return Message(message="Enviamos un enlace de confirmación al nuevo correo.")


@router.post(
    "/email/confirm",
    response_model=Message,
    summary="Confirm an email change",
    responses={
        400: {"description": "Invalid, used or expired token"},
        409: {"description": "Email already registered"},
    },
)
async def confirm_my_email(
    data: TokenInput,
    db: DbSession,
    response: Response,
) -> Message:
    await account.confirm_email_change(
        db,
        data.token,
    )

    response.delete_cookie(
        "ps_refresh",
        path="/api/v1/auth",
    )

    return Message(message="Correo actualizado. Iniciá sesión nuevamente.")


# ---DEACTIVATE ACCOUNT---


@router.delete(
    "",
    response_model=Message,
    summary="Deactivate my account",
    description=(
        "Lets the authenticated client request a logical deactivation "
        "of their account. Requires the current password and an "
        "explicit confirmation. Revokes sessions and pending tokens."
    ),
    responses={
        400: {"description": "Wrong password or invalid account"},
        401: {"description": "Not authenticated"},
        403: {"description": "Operation not allowed"},
        422: {"description": "Validation error"},
    },
)
async def deactivate_my_account(
    data: DeactivateAccountInput,
    user: CurrentUser,
    db: DbSession,
    response: Response,
) -> Message:

    await account.deactivate_account(
        db,
        user,
        data,
    )

    response.delete_cookie(
        "ps_refresh",
        path="/api/v1/auth",
    )

    return Message(
        message=("Tu cuenta fue dada de baja correctamente. Se cerraron todas tus sesiones.")
    )

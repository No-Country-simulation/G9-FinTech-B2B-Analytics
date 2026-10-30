from fastapi import APIRouter, HTTPException, Request, Response, status

from app.api.deps import CurrentUser, DbSession, Queue
from app.core.config import settings
from app.schemas.auth import (
    CurrentUserOutput,
    EmailInput,
    LoginInput,
    SetPasswordInput,
    TokenInput,
    TokenOutput,
    TokenStatusOutput,
)
from app.schemas.common import Message
from app.services import authentication, stores, tokens, users

router = APIRouter(prefix="/auth", tags=["auth"])

COOKIE_REFRESH = "ps_refresh"
COOKIE_PATH = "/api/v1/auth"


def _save_refresh(response: Response, refresh: str) -> None:
    response.set_cookie(
        COOKIE_REFRESH,
        refresh,
        httponly=True,
        secure=settings.secure_cookies,
        samesite="lax",
        max_age=settings.session_max_hours * 3600,
        path=COOKIE_PATH,
    )


def _token_output(access: str, role: str) -> TokenOutput:
    return TokenOutput(
        access_token=access, expires_in=settings.access_token_minutes * 60, role=role
    )


@router.post("/login", response_model=TokenOutput)
async def login(
    data: LoginInput, request: Request, response: Response, db: DbSession
) -> TokenOutput:
    user = await authentication.authenticate(db, data.email, data.password)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Correo o contraseña incorrectos")
    access, refresh = await authentication.open_session(db, user, request.headers.get("user-agent"))
    _save_refresh(response, refresh)
    return _token_output(access, user.role)


@router.post("/refresh", response_model=TokenOutput)
async def refresh(request: Request, response: Response, db: DbSession) -> TokenOutput:
    token = request.cookies.get(COOKIE_REFRESH)
    result = await authentication.refresh_session(db, token) if token else None
    if result is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Tu sesión venció. Ingresá de nuevo.")
    user, access, new_refresh = result
    _save_refresh(response, new_refresh)
    return _token_output(access, user.role)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: Request, response: Response, user: CurrentUser, db: DbSession) -> None:
    await authentication.close_session(db, request.state.session_id)
    response.delete_cookie(COOKIE_REFRESH, path=COOKIE_PATH)


@router.get("/me", response_model=CurrentUserOutput)
async def me(user: CurrentUser, db: DbSession) -> CurrentUserOutput:
    store_ids = [s.id for s in await stores.stores_of_user(db, user.id)]
    return CurrentUserOutput(
        id=user.id,
        name=user.name,
        company=user.company,
        email=user.email,
        role=user.role,
        store_ids=store_ids,
    )


@router.post("/token/verify", response_model=TokenStatusOutput)
async def verify_token(data: TokenInput, db: DbSession) -> TokenStatusOutput:
    token_state, token_type, owner = await tokens.token_status(db, data.token)
    return TokenStatusOutput(
        status=token_state,
        type=token_type,
        email=owner.email if owner else None,
        company=owner.company if owner else None,
    )


@router.post("/password", response_model=Message)
async def set_password(data: SetPasswordInput, db: DbSession) -> Message:
    await tokens.consume_token(db, data.token, data.password)
    return Message(message="Tu contraseña quedó guardada. Ya podés ingresar.")


@router.post("/recover", response_model=Message, status_code=status.HTTP_202_ACCEPTED)
async def recover(data: EmailInput, db: DbSession, queue: Queue) -> Message:
    await users.request_password_reset(db, queue, data.email)
    return Message(
        message=(
            "Si el correo corresponde a una cuenta, "
            "te enviamos un enlace para restablecer la contraseña."
        )
    )

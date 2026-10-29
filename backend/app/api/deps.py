import uuid
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import decode_access_token
from app.models import Role, User, UserSession, UserStatus
from app.services.mail import TaskQueue

DbSession = Annotated[AsyncSession, Depends(get_session)]

_bearer = HTTPBearer(auto_error=False)


def get_queue(request: Request) -> TaskQueue:
    return request.app.state.arq


Queue = Annotated[TaskQueue, Depends(get_queue)]


async def get_current_user(
    request: Request,
    db: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> User:
    unauthenticated = HTTPException(
        status.HTTP_401_UNAUTHORIZED, "No autenticado", headers={"WWW-Authenticate": "Bearer"}
    )
    if credentials is None:
        raise unauthenticated
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = uuid.UUID(payload["sub"])
        session_id = uuid.UUID(payload["sid"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise unauthenticated from None

    user = await db.scalar(
        select(User)
        .join(UserSession, UserSession.user_id == User.id)
        .where(
            User.id == user_id,
            UserSession.id == session_id,
            UserSession.revoked_at.is_(None),
        )
    )
    if user is None or user.status != UserStatus.ACTIVE:
        raise unauthenticated

    request.state.session_id = session_id  # used by /auth/logout
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def require_admin(user: CurrentUser) -> User:
    if user.role != Role.ADMIN:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "No tenés permisos para esta acción")
    return user


CurrentAdmin = Annotated[User, Depends(require_admin)]

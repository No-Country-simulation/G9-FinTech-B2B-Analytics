import uuid
from typing import Literal

from pydantic import BaseModel, EmailStr, Field

from app.models import Role, TokenType
from app.schemas.common import Password


class LoginInput(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class TokenOutput(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    role: Role


class EmailInput(BaseModel):
    email: EmailStr


class TokenInput(BaseModel):
    token: str = Field(min_length=20, max_length=200)


class TokenStatusOutput(BaseModel):
    status: Literal["valid", "expired", "invalid"]
    type: TokenType | None = None
    # Only for a valid link.
    email: str | None = None
    company: str | None = None


class SetPasswordInput(TokenInput):
    password: Password


class CurrentUserOutput(BaseModel):
    id: uuid.UUID
    name: str
    company: str
    email: str
    role: Role
    store_ids: list[uuid.UUID]

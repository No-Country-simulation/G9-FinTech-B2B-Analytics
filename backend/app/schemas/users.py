import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models import Role, UserStatus


class UserCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=2, max_length=120)
    company: str = Field(min_length=2, max_length=160)
    email: EmailStr
    role: Role = Role.CLIENT


class UserOutput(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    company: str
    email: str
    role: Role
    status: UserStatus
    last_access_at: datetime | None
    created_at: datetime
    store_count: int = 0


class UserCreatedOutput(BaseModel):
    user: UserOutput
    email_queued: bool


class UserEmailInput(BaseModel):
    email: EmailStr


class UserEmailChangedOutput(BaseModel):
    user: UserOutput
    email_queued: bool

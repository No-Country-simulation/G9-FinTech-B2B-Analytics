from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
)

from app.schemas.common import Password


class ProfileUpdate(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=120,
    )

    company: str | None = Field(
        default=None,
        min_length=2,
        max_length=160,
    )

    @field_validator("name", "company")
    @classmethod
    def reject_nulls(cls, value: str | None) -> str:
        if value is None:
            raise ValueError("El campo no puede ser null")
        return value


class ProfileOutput(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    company: str


class ChangePasswordInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    current_password: str = Field(
        min_length=1,
        max_length=128,
    )

    new_password: Password = Field(
        max_length=128,
    )


class ChangeEmailInput(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    new_email: EmailStr = Field(max_length=254)
    current_password: str = Field(
        min_length=1,
        max_length=128,
    )


class DeactivateAccountInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    current_password: str = Field(
        min_length=1,
        max_length=128,
    )

    # Typed by the user in the UI, so it stays in Spanish.
    confirmation: Literal["ELIMINAR MI CUENTA"]

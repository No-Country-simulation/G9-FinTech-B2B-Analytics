from typing import Annotated

from pydantic import AfterValidator, BaseModel


class Page[T](BaseModel):
    items: list[T]
    total: int
    page: int
    size: int


class Message(BaseModel):
    message: str


def validate_password(value: str) -> str:
    if len(value) < 8 or not any(c.isupper() for c in value) or not any(c.isdigit() for c in value):
        raise ValueError(
            "La contraseña debe tener al menos 8 caracteres, una mayúscula y un número"
        )
    return value


Password = Annotated[str, AfterValidator(validate_password)]

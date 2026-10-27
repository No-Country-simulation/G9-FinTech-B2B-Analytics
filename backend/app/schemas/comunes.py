from typing import Annotated

from pydantic import AfterValidator, BaseModel


class Pagina[T](BaseModel):
    items: list[T]
    total: int
    pagina: int
    tamano: int


class Mensaje(BaseModel):
    mensaje: str


def validar_password(valor: str) -> str:
    if len(valor) < 8 or not any(c.isupper() for c in valor) or not any(c.isdigit() for c in valor):
        raise ValueError(
            "La contraseña debe tener al menos 8 caracteres, una mayúscula y un número"
        )
    return valor


Password = Annotated[str, AfterValidator(validar_password)]

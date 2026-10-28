from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
)

from app.schemas.comunes import Password


class DatosCuentaActualizar(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    nombre: str | None = Field(
        default=None,
        min_length=2,
        max_length=120,
    )

    empresa: str | None = Field(
        default=None,
        min_length=2,
        max_length=160,
    )

    @field_validator("nombre", "empresa")
    @classmethod
    def no_permitir_nulos(cls, valor: str | None) -> str:
        if valor is None:
            raise ValueError("El campo no puede ser null")
        return valor


class DatosCuentaSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    nombre: str
    empresa: str


class CambiarContrasenaEntrada(BaseModel):
    model_config = ConfigDict(extra="forbid")

    contrasena_actual: str = Field(
        min_length=1,
        max_length=128,
    )

    contrasena_nueva: Password = Field(
        max_length=128,
    )

class CambiarCorreoEntrada(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    nuevo_correo: EmailStr = Field(max_length=254)
    contrasena_actual: str = Field(
        min_length=1,
        max_length=128,
    )
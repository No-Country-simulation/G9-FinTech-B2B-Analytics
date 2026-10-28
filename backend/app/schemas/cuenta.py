from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


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
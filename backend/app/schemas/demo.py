import uuid
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from pydantic import AwareDatetime, BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models import TipoOrganizacion

ZONA_AR = ZoneInfo("America/Argentina/Buenos_Aires")


class SolicitudDemoEntrada(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    empresa: str = Field(min_length=2, max_length=160)
    nombre: str = Field(min_length=2, max_length=120)
    correo: EmailStr
    tipo_organizacion: TipoOrganizacion
    comentario: str | None = Field(default=None, max_length=1000)
    fecha_preferida: AwareDatetime

    @field_validator("fecha_preferida")
    @classmethod
    def horario_laboral(cls, valor: datetime) -> datetime:
        if valor <= datetime.now(UTC):
            raise ValueError("La fecha tiene que ser futura")
        local = valor.astimezone(ZONA_AR)
        if local.weekday() >= 5 or not 9 <= local.hour < 18:
            raise ValueError(
                "Elegí un horario de lunes a viernes, entre las 9 y las 18 (hora de Argentina)"
            )
        return valor


class SolicitudDemoSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    empresa: str
    nombre: str
    correo: str
    tipo_organizacion: TipoOrganizacion
    comentario: str | None
    fecha_preferida: datetime
    creada_en: datetime

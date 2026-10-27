import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models import EstadoUsuario, Rol


class UsuarioCrear(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    nombre: str = Field(min_length=2, max_length=120)
    empresa: str = Field(min_length=2, max_length=160)
    correo: EmailStr
    rol: Rol = Rol.CLIENTE


class UsuarioSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nombre: str
    empresa: str
    correo: str
    rol: Rol
    estado: EstadoUsuario
    ultimo_acceso: datetime | None
    creado_en: datetime
    cantidad_tiendas: int = 0


class UsuarioCreadoSalida(BaseModel):
    usuario: UsuarioSalida
    correo_encolado: bool

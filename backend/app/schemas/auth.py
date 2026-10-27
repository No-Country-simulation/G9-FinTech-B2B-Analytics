import uuid
from typing import Literal

from pydantic import BaseModel, EmailStr, Field

from app.models import Rol, TipoToken
from app.schemas.comunes import Password


class LoginEntrada(BaseModel):
    correo: EmailStr
    password: str = Field(min_length=1, max_length=128)


class TokenSalida(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expira_en: int  # segundos
    rol: Rol


class CorreoEntrada(BaseModel):
    correo: EmailStr


class TokenEntrada(BaseModel):
    token: str = Field(min_length=20, max_length=200)


class EstadoTokenSalida(BaseModel):
    estado: Literal["valido", "vencido", "invalido"]
    tipo: TipoToken | None = None


class DefinirPasswordEntrada(TokenEntrada):
    password: Password


class UsuarioActualSalida(BaseModel):
    id: uuid.UUID
    nombre: str
    empresa: str
    correo: str
    rol: Rol
    tienda_ids: list[uuid.UUID]

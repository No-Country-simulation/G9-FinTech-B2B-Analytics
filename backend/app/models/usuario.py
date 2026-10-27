from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.enums import EstadoUsuario, Rol
from app.models.mixins import ConFechas, ConId, columna_enum


class Usuario(ConId, ConFechas, Base):
    __tablename__ = "usuarios"

    nombre: Mapped[str] = mapped_column(String(120))
    empresa: Mapped[str] = mapped_column(String(160))
    correo: Mapped[str] = mapped_column(String(254), unique=True)
    password_hash: Mapped[str | None] = mapped_column(String(255))
    rol: Mapped[Rol] = mapped_column(
        columna_enum(Rol, "rol_usuario"),
        default=Rol.CLIENTE,
        server_default=Rol.CLIENTE.value,
        index=True,
    )
    estado: Mapped[EstadoUsuario] = mapped_column(
        columna_enum(EstadoUsuario, "estado_usuario"),
        default=EstadoUsuario.PENDIENTE,
        server_default=EstadoUsuario.PENDIENTE.value,
        index=True,
    )
    ultimo_acceso: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

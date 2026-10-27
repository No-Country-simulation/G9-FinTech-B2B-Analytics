import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func, true
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.enums import Rubro
from app.models.mixins import ConFechas, ConId, columna_enum


class Tienda(ConId, ConFechas, Base):
    __tablename__ = "tiendas"

    nombre: Mapped[str] = mapped_column(String(120))
    slug: Mapped[str] = mapped_column(String(60), unique=True)
    url_base: Mapped[str] = mapped_column(String(255))
    rubro: Mapped[Rubro] = mapped_column(columna_enum(Rubro, "rubro_tienda"))
    scraper_clave: Mapped[str] = mapped_column(String(60), unique=True)
    activa: Mapped[bool] = mapped_column(default=True, server_default=true())


class UsuarioTienda(Base):
    __tablename__ = "usuario_tienda"

    usuario_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"), primary_key=True
    )
    tienda_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tiendas.id", ondelete="RESTRICT"), primary_key=True, index=True
    )
    asignada_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    asignada_por: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL")
    )

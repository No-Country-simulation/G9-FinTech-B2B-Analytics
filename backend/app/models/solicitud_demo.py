from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.enums import TipoOrganizacion
from app.models.mixins import ConId, columna_enum


class SolicitudDemo(ConId, Base):
    __tablename__ = "solicitudes_demo"

    empresa: Mapped[str] = mapped_column(String(160))
    nombre: Mapped[str] = mapped_column(String(120))
    correo: Mapped[str] = mapped_column(String(254))
    tipo_organizacion: Mapped[TipoOrganizacion] = mapped_column(
        columna_enum(TipoOrganizacion, "tipo_organizacion")
    )
    comentario: Mapped[str | None] = mapped_column(Text)
    fecha_preferida: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    creada_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

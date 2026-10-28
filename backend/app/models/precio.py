import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, false, true
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Precio(Base):
    """Hypertable por capturado_en. La PK incluye la columna de tiempo."""

    __tablename__ = "precios"

    publicacion_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("publicaciones.id", ondelete="CASCADE"), primary_key=True
    )
    capturado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    precio_local: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    precio_tachado: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    precio_regular: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    es_promo: Mapped[bool] = mapped_column(default=False, server_default=false())
    disponible: Mapped[bool] = mapped_column(default=True, server_default=true())
    gramaje: Mapped[Decimal | None] = mapped_column(Numeric(12, 3))
    unidad: Mapped[str | None] = mapped_column(String(10))
    # Snapshot de la cotización vigente al capturar (sin FK: no se puede apuntar a una hypertable)
    tc_oficial: Mapped[Decimal | None] = mapped_column(Numeric(14, 4))
    tc_blue: Mapped[Decimal | None] = mapped_column(Numeric(14, 4))
    cotizado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    precio_usd_oficial: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    precio_usd_blue: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))

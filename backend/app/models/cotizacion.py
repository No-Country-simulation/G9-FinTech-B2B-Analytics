from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.enums import TipoCotizacion
from app.models.mixins import columna_enum


class Cotizacion(Base):
    """Hypertable por cotizado_en. La PK incluye la columna de tiempo (requisito de TimescaleDB)."""

    __tablename__ = "cotizaciones"

    fuente: Mapped[str] = mapped_column(String(30), primary_key=True)
    tipo: Mapped[TipoCotizacion] = mapped_column(
        columna_enum(TipoCotizacion, "tipo_cotizacion"), primary_key=True
    )
    cotizado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    compra: Mapped[Decimal | None] = mapped_column(Numeric(14, 4))
    venta: Mapped[Decimal] = mapped_column(Numeric(14, 4))
    fecha_fuente: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

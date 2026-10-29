from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.enums import RateType
from app.models.mixins import enum_column


class ExchangeRate(Base):
    """Hypertable by quoted_at. The PK includes the time column (TimescaleDB requirement)."""

    __tablename__ = "exchange_rates"

    source: Mapped[str] = mapped_column(String(30), primary_key=True)
    type: Mapped[RateType] = mapped_column(enum_column(RateType, "rate_type"), primary_key=True)
    quoted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    buy: Mapped[Decimal | None] = mapped_column(Numeric(14, 4))
    sell: Mapped[Decimal] = mapped_column(Numeric(14, 4))
    source_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

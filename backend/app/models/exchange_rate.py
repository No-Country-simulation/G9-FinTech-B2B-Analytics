import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.price_fx_conversion import PriceFxConversion

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Index,
    Numeric,
    String,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class ExchangeRate(Base):
    __tablename__ = "exchange_rates"

    __table_args__ = (
        CheckConstraint(
            "rate_type IN ('OFICIAL', 'BLUE')",
            name="ck_exchange_rates_rate_type",
        ),
        CheckConstraint(
            "buy_price_ars > 0",
            name="ck_exchange_rates_buy_price_positive",
        ),
        CheckConstraint(
            "sell_price_ars > 0",
            name="ck_exchange_rates_sell_price_positive",
        ),
        Index(
            "ix_exchange_rates_type_fetched_at",
            "rate_type",
            "fetched_at",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    rate_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    buy_price_ars: Mapped[Decimal] = mapped_column(
        Numeric(14, 4),
        nullable=False,
    )

    sell_price_ars: Mapped[Decimal] = mapped_column(
        Numeric(14, 4),
        nullable=False,
    )

    quoted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        primary_key=True,
        nullable=False,
        server_default=func.now(),
    )

    source: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )
    
    fx_conversions: Mapped[list["PriceFxConversion"]] = relationship(
        back_populates="exchange_rate",
    )
import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKeyConstraint,
    Index,
    Numeric,
    String,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.price_snapshot import PriceSnapshot
    from app.models.exchange_rate import ExchangeRate


class PriceFxConversion(Base):
    __tablename__ = "price_fx_conversions"

    __table_args__ = (
        ForeignKeyConstraint(
            ["price_snapshot_id", "snapshot_captured_at"],
            ["price_snapshots.id", "price_snapshots.captured_at"],
            name="fk_price_fx_conversions_price_snapshot",
        ),
        ForeignKeyConstraint(
            ["exchange_rate_id", "exchange_rate_fetched_at"],
            ["exchange_rates.id", "exchange_rates.fetched_at"],
            name="fk_price_fx_conversions_exchange_rate",
        ),
        CheckConstraint(
            "rate_type IN ('OFICIAL', 'BLUE')",
            name="ck_price_fx_conversions_rate_type",
        ),
        CheckConstraint(
            "rate_used_ars_per_usd > 0",
            name="ck_price_fx_conversions_rate_positive",
        ),
        CheckConstraint(
            "current_price_usd >= 0",
            name="ck_price_fx_conversions_current_usd",
        ),
        CheckConstraint(
            "regular_price_usd IS NULL OR regular_price_usd >= 0",
            name="ck_price_fx_conversions_regular_usd",
        ),
        Index(
            "ix_price_fx_conversions_exchange_rate",
            "exchange_rate_id",
            "exchange_rate_fetched_at",
        ),
    )

    price_snapshot_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
    )

    snapshot_captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        primary_key=True,
    )

    rate_type: Mapped[str] = mapped_column(
        String(20),
        primary_key=True,
    )

    exchange_rate_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        nullable=False,
    )

    exchange_rate_fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    rate_used_ars_per_usd: Mapped[Decimal] = mapped_column(
        Numeric(14, 4),
        nullable=False,
    )

    current_price_usd: Mapped[Decimal] = mapped_column(
        Numeric(18, 6),
        nullable=False,
    )

    regular_price_usd: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 6),
        nullable=True,
    )

    converted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    price_snapshot: Mapped["PriceSnapshot"] = relationship(
        back_populates="fx_conversions",
    )

    exchange_rate: Mapped["ExchangeRate"] = relationship(
        back_populates="fx_conversions",
    )
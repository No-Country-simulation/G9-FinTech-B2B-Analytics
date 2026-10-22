import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.store_product import StoreProduct
    from app.models.scraper_run import ScraperRun
    from app.models.price_fx_conversion import PriceFxConversion


class PriceSnapshot(Base):
    __tablename__ = "price_snapshots"

    __table_args__ = (
        CheckConstraint(
            "current_price_ars >= 0",
            name="ck_price_snapshots_current_price",
        ),
        CheckConstraint(
            "regular_price_ars IS NULL OR regular_price_ars >= 0",
            name="ck_price_snapshots_regular_price",
        ),
        CheckConstraint(
            "observed_quantity IS NULL OR observed_quantity > 0",
            name="ck_price_snapshots_observed_quantity",
        ),
        Index(
            "ix_price_snapshots_product_captured_at",
            "store_product_id",
            "captured_at",
        ),
        Index(
            "ix_price_snapshots_captured_at",
            "captured_at",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    store_product_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("store_products.id"),
        nullable=False,
    )

    scraper_run_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("scraper_runs.id"),
        nullable=True,
        index=True,
    )

    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        primary_key=True,
        nullable=False,
    )

    current_price_ars: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )

    regular_price_ars: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 2),
        nullable=True,
    )

    is_promotion: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    promotion_label: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    in_stock: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    observed_quantity: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 3),
        nullable=True,
    )

    observed_unit: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    store_product: Mapped["StoreProduct"] = relationship(
        back_populates="price_snapshots",
    )

    scraper_run: Mapped["ScraperRun | None"] = relationship(
        back_populates="price_snapshots",
    )
    
    fx_conversions: Mapped[list["PriceFxConversion"]] = relationship(
        back_populates="price_snapshot",
    )
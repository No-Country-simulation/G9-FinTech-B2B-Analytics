import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    Uuid,
    func,
    text,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.store import Store
    from app.models.canonical_product import CanonicalProduct
    from app.models.price_snapshot import PriceSnapshot
    from app.models.triggered_alert import TriggeredAlert


class StoreProduct(Base):
    __tablename__ = "store_products"

    __table_args__ = (
        CheckConstraint(
            "match_status IN ('CONFIRMADO', 'REVISAR', 'SEPARADO')",
            name="ck_store_products_match_status",
        ),
        CheckConstraint(
            "match_confidence >= 0 AND match_confidence <= 100",
            name="ck_store_products_match_confidence",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    store_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("stores.id"),
        nullable=False,
        index=True,
    )

    canonical_product_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("canonical_products.id"),
        nullable=True,
        index=True,
    )

    raw_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    raw_sku: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
    )

    url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    match_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default=text("'REVISAR'"),
    )

    match_confidence: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=true(),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    store: Mapped["Store"] = relationship(
        back_populates="products",
    )

    canonical_product: Mapped["CanonicalProduct | None"] = relationship(
        back_populates="store_products",
    )
    
    price_snapshots: Mapped[list["PriceSnapshot"]] = relationship(
        back_populates="store_product",
    )
    
    triggered_alerts: Mapped[list["TriggeredAlert"]] = relationship(
        back_populates="store_product",
    )
import uuid
from datetime import datetime
from decimal import Decimal

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.store_product import StoreProduct
    from app.models.category import Category
    from app.models.basket_item import BasketItem
    from app.models.alert_rule import AlertRule
    from app.models.triggered_alert import TriggeredAlert

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Uuid,
    func,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class CanonicalProduct(Base):
    __tablename__ = "canonical_products"

    __table_args__ = (
        CheckConstraint(
            "standard_quantity > 0",
            name="ck_canonical_products_quantity_positive",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    category_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("categories.id"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    brand: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
    )

    model: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
    )

    standard_quantity: Mapped[Decimal] = mapped_column(
        Numeric(12, 3),
        nullable=False,
    )

    standard_unit: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
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

    category: Mapped["Category"] = relationship(
        back_populates="products",
    )
    
    store_products: Mapped[list["StoreProduct"]] = relationship(
        back_populates="canonical_product",
    )
    
    basket_items: Mapped[list["BasketItem"]] = relationship(
        back_populates="canonical_product",
    )
    
    alert_rules: Mapped[list["AlertRule"]] = relationship(
        back_populates="canonical_product",
    )
    
    triggered_alerts: Mapped[list["TriggeredAlert"]] = relationship(
        back_populates="canonical_product",
    )
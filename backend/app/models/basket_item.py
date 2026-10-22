import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.basket import Basket
    from app.models.canonical_product import CanonicalProduct


class BasketItem(Base):
    __tablename__ = "basket_items"

    __table_args__ = (
        CheckConstraint(
            "quantity > 0",
            name="ck_basket_items_quantity_positive",
        ),
    )

    basket_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("baskets.id"),
        primary_key=True,
        nullable=False,
    )

    canonical_product_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("canonical_products.id"),
        primary_key=True,
        nullable=False,
        index=True,
    )

    quantity: Mapped[Decimal] = mapped_column(
        Numeric(12, 3),
        nullable=False,
    )

    weight: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 6),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    basket: Mapped["Basket"] = relationship(
        back_populates="items",
    )

    canonical_product: Mapped["CanonicalProduct"] = relationship(
        back_populates="basket_items",
    )
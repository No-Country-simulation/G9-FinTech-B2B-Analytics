import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    Uuid,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.alert_rule import AlertRule
    from app.models.canonical_product import CanonicalProduct
    from app.models.store_product import StoreProduct
    from app.models.commercial_event import CommercialEvent


class TriggeredAlert(Base):
    __tablename__ = "triggered_alerts"

    __table_args__ = (
        Index(
            "ix_triggered_alerts_user_status_detected_at",
            "user_id",
            "status",
            "detected_at",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )

    rule_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("alert_rules.id"),
        nullable=True,
        index=True,
    )

    alert_type: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )

    canonical_product_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("canonical_products.id"),
        nullable=True,
        index=True,
    )

    store_product_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("store_products.id"),
        nullable=True,
        index=True,
    )

    commercial_event_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("commercial_events.id"),
        nullable=True,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(180),
        nullable=False,
    )

    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    details: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
    )

    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    dedupe_key: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )

    user: Mapped["User"] = relationship(
        back_populates="triggered_alerts",
    )

    rule: Mapped["AlertRule | None"] = relationship(
        back_populates="triggered_alerts",
    )

    canonical_product: Mapped["CanonicalProduct | None"] = relationship(
        back_populates="triggered_alerts",
    )

    store_product: Mapped["StoreProduct | None"] = relationship(
        back_populates="triggered_alerts",
    )

    commercial_event: Mapped["CommercialEvent | None"] = relationship(
        back_populates="triggered_alerts",
    )
import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Uuid,
    func,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.canonical_product import CanonicalProduct
    from app.models.commercial_event import CommercialEvent
    from app.models.triggered_alert import TriggeredAlert


class AlertRule(Base):
    __tablename__ = "alert_rules"

    __table_args__ = (
        CheckConstraint(
            "rule_type IN ('PRICE_VS_DEVALUATION', 'COMMERCIAL_EVENT')",
            name="ck_alert_rules_rule_type",
        ),
        CheckConstraint(
            "fx_rate_type IN ('OFICIAL', 'BLUE')",
            name="ck_alert_rules_fx_rate_type",
        ),
        CheckConstraint(
            "period_days IS NULL OR period_days > 0",
            name="ck_alert_rules_period_days",
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
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    rule_type: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )

    canonical_product_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("canonical_products.id"),
        nullable=True,
        index=True,
    )

    commercial_event_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("commercial_events.id"),
        nullable=True,
        index=True,
    )

    fx_rate_type: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    period_days: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    threshold_pp: Mapped[Decimal | None] = mapped_column(
        Numeric(8, 3),
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

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    user: Mapped["User"] = relationship(
        back_populates="alert_rules",
    )

    canonical_product: Mapped["CanonicalProduct | None"] = relationship(
        back_populates="alert_rules",
    )

    commercial_event: Mapped["CommercialEvent | None"] = relationship(
        back_populates="alert_rules",
    )
    
    triggered_alerts: Mapped[list["TriggeredAlert"]] = relationship(
        back_populates="rule",
    )
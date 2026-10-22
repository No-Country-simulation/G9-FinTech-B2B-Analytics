import uuid
from datetime import datetime
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.alert_rule import AlertRule
    from app.models.triggered_alert import TriggeredAlert
    
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    String,
    Text,
    Uuid,
    func,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class CommercialEvent(Base):
    __tablename__ = "commercial_events"

    __table_args__ = (
        CheckConstraint(
            "ends_at > starts_at",
            name="ck_commercial_events_dates",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    slug: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        unique=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    starts_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    ends_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
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
    
    alert_rules: Mapped[list["AlertRule"]] = relationship(
        back_populates="commercial_event",
    )
    
    triggered_alerts: Mapped[list["TriggeredAlert"]] = relationship(
        back_populates="commercial_event",
    )
import uuid
from datetime import datetime
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.auth_token import AuthToken
    from app.models.user_session import UserSession
    from app.models.alert_rule import AlertRule
    from app.models.triggered_alert import TriggeredAlert

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Index,
    String,
    Text,
    Uuid,
    func,
    text,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    email: Mapped[str] = mapped_column(
        String(254),
        nullable=False,
    )

    password_hash: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default=text("'CLIENT'"),
    )

    email_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=true(),
    )

    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
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
    
    auth_tokens: Mapped[list["AuthToken"]] = relationship(
        back_populates="user",
    )
    
    user_sessions: Mapped[list["UserSession"]] = relationship(
        back_populates="user",
    )
    
    alert_rules: Mapped[list["AlertRule"]] = relationship(
        back_populates="user",
    )
    
    triggered_alerts: Mapped[list["TriggeredAlert"]] = relationship(
        back_populates="user",
    )

    __table_args__ = (
        CheckConstraint(
            "role IN ('CLIENT', 'ADMIN')",
            name="ck_users_role",
        ),
        Index(
            "uq_users_email_lower",
            func.lower(email),
            unique=True,
        ),
    )
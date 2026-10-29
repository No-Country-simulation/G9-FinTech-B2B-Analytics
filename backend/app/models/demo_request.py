from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.enums import OrganizationType
from app.models.mixins import WithId, enum_column


class DemoRequest(WithId, Base):
    __tablename__ = "demo_requests"

    company: Mapped[str] = mapped_column(String(160))
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(254))
    organization_type: Mapped[OrganizationType] = mapped_column(
        enum_column(OrganizationType, "organization_type")
    )
    comment: Mapped[str | None] = mapped_column(Text)
    preferred_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

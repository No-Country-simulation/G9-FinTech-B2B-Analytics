from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.enums import Role, UserStatus
from app.models.mixins import WithId, WithTimestamps, enum_column


class User(WithId, WithTimestamps, Base):
    __tablename__ = "users"

    name: Mapped[str] = mapped_column(String(120))
    company: Mapped[str] = mapped_column(String(160))
    email: Mapped[str] = mapped_column(String(254), unique=True)
    password_hash: Mapped[str | None] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(
        enum_column(Role, "user_role"),
        default=Role.CLIENT,
        server_default=Role.CLIENT.value,
        index=True,
    )
    status: Mapped[UserStatus] = mapped_column(
        enum_column(UserStatus, "user_status"),
        default=UserStatus.PENDING,
        server_default=UserStatus.PENDING.value,
        index=True,
    )
    last_access_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

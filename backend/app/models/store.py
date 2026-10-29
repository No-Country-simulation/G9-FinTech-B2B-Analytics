import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func, true
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.enums import StoreCategory
from app.models.mixins import WithId, WithTimestamps, enum_column


class Store(WithId, WithTimestamps, Base):
    __tablename__ = "stores"

    name: Mapped[str] = mapped_column(String(120))
    slug: Mapped[str] = mapped_column(String(60), unique=True)
    base_url: Mapped[str] = mapped_column(String(255))
    category: Mapped[StoreCategory] = mapped_column(enum_column(StoreCategory, "store_category"))
    scraper_key: Mapped[str] = mapped_column(String(60), unique=True)
    active: Mapped[bool] = mapped_column(default=True, server_default=true())


class UserStore(Base):
    __tablename__ = "user_store"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    store_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("stores.id", ondelete="RESTRICT"), primary_key=True, index=True
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    assigned_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )

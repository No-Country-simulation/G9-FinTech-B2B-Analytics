import uuid
from datetime import datetime
##
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.store_product import StoreProduct
    from app.models.scraper_run import ScraperRun

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    String,
    Uuid,
    func,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column , relationship

from app.models.base import Base


class Store(Base):
    __tablename__ = "stores"

    __table_args__ = (
        CheckConstraint(
            "scraping_method IN ('SCRAPY', 'PLAYWRIGHT', 'API')",
            name="ck_stores_scraping_method",
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

    base_url: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    scraping_method: Mapped[str | None] = mapped_column(
        String(30),
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
    
    products: Mapped[list["StoreProduct"]] = relationship(
        back_populates="store",
    )
    
    scraper_runs: Mapped[list["ScraperRun"]] = relationship(
        back_populates="store",
    )
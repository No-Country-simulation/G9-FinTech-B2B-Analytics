import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    Uuid,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.store import Store
    from app.models.price_snapshot import PriceSnapshot


class ScraperRun(Base):
    __tablename__ = "scraper_runs"

    __table_args__ = (
        CheckConstraint(
            "status IN ('RUNNING', 'SUCCESS', 'PARTIAL', 'FAILED')",
            name="ck_scraper_runs_status",
        ),
        CheckConstraint(
            "trigger_type IN ('SCHEDULED', 'MANUAL')",
            name="ck_scraper_runs_trigger_type",
        ),
        CheckConstraint(
            "items_scraped >= 0 AND snapshots_saved >= 0 AND error_count >= 0",
            name="ck_scraper_runs_counts_nonnegative",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    store_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("stores.id"),
        nullable=False,
        index=True,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    trigger_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    items_scraped: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("0"),
    )

    snapshots_saved: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("0"),
    )

    error_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("0"),
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    store: Mapped["Store"] = relationship(
        back_populates="scraper_runs",
    )
    
    price_snapshots: Mapped[list["PriceSnapshot"]] = relationship(
        back_populates="scraper_run",
    )
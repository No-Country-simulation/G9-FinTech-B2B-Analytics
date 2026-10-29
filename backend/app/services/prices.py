import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Listing, Price, RateType
from app.services import rates

CENTS = Decimal("0.01")


@dataclass(frozen=True)
class ScrapedObservation:
    """What each scraper delivers per product. It is the contract between scraping and storage."""

    store_id: uuid.UUID
    external_code: str
    name: str
    url: str
    current_price: Decimal | None
    strikethrough_price: Decimal | None = None
    available: bool = True
    category: str | None = None
    grammage: Decimal | None = None
    unit: str | None = None


async def record_observation(
    db: AsyncSession, observation: ScrapedObservation, captured_at: datetime | None = None
) -> Price | None:
    """Saves the listing (if new) and the price. Returns None if there is no current price."""
    if observation.current_price is None or observation.current_price <= 0:
        return None

    is_promo = (
        observation.strikethrough_price is not None
        and observation.strikethrough_price > observation.current_price
    )
    regular_price = observation.strikethrough_price if is_promo else observation.current_price

    listing_id = await db.scalar(
        insert(Listing)
        .values(
            store_id=observation.store_id,
            external_code=observation.external_code,
            name=observation.name,
            url=observation.url,
            source_category=observation.category,
        )
        .on_conflict_do_update(
            index_elements=["store_id", "external_code"],
            set_={
                "name": observation.name,
                "url": observation.url,
                "source_category": observation.category,
                "updated_at": func.now(),
            },
        )
        .returning(Listing.id)
    )

    latest = await rates.latest_rates(db)
    sell = {r.type: r.sell for r in latest}
    fx_official = sell.get(RateType.OFFICIAL)
    fx_blue = sell.get(RateType.BLUE)

    def to_usd(fx: Decimal | None) -> Decimal | None:
        return (observation.current_price / fx).quantize(CENTS) if fx else None

    price = Price(
        listing_id=listing_id,
        captured_at=captured_at or datetime.now(UTC),
        local_price=observation.current_price,
        strikethrough_price=observation.strikethrough_price,
        regular_price=regular_price,
        is_promo=is_promo,
        available=observation.available,
        grammage=observation.grammage,
        unit=observation.unit,
        fx_official=fx_official,
        fx_blue=fx_blue,
        quoted_at=max((r.quoted_at for r in latest), default=None),
        price_usd_official=to_usd(fx_official),
        price_usd_blue=to_usd(fx_blue),
    )
    db.add(price)
    await db.commit()
    return price

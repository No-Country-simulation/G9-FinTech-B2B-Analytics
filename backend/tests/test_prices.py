import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import func, select

from app.core.database import SessionLocal
from app.models import ExchangeRate, Listing, Price, RateType, Store, StoreCategory
from app.services.prices import ScrapedObservation, record_observation


async def prepare() -> uuid.UUID:
    async with SessionLocal() as db:
        store = Store(
            name="Tienda T",
            slug="tienda-t",
            base_url="https://t.example.com",
            category=StoreCategory.ELECTRONICS,
            scraper_key="tienda_t",
        )
        now = datetime.now(UTC)
        db.add_all(
            [
                store,
                ExchangeRate(
                    source="dolarapi",
                    type=RateType.OFFICIAL,
                    quoted_at=now,
                    sell=Decimal("1500"),
                ),
                ExchangeRate(
                    source="dolarapi",
                    type=RateType.BLUE,
                    quoted_at=now,
                    sell=Decimal("1600"),
                ),
            ]
        )
        await db.commit()
        return store.id


def observation(store_id: uuid.UUID, **changes: object) -> ScrapedObservation:
    base = {
        "store_id": store_id,
        "external_code": "SKU-1",
        "name": "Smart TV 50",
        "url": "https://t.example.com/tv",
        "current_price": Decimal("750"),
        "strikethrough_price": Decimal("1000"),
    }
    return ScrapedObservation(**(base | changes))


async def test_promo_computes_regular_price_and_usd() -> None:
    store_id = await prepare()
    async with SessionLocal() as db:
        price = await record_observation(db, observation(store_id))

    assert price is not None
    assert price.is_promo is True
    assert price.regular_price == Decimal("1000")
    assert price.price_usd_official == Decimal("0.50")
    assert price.price_usd_blue == Decimal("0.47")


async def test_without_strikethrough_is_not_promo() -> None:
    store_id = await prepare()
    async with SessionLocal() as db:
        price = await record_observation(db, observation(store_id, strikethrough_price=None))

    assert price is not None
    assert price.is_promo is False
    assert price.regular_price == Decimal("750")


async def test_without_current_price_is_not_saved() -> None:
    store_id = await prepare()
    async with SessionLocal() as db:
        assert await record_observation(db, observation(store_id, current_price=None)) is None
        assert await db.scalar(select(func.count()).select_from(Price)) == 0


async def test_same_listing_is_reused() -> None:
    store_id = await prepare()
    async with SessionLocal() as db:
        await record_observation(db, observation(store_id))
        await record_observation(db, observation(store_id, current_price=Decimal("800")))
        assert await db.scalar(select(func.count()).select_from(Listing)) == 1
        assert await db.scalar(select(func.count()).select_from(Price)) == 2

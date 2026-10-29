from datetime import UTC, datetime
from decimal import Decimal

import httpx
import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.core.database import SessionLocal
from app.models import ExchangeRate, RateType
from app.services import rates
from app.services.rates import SourceError
from app.workers import tasks
from app.workers.tasks import WorkerSettings
from tests.conftest import bearer


def client_for(handler) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


def response_dolarapi(request: httpx.Request) -> httpx.Response:
    casa = request.url.path.rsplit("/", 1)[-1]
    sell = 1560 if casa == "oficial" else 1575
    return httpx.Response(
        200,
        json={
            "casa": casa,
            "compra": sell - 50,
            "venta": sell,
            "fechaActualizacion": "2026-10-27T18:00:00.000Z",
        },
    )


BLUELYTICS_RESPONSE = {
    "oficial": {"value_avg": 1533.5, "value_sell": 1560.0, "value_buy": 1507.0},
    "blue": {"value_avg": 1558.0, "value_sell": 1575.0, "value_buy": 1541.0},
    "last_update": "2026-10-27T19:45:55.382008-03:00",
}


async def test_stores_official_and_blue_from_dolarapi() -> None:
    async with client_for(response_dolarapi) as client, SessionLocal() as db:
        stored = await rates.ingest_rates(db, client)
        rows = (await db.scalars(select(ExchangeRate))).all()

    assert stored == 2
    assert {r.type.value for r in rows} == {"official", "blue"}
    assert {r.source for r in rows} == {"dolarapi"}
    assert len({r.quoted_at for r in rows}) == 1  # same timestamp for both


async def test_uses_bluelytics_when_dolarapi_fails() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "dolarapi.com":
            return httpx.Response(500)
        return httpx.Response(200, json=BLUELYTICS_RESPONSE)

    async with client_for(handler) as client, SessionLocal() as db:
        await rates.ingest_rates(db, client)
        rows = (await db.scalars(select(ExchangeRate))).all()

    assert {r.source for r in rows} == {"bluelytics"}
    assert {r.sell for r in rows} == {1560, 1575}


async def test_error_when_no_source_responds() -> None:
    async with client_for(lambda request: httpx.Response(503)) as client, SessionLocal() as db:
        with pytest.raises(SourceError):
            await rates.ingest_rates(db, client)
        assert (await db.scalars(select(ExchangeRate))).all() == []


async def test_endpoint_returns_latest_rate_to_admin_only(
    client: AsyncClient, admin_token: str, client_token: str
) -> None:
    async with SessionLocal() as db:
        db.add(
            ExchangeRate(
                source="dolarapi",
                type=RateType.BLUE,
                quoted_at=datetime.now(UTC),
                buy=Decimal("1555"),
                sell=Decimal("1575"),
            )
        )
        await db.commit()

    url = "/api/v1/admin/rates"
    assert (await client.get(url)).status_code == 401
    assert (await client.get(url, headers=bearer(client_token))).status_code == 403

    response = await client.get(url, headers=bearer(admin_token))
    assert response.status_code == 200
    assert response.json()[0]["type"] == "blue"


async def test_job_stores_rates() -> None:
    async with client_for(response_dolarapi) as http:
        assert await tasks.ingest_rates({"http": http}) == 2


async def test_job_does_not_fail_without_source() -> None:
    async with client_for(lambda request: httpx.Response(503)) as http:
        assert await tasks.ingest_rates({"http": http}) == 0


def test_job_scheduled_hourly() -> None:
    job = next(j for j in WorkerSettings.cron_jobs if j.coroutine is tasks.ingest_rates)
    assert job.minute == 0
    assert job.hour is None  # no hour restriction: runs every hour
    assert not job.run_at_startup

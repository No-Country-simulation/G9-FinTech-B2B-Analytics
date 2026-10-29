from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from httpx import AsyncClient

from tests.conftest import bearer

AR = ZoneInfo("America/Argentina/Buenos_Aires")
URL_PUBLIC = "/api/v1/demo/requests"
URL_ADMIN = "/api/v1/admin/demo-requests"


def next_day(business_day: bool) -> str:
    day = datetime.now(AR) + timedelta(days=1)
    while (day.weekday() < 5) != business_day:
        day += timedelta(days=1)
    return day.replace(hour=10, minute=0, second=0, microsecond=0).isoformat()


def data(**changes: object) -> dict:
    base = {
        "company": "Supermercados del Sur",
        "name": "Ana Pérez",
        "email": "Ana@Example.com",
        "organization_type": "retail",
        "preferred_date": next_day(business_day=True),
    }
    return base | changes


async def test_visitor_creates_request(client: AsyncClient) -> None:
    response = await client.post(URL_PUBLIC, json=data())
    assert response.status_code == 201
    assert response.json()["email"] == "ana@example.com"


async def test_rejects_weekend(client: AsyncClient) -> None:
    response = await client.post(URL_PUBLIC, json=data(preferred_date=next_day(business_day=False)))
    assert response.status_code == 422


async def test_list_is_admin_only(client: AsyncClient, client_token: str, admin_token: str) -> None:
    await client.post(URL_PUBLIC, json=data())

    assert (await client.get(URL_ADMIN)).status_code == 401
    assert (await client.get(URL_ADMIN, headers=bearer(client_token))).status_code == 403

    response = await client.get(URL_ADMIN, headers=bearer(admin_token))
    assert response.status_code == 200
    assert response.json()["total"] == 1

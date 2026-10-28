import httpx
import pytest
from sqlalchemy import select

from app.core.database import SessionLocal
from app.models import Cotizacion
from app.services import cotizaciones
from app.services.cotizaciones import ErrorFuente


def cliente(handler) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


def respuesta_dolarapi(request: httpx.Request) -> httpx.Response:
    casa = request.url.path.rsplit("/", 1)[-1]
    venta = 1560 if casa == "oficial" else 1575
    return httpx.Response(
        200,
        json={
            "casa": casa,
            "compra": venta - 50,
            "venta": venta,
            "fechaActualizacion": "2026-10-27T18:00:00.000Z",
        },
    )


RESPUESTA_BLUELYTICS = {
    "oficial": {"value_avg": 1533.5, "value_sell": 1560.0, "value_buy": 1507.0},
    "blue": {"value_avg": 1558.0, "value_sell": 1575.0, "value_buy": 1541.0},
    "last_update": "2026-10-27T19:45:55.382008-03:00",
}


async def test_guarda_oficial_y_blue_desde_dolarapi() -> None:
    async with cliente(respuesta_dolarapi) as client, SessionLocal() as db:
        guardadas = await cotizaciones.ingestar_cotizaciones(db, client)
        filas = (await db.scalars(select(Cotizacion))).all()

    assert guardadas == 2
    assert {f.tipo.value for f in filas} == {"oficial", "blue"}
    assert {f.fuente for f in filas} == {"dolarapi"}
    assert len({f.cotizado_en for f in filas}) == 1  # mismo timestamp para ambas


async def test_usa_bluelytics_si_dolarapi_falla() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "dolarapi.com":
            return httpx.Response(500)
        return httpx.Response(200, json=RESPUESTA_BLUELYTICS)

    async with cliente(handler) as client, SessionLocal() as db:
        await cotizaciones.ingestar_cotizaciones(db, client)
        filas = (await db.scalars(select(Cotizacion))).all()

    assert {f.fuente for f in filas} == {"bluelytics"}
    assert {f.venta for f in filas} == {1560, 1575}


async def test_error_si_ninguna_fuente_responde() -> None:
    async with cliente(lambda request: httpx.Response(503)) as client, SessionLocal() as db:
        with pytest.raises(ErrorFuente):
            await cotizaciones.ingestar_cotizaciones(db, client)
        assert (await db.scalars(select(Cotizacion))).all() == []

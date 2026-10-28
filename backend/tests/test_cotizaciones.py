from datetime import UTC, datetime
from decimal import Decimal

import httpx
import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.core.database import SessionLocal
from app.models import Cotizacion, TipoCotizacion
from app.services import cotizaciones
from app.services.cotizaciones import ErrorFuente
from app.workers import tareas
from app.workers.tareas import WorkerSettings
from tests.conftest import bearer


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


async def test_endpoint_devuelve_ultima_cotizacion_solo_a_admin(
    client: AsyncClient, token_admin: str, token_cliente: str
) -> None:
    async with SessionLocal() as db:
        db.add(
            Cotizacion(
                fuente="dolarapi",
                tipo=TipoCotizacion.BLUE,
                cotizado_en=datetime.now(UTC),
                compra=Decimal("1555"),
                venta=Decimal("1575"),
            )
        )
        await db.commit()

    url = "/api/v1/admin/cotizaciones"
    assert (await client.get(url)).status_code == 401
    assert (await client.get(url, headers=bearer(token_cliente))).status_code == 403

    respuesta = await client.get(url, headers=bearer(token_admin))
    assert respuesta.status_code == 200
    assert respuesta.json()[0]["tipo"] == "blue"


async def test_job_guarda_cotizaciones() -> None:
    async with cliente(respuesta_dolarapi) as http:
        assert await tareas.ingestar_cotizaciones({"http": http}) == 2


async def test_job_no_falla_si_no_hay_fuente() -> None:
    async with cliente(lambda request: httpx.Response(503)) as http:
        assert await tareas.ingestar_cotizaciones({"http": http}) == 0


def test_job_programado_cada_hora() -> None:
    job = next(j for j in WorkerSettings.cron_jobs if j.coroutine is tareas.ingestar_cotizaciones)
    assert job.minute == 0
    assert job.hour is None  # sin restricción de hora: corre todas
    assert not job.run_at_startup

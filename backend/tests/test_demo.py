from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from httpx import AsyncClient

from tests.conftest import bearer

AR = ZoneInfo("America/Argentina/Buenos_Aires")
URL_PUBLICA = "/api/v1/demo/solicitudes"
URL_ADMIN = "/api/v1/admin/solicitudes"


def proximo_dia(habil: bool) -> str:
    dia = datetime.now(AR) + timedelta(days=1)
    while (dia.weekday() < 5) != habil:
        dia += timedelta(days=1)
    return dia.replace(hour=10, minute=0, second=0, microsecond=0).isoformat()


def datos(**cambios: object) -> dict:
    base = {
        "empresa": "Supermercados del Sur",
        "nombre": "Ana Pérez",
        "correo": "Ana@Example.com",
        "tipo_organizacion": "retail",
        "fecha_preferida": proximo_dia(habil=True),
    }
    return base | cambios


async def test_visitante_crea_solicitud(client: AsyncClient) -> None:
    respuesta = await client.post(URL_PUBLICA, json=datos())
    assert respuesta.status_code == 201
    assert respuesta.json()["correo"] == "ana@example.com"


async def test_rechaza_fin_de_semana(client: AsyncClient) -> None:
    respuesta = await client.post(URL_PUBLICA, json=datos(fecha_preferida=proximo_dia(habil=False)))
    assert respuesta.status_code == 422


async def test_listado_solo_para_admin(
    client: AsyncClient, token_cliente: str, token_admin: str
) -> None:
    await client.post(URL_PUBLICA, json=datos())

    assert (await client.get(URL_ADMIN)).status_code == 401
    assert (await client.get(URL_ADMIN, headers=bearer(token_cliente))).status_code == 403

    respuesta = await client.get(URL_ADMIN, headers=bearer(token_admin))
    assert respuesta.status_code == 200
    assert respuesta.json()["total"] == 1

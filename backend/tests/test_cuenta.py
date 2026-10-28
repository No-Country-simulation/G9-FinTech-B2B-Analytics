import pytest
from httpx import AsyncClient

from tests.conftest import bearer

URL = "/api/v1/cuenta/datos"


async def test_editar_nombre_y_empresa(
    client: AsyncClient,
    token_cliente: str,
) -> None:
    respuesta = await client.patch(
        URL,
        json={
            "nombre": "Luciano Castillo",
            "empresa": "PriceScope Analytics",
        },
        headers=bearer(token_cliente),
    )

    assert respuesta.status_code == 200
    assert respuesta.json() == {
        "nombre": "Luciano Castillo",
        "empresa": "PriceScope Analytics",
    }

    # Comprobamos que los cambios quedaron guardados.
    respuesta_yo = await client.get(
        "/api/v1/auth/yo",
        headers=bearer(token_cliente),
    )

    assert respuesta_yo.status_code == 200
    assert respuesta_yo.json()["nombre"] == "Luciano Castillo"
    assert respuesta_yo.json()["empresa"] == "PriceScope Analytics"


async def test_editar_solo_empresa(
    client: AsyncClient,
    token_cliente: str,
) -> None:
    respuesta = await client.patch(
        URL,
        json={"empresa": "Empresa Actualizada"},
        headers=bearer(token_cliente),
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["empresa"] == "Empresa Actualizada"
    assert respuesta.json()["nombre"] == "Usuario de prueba"


async def test_sin_autenticacion(
    client: AsyncClient,
) -> None:
    respuesta = await client.patch(
        URL,
        json={"nombre": "Nuevo Nombre"},
    )

    assert respuesta.status_code == 401


async def test_solicitud_vacia(
    client: AsyncClient,
    token_cliente: str,
) -> None:
    respuesta = await client.patch(
        URL,
        json={},
        headers=bearer(token_cliente),
    )

    assert respuesta.status_code == 400


@pytest.mark.parametrize(
    "datos",
    [
        {"nombre": ""},
        {"nombre": " "},
        {"nombre": "A"},
        {"nombre": None},
        {"empresa": "A"},
        {"empresa": None},
        {"nombre": "A" * 121},
        {"empresa": "A" * 161},
    ],
)
async def test_validaciones(
    client: AsyncClient,
    token_cliente: str,
    datos: dict,
) -> None:
    respuesta = await client.patch(
        URL,
        json=datos,
        headers=bearer(token_cliente),
    )

    assert respuesta.status_code == 422


async def test_no_permite_modificar_rol(
    client: AsyncClient,
    token_cliente: str,
) -> None:
    respuesta = await client.patch(
        URL,
        json={
            "nombre": "Luciano Castillo",
            "rol": "admin",
        },
        headers=bearer(token_cliente),
    )

    assert respuesta.status_code == 422


async def test_no_permite_modificar_correo(
    client: AsyncClient,
    token_cliente: str,
) -> None:
    respuesta = await client.patch(
        URL,
        json={"correo": "nuevo@example.com"},
        headers=bearer(token_cliente),
    )

    assert respuesta.status_code == 422


async def test_no_permite_modificar_password(
    client: AsyncClient,
    token_cliente: str,
) -> None:
    respuesta = await client.patch(
        URL,
        json={"password_hash": "valor_incorrecto"},
        headers=bearer(token_cliente),
    )

    assert respuesta.status_code == 422
import re

from httpx import AsyncClient

from tests.conftest import ColaFalsa, bearer, login

URL = "/api/v1/admin/usuarios"
NUEVO = {"nombre": "Carla Gómez", "empresa": "Fondo Austral", "correo": "carla@example.com"}


def token_del_correo(cola: ColaFalsa) -> str:
    funcion, args = cola.trabajos[-1]
    assert funcion == "enviar_correo"
    texto = args[2]
    return re.search(r"/definir-contrasena/(\S+)", texto).group(1)


async def test_alta_queda_pendiente_y_encola_correo(
    client: AsyncClient, token_admin: str, cola: ColaFalsa
) -> None:
    respuesta = await client.post(URL, json=NUEVO, headers=bearer(token_admin))
    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["usuario"]["estado"] == "pendiente"
    assert cuerpo["correo_encolado"] is True
    assert len(cola.trabajos) == 1


async def test_correo_duplicado(client: AsyncClient, token_admin: str) -> None:
    await client.post(URL, json=NUEVO, headers=bearer(token_admin))
    respuesta = await client.post(
        URL, json=NUEVO | {"correo": "CARLA@example.com"}, headers=bearer(token_admin)
    )
    assert respuesta.status_code == 409


async def test_flujo_completo_alta_password_login(
    client: AsyncClient, token_admin: str, cola: ColaFalsa
) -> None:
    await client.post(URL, json=NUEVO, headers=bearer(token_admin))
    token = token_del_correo(cola)

    verificado = await client.post("/api/v1/auth/token/verificar", json={"token": token})
    assert verificado.json()["estado"] == "valido"

    definido = await client.post(
        "/api/v1/auth/password", json={"token": token, "password": "Carla2026"}
    )
    assert definido.status_code == 200

    acceso = await login(client, "carla@example.com", "Carla2026")
    yo = await client.get("/api/v1/auth/yo", headers=bearer(acceso))
    assert yo.json()["tienda_ids"] == []

    reusado = await client.post(
        "/api/v1/auth/password", json={"token": token, "password": "Otra2026x"}
    )
    assert reusado.status_code == 400


async def test_cliente_no_puede_crear_usuarios(client: AsyncClient, token_cliente: str) -> None:
    respuesta = await client.post(URL, json=NUEVO, headers=bearer(token_cliente))
    assert respuesta.status_code == 403

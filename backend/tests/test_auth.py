from httpx import AsyncClient

from tests.conftest import bearer, crear_usuario_activo, login


async def test_login_incorrecto_es_generico(client: AsyncClient) -> None:
    await crear_usuario_activo("ana@example.com")
    mala_password = await client.post(
        "/api/v1/auth/login", json={"correo": "ana@example.com", "password": "Incorrecta1"}
    )
    no_existe = await client.post(
        "/api/v1/auth/login", json={"correo": "nadie@example.com", "password": "Incorrecta1"}
    )
    assert mala_password.status_code == no_existe.status_code == 401
    assert mala_password.json() == no_existe.json()


async def test_logout_invalida_el_token(client: AsyncClient) -> None:
    await crear_usuario_activo("ana@example.com")
    token = await login(client, "ana@example.com")

    assert (await client.post("/api/v1/auth/logout", headers=bearer(token))).status_code == 204
    assert (await client.get("/api/v1/auth/yo", headers=bearer(token))).status_code == 401


async def test_refresh_rota_la_sesion(client: AsyncClient) -> None:
    await crear_usuario_activo("ana@example.com")
    await login(client, "ana@example.com")  # deja la cookie ps_refresh en el cliente

    respuesta = await client.post("/api/v1/auth/refresh")
    assert respuesta.status_code == 200
    assert "access_token" in respuesta.json()


async def test_recuperar_responde_igual_exista_o_no(client: AsyncClient) -> None:
    await crear_usuario_activo("ana@example.com")
    existe = await client.post("/api/v1/auth/recuperar", json={"correo": "ana@example.com"})
    no_existe = await client.post("/api/v1/auth/recuperar", json={"correo": "nadie@example.com"})
    assert existe.status_code == no_existe.status_code == 202
    assert existe.json() == no_existe.json()

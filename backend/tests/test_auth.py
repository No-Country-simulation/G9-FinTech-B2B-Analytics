from httpx import AsyncClient

from tests.conftest import bearer, create_active_user, login


async def test_failed_login_is_generic(client: AsyncClient) -> None:
    await create_active_user("ana@example.com")
    wrong_password = await client.post(
        "/api/v1/auth/login", json={"email": "ana@example.com", "password": "Incorrecta1"}
    )
    not_found = await client.post(
        "/api/v1/auth/login", json={"email": "nadie@example.com", "password": "Incorrecta1"}
    )
    assert wrong_password.status_code == not_found.status_code == 401
    assert wrong_password.json() == not_found.json()


async def test_logout_invalidates_the_token(client: AsyncClient) -> None:
    await create_active_user("ana@example.com")
    token = await login(client, "ana@example.com")

    assert (await client.post("/api/v1/auth/logout", headers=bearer(token))).status_code == 204
    assert (await client.get("/api/v1/auth/me", headers=bearer(token))).status_code == 401


async def test_refresh_rotates_the_session(client: AsyncClient) -> None:
    await create_active_user("ana@example.com")
    await login(client, "ana@example.com")  # sets the ps_refresh cookie on the client

    response = await client.post("/api/v1/auth/refresh")
    assert response.status_code == 200
    assert "access_token" in response.json()


async def test_recover_responds_the_same_whether_or_not_the_account_exists(
    client: AsyncClient,
) -> None:
    await create_active_user("ana@example.com")
    exists = await client.post("/api/v1/auth/recover", json={"email": "ana@example.com"})
    not_exists = await client.post("/api/v1/auth/recover", json={"email": "nadie@example.com"})
    assert exists.status_code == not_exists.status_code == 202
    assert exists.json() == not_exists.json()

import re

from httpx import AsyncClient

from tests.conftest import FakeQueue, bearer, login

URL = "/api/v1/admin/users"
NEW_USER = {"name": "Carla Gómez", "company": "Fondo Austral", "email": "carla@example.com"}


def token_from_email(queue: FakeQueue) -> str:
    function, args = queue.jobs[-1]
    assert function == "send_email"
    text = args[2]
    return re.search(r"/definir-contrasena/(\S+)", text).group(1)


async def test_new_user_is_pending_and_email_is_queued(
    client: AsyncClient, admin_token: str, queue: FakeQueue
) -> None:
    response = await client.post(URL, json=NEW_USER, headers=bearer(admin_token))
    assert response.status_code == 201
    body = response.json()
    assert body["user"]["status"] == "pending"
    assert body["email_queued"] is True
    assert len(queue.jobs) == 1


async def test_duplicate_email(client: AsyncClient, admin_token: str) -> None:
    await client.post(URL, json=NEW_USER, headers=bearer(admin_token))
    response = await client.post(
        URL, json=NEW_USER | {"email": "CARLA@example.com"}, headers=bearer(admin_token)
    )
    assert response.status_code == 409


async def test_full_flow_create_set_password_login(
    client: AsyncClient, admin_token: str, queue: FakeQueue
) -> None:
    await client.post(URL, json=NEW_USER, headers=bearer(admin_token))
    token = token_from_email(queue)

    verified = await client.post("/api/v1/auth/token/verify", json={"token": token})
    assert verified.json()["status"] == "valid"

    defined = await client.post(
        "/api/v1/auth/password", json={"token": token, "password": "Carla2026"}
    )
    assert defined.status_code == 200

    access = await login(client, "carla@example.com", "Carla2026")
    me = await client.get("/api/v1/auth/me", headers=bearer(access))
    assert me.json()["store_ids"] == []

    reused = await client.post(
        "/api/v1/auth/password", json={"token": token, "password": "Otra2026x"}
    )
    assert reused.status_code == 400


async def test_client_cannot_create_users(client: AsyncClient, client_token: str) -> None:
    response = await client.post(URL, json=NEW_USER, headers=bearer(client_token))
    assert response.status_code == 403

import re

from httpx import AsyncClient

from tests.conftest import FakeQueue, bearer, create_active_user, login

URL = "/api/v1/admin/users"
PENDING_USER = {"name": "Carla Gómez", "company": "Fondo Austral", "email": "carla@example.com"}


def last_link(queue: FakeQueue, path: str) -> str:
    function, args = queue.jobs[-1]
    assert function == "send_email"
    return re.search(rf"/{path}/(\S+)", args[2]).group(1)


async def create_pending(client: AsyncClient, admin_token: str) -> str:
    response = await client.post(URL, json=PENDING_USER, headers=bearer(admin_token))
    return response.json()["user"]["id"]


# --- Block / unblock ---


async def test_block_closes_sessions_and_unblock_restores_access(
    client: AsyncClient, admin_token: str
) -> None:
    user = await create_active_user("ana@example.com")
    access = await login(client, "ana@example.com")

    blocked = await client.post(f"{URL}/{user.id}/block", headers=bearer(admin_token))
    assert blocked.status_code == 200
    assert blocked.json()["status"] == "blocked"

    me = await client.get("/api/v1/auth/me", headers=bearer(access))
    assert me.status_code == 401
    refused = await client.post(
        "/api/v1/auth/login", json={"email": "ana@example.com", "password": "Prueba123"}
    )
    assert refused.status_code == 401

    unblocked = await client.post(f"{URL}/{user.id}/unblock", headers=bearer(admin_token))
    assert unblocked.json()["status"] == "active"
    await login(client, "ana@example.com")


async def test_unblocking_a_user_without_password_returns_to_pending(
    client: AsyncClient, admin_token: str
) -> None:
    user_id = await create_pending(client, admin_token)
    await client.post(f"{URL}/{user_id}/block", headers=bearer(admin_token))
    unblocked = await client.post(f"{URL}/{user_id}/unblock", headers=bearer(admin_token))
    assert unblocked.json()["status"] == "pending"


async def test_block_invalidates_the_access_link(
    client: AsyncClient, admin_token: str, queue: FakeQueue
) -> None:
    user_id = await create_pending(client, admin_token)
    token = last_link(queue, "definir-contrasena")
    await client.post(f"{URL}/{user_id}/block", headers=bearer(admin_token))
    verified = await client.post("/api/v1/auth/token/verify", json={"token": token})
    assert verified.json()["status"] == "invalid"


async def test_admin_cannot_block_or_deactivate_themselves(
    client: AsyncClient, admin_token: str
) -> None:
    me = await client.get("/api/v1/auth/me", headers=bearer(admin_token))
    admin_id = me.json()["id"]
    for action in ("block", "deactivate"):
        response = await client.post(f"{URL}/{admin_id}/{action}", headers=bearer(admin_token))
        assert response.status_code == 403


async def test_block_twice_and_unblock_active(client: AsyncClient, admin_token: str) -> None:
    user = await create_active_user("ana@example.com")
    await client.post(f"{URL}/{user.id}/block", headers=bearer(admin_token))
    again = await client.post(f"{URL}/{user.id}/block", headers=bearer(admin_token))
    assert again.status_code == 409

    other = await create_active_user("beto@example.com")
    response = await client.post(f"{URL}/{other.id}/unblock", headers=bearer(admin_token))
    assert response.status_code == 400


# --- Deactivate ---


async def test_deactivate_is_final(client: AsyncClient, admin_token: str) -> None:
    user = await create_active_user("ana@example.com")
    access = await login(client, "ana@example.com")

    response = await client.post(f"{URL}/{user.id}/deactivate", headers=bearer(admin_token))
    assert response.status_code == 200
    assert response.json()["status"] == "deactivated"
    assert (await client.get("/api/v1/auth/me", headers=bearer(access))).status_code == 401

    for action in ("block", "unblock"):
        blocked = await client.post(f"{URL}/{user.id}/{action}", headers=bearer(admin_token))
        assert blocked.status_code == 400
    again = await client.post(f"{URL}/{user.id}/deactivate", headers=bearer(admin_token))
    assert again.status_code == 409


# --- Email change ---


async def test_change_email_of_active_user(client: AsyncClient, admin_token: str) -> None:
    user = await create_active_user("ana@example.com")
    response = await client.patch(
        f"{URL}/{user.id}/email",
        json={"email": "Ana.Nueva@example.com"},
        headers=bearer(admin_token),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["user"]["email"] == "ana.nueva@example.com"
    assert body["email_queued"] is False
    await login(client, "ana.nueva@example.com")


async def test_change_email_of_pending_user_resends_access(
    client: AsyncClient, admin_token: str, queue: FakeQueue
) -> None:
    user_id = await create_pending(client, admin_token)
    old_token = last_link(queue, "definir-contrasena")

    response = await client.patch(
        f"{URL}/{user_id}/email",
        json={"email": "carla.ok@example.com"},
        headers=bearer(admin_token),
    )
    assert response.json()["email_queued"] is True
    _, args = queue.jobs[-1]
    assert args[0] == "carla.ok@example.com"

    old = await client.post("/api/v1/auth/token/verify", json={"token": old_token})
    assert old.json()["status"] == "invalid"
    new = await client.post(
        "/api/v1/auth/token/verify", json={"token": last_link(queue, "definir-contrasena")}
    )
    assert new.json()["status"] == "valid"


async def test_change_email_rejects_taken_same_and_closed(
    client: AsyncClient, admin_token: str
) -> None:
    user = await create_active_user("ana@example.com")
    await create_active_user("beto@example.com")
    headers = bearer(admin_token)

    taken = await client.patch(
        f"{URL}/{user.id}/email", json={"email": "BETO@example.com"}, headers=headers
    )
    assert taken.status_code == 409
    same = await client.patch(
        f"{URL}/{user.id}/email", json={"email": "ana@example.com"}, headers=headers
    )
    assert same.status_code == 400

    await client.post(f"{URL}/{user.id}/block", headers=headers)
    blocked = await client.patch(
        f"{URL}/{user.id}/email", json={"email": "ana2@example.com"}, headers=headers
    )
    assert blocked.status_code == 400


# --- Password reset link ---


async def test_password_reset_link_for_active_user(
    client: AsyncClient, admin_token: str, queue: FakeQueue
) -> None:
    user = await create_active_user("ana@example.com")
    response = await client.post(f"{URL}/{user.id}/password-reset", headers=bearer(admin_token))
    assert response.status_code == 202

    token = last_link(queue, "restablecer")
    defined = await client.post(
        "/api/v1/auth/password", json={"token": token, "password": "Nueva2026"}
    )
    assert defined.status_code == 200
    await login(client, "ana@example.com", "Nueva2026")


async def test_password_reset_requires_active_user(client: AsyncClient, admin_token: str) -> None:
    user_id = await create_pending(client, admin_token)
    response = await client.post(f"{URL}/{user_id}/password-reset", headers=bearer(admin_token))
    assert response.status_code == 400


# --- Permissions ---


async def test_clients_cannot_use_admin_account_actions(
    client: AsyncClient, client_token: str
) -> None:
    other = await create_active_user("ana@example.com")
    headers = bearer(client_token)
    for action in ("block", "unblock", "deactivate", "password-reset"):
        response = await client.post(f"{URL}/{other.id}/{action}", headers=headers)
        assert response.status_code == 403
    email = await client.patch(
        f"{URL}/{other.id}/email", json={"email": "x@example.com"}, headers=headers
    )
    assert email.status_code == 403

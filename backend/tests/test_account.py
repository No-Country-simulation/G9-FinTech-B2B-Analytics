import re
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.security import hash_token
from app.models import EmailChange, User, UserStatus
from tests.conftest import FakeQueue, bearer

URL = "/api/v1/account/profile"


async def test_edit_name_and_company(
    client: AsyncClient,
    client_token: str,
) -> None:
    response = await client.patch(
        URL,
        json={
            "name": "Luciano Castillo",
            "company": "PriceScope Analytics",
        },
        headers=bearer(client_token),
    )

    assert response.status_code == 200
    assert response.json() == {
        "name": "Luciano Castillo",
        "company": "PriceScope Analytics",
    }

    # Check that the changes were saved.
    response_me = await client.get(
        "/api/v1/auth/me",
        headers=bearer(client_token),
    )

    assert response_me.status_code == 200
    assert response_me.json()["name"] == "Luciano Castillo"
    assert response_me.json()["company"] == "PriceScope Analytics"


async def test_edit_only_company(
    client: AsyncClient,
    client_token: str,
) -> None:
    response = await client.patch(
        URL,
        json={"company": "Empresa Actualizada"},
        headers=bearer(client_token),
    )

    assert response.status_code == 200
    assert response.json()["company"] == "Empresa Actualizada"
    assert response.json()["name"] == "Usuario de prueba"


async def test_without_authentication(
    client: AsyncClient,
) -> None:
    response = await client.patch(
        URL,
        json={"name": "Nuevo Nombre"},
    )

    assert response.status_code == 401


async def test_empty_request(
    client: AsyncClient,
    client_token: str,
) -> None:
    response = await client.patch(
        URL,
        json={},
        headers=bearer(client_token),
    )

    assert response.status_code == 400


@pytest.mark.parametrize(
    "data",
    [
        {"name": ""},
        {"name": " "},
        {"name": "A"},
        {"name": None},
        {"company": "A"},
        {"company": None},
        {"name": "A" * 121},
        {"company": "A" * 161},
    ],
)
async def test_validations(
    client: AsyncClient,
    client_token: str,
    data: dict,
) -> None:
    response = await client.patch(
        URL,
        json=data,
        headers=bearer(client_token),
    )

    assert response.status_code == 422


async def test_cannot_change_role(
    client: AsyncClient,
    client_token: str,
) -> None:
    response = await client.patch(
        URL,
        json={
            "name": "Luciano Castillo",
            "role": "admin",
        },
        headers=bearer(client_token),
    )

    assert response.status_code == 422


async def test_cannot_change_email(
    client: AsyncClient,
    client_token: str,
) -> None:
    response = await client.patch(
        URL,
        json={"email": "nuevo@example.com"},
        headers=bearer(client_token),
    )

    assert response.status_code == 422


async def test_cannot_change_password_hash(
    client: AsyncClient,
    client_token: str,
) -> None:
    response = await client.patch(
        URL,
        json={"password_hash": "valor_incorrecto"},
        headers=bearer(client_token),
    )

    assert response.status_code == 422


# ---PASSWORD CHANGE---
URL_PASSWORD = "/api/v1/account/password"


async def test_change_password_successfully(
    client: AsyncClient,
    client_token: str,
) -> None:
    response = await client.patch(
        URL_PASSWORD,
        json={
            "current_password": "Prueba123",
            "new_password": "NuevaClave456",
        },
        headers=bearer(client_token),
    )

    assert response.status_code == 200

    # The previous session must be invalidated.
    me = await client.get(
        "/api/v1/auth/me",
        headers=bearer(client_token),
    )
    assert me.status_code == 401

    # The old password no longer works.
    old_login = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "cliente@example.com",
            "password": "Prueba123",
        },
    )
    assert old_login.status_code == 401

    # The new password allows login.
    new_login = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "cliente@example.com",
            "password": "NuevaClave456",
        },
    )
    assert new_login.status_code == 200


async def test_wrong_current_password(
    client: AsyncClient,
    client_token: str,
) -> None:
    response = await client.patch(
        URL_PASSWORD,
        json={
            "current_password": "Incorrecta123",
            "new_password": "NuevaClave456",
        },
        headers=bearer(client_token),
    )

    assert response.status_code == 400

    # The original password must keep working.
    login = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "cliente@example.com",
            "password": "Prueba123",
        },
    )

    assert login.status_code == 200


async def test_cannot_reuse_same_password(
    client: AsyncClient,
    client_token: str,
) -> None:
    response = await client.patch(
        URL_PASSWORD,
        json={
            "current_password": "Prueba123",
            "new_password": "Prueba123",
        },
        headers=bearer(client_token),
    )

    assert response.status_code == 400


async def test_invalid_new_password(
    client: AsyncClient,
    client_token: str,
) -> None:
    response = await client.patch(
        URL_PASSWORD,
        json={
            "current_password": "Prueba123",
            "new_password": "123",
        },
        headers=bearer(client_token),
    )

    assert response.status_code == 422


async def test_change_password_without_token(
    client: AsyncClient,
) -> None:
    response = await client.patch(
        URL_PASSWORD,
        json={
            "current_password": "Prueba123",
            "new_password": "NuevaClave456",
        },
    )

    assert response.status_code == 401


# ---EMAIL CHANGE---
URL_EMAIL = "/api/v1/account/email"
URL_CONFIRM = "/api/v1/account/email/confirm"


def email_change_token(queue: FakeQueue) -> str:
    function, args = queue.jobs[-1]

    assert function == "send_email"

    match = re.search(
        r"/confirmar-correo/([A-Za-z0-9_-]+)",
        args[2],
    )
    assert match is not None

    return match.group(1)


async def test_change_email_successfully(
    client: AsyncClient,
    client_token: str,
    queue: FakeQueue,
) -> None:
    response = await client.post(
        URL_EMAIL,
        json={
            "new_email": "nuevo@example.com",
            "current_password": "Prueba123",
        },
        headers=bearer(client_token),
    )

    assert response.status_code == 202
    assert queue.jobs[-1][1][0] == "nuevo@example.com"

    # Until confirmed, the email is still the old one.
    me = await client.get(
        "/api/v1/auth/me",
        headers=bearer(client_token),
    )
    assert me.json()["email"] == "cliente@example.com"

    token = email_change_token(queue)

    confirmation = await client.post(
        URL_CONFIRM,
        json={"token": token},
    )

    assert confirmation.status_code == 200

    # The previous session is revoked.
    me = await client.get(
        "/api/v1/auth/me",
        headers=bearer(client_token),
    )
    assert me.status_code == 401

    # Login with the old email no longer works.
    previous = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "cliente@example.com",
            "password": "Prueba123",
        },
    )
    assert previous.status_code == 401

    # The new email works.
    new = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "nuevo@example.com",
            "password": "Prueba123",
        },
    )
    assert new.status_code == 200


async def test_email_confirmation_cannot_be_reused(
    client: AsyncClient,
    client_token: str,
    queue: FakeQueue,
) -> None:
    await client.post(
        URL_EMAIL,
        json={
            "new_email": "nuevo@example.com",
            "current_password": "Prueba123",
        },
        headers=bearer(client_token),
    )

    token = email_change_token(queue)

    first = await client.post(
        URL_CONFIRM,
        json={"token": token},
    )

    second = await client.post(
        URL_CONFIRM,
        json={"token": token},
    )

    assert first.status_code == 200
    assert second.status_code == 400


async def test_invalid_email_change_token(
    client: AsyncClient,
) -> None:
    response = await client.post(
        URL_CONFIRM,
        json={"token": "token-inexistente-123456789"},
    )

    assert response.status_code == 400


async def test_expired_email_change_token(
    client: AsyncClient,
    client_token: str,
    queue: FakeQueue,
) -> None:
    response = await client.post(
        URL_EMAIL,
        json={
            "new_email": "nuevo@example.com",
            "current_password": "Prueba123",
        },
        headers=bearer(client_token),
    )

    assert response.status_code == 202

    token = email_change_token(queue)

    # Simulate that the link has already expired.
    async with SessionLocal() as db:
        record = await db.scalar(
            select(EmailChange).where(EmailChange.token_hash == hash_token(token))
        )

        assert record is not None

        record.expires_at = datetime.now(UTC) - timedelta(minutes=1)
        await db.commit()

    confirmation = await client.post(
        URL_CONFIRM,
        json={"token": token},
    )

    assert confirmation.status_code == 400

    # The original email must remain.
    me = await client.get(
        "/api/v1/auth/me",
        headers=bearer(client_token),
    )

    assert me.status_code == 200
    assert me.json()["email"] == "cliente@example.com"


async def test_new_request_invalidates_previous_token(
    client: AsyncClient,
    client_token: str,
    queue: FakeQueue,
) -> None:

    first = await client.post(
        URL_EMAIL,
        json={
            "new_email": "primero@example.com",
            "current_password": "Prueba123",
        },
        headers=bearer(client_token),
    )

    assert first.status_code == 202
    previous_token = email_change_token(queue)

    second = await client.post(
        URL_EMAIL,
        json={
            "new_email": "segundo@example.com",
            "current_password": "Prueba123",
        },
        headers=bearer(client_token),
    )

    assert second.status_code == 202
    new_token = email_change_token(queue)

    # The first link must no longer work.
    previous_response = await client.post(
        URL_CONFIRM,
        json={"token": previous_token},
    )

    assert previous_response.status_code == 400

    # The second link must work.
    new_response = await client.post(
        URL_CONFIRM,
        json={"token": new_token},
    )

    assert new_response.status_code == 200


# ---DEACTIVATE ACCOUNT---
URL_DELETE = "/api/v1/account"

DELETE_DATA = {
    "current_password": "Prueba123",
    "confirmation": "ELIMINAR MI CUENTA",
}


async def test_deactivate_account_successfully(
    client: AsyncClient,
    client_token: str,
) -> None:

    response = await client.request(
        "DELETE",
        URL_DELETE,
        json=DELETE_DATA,
        headers=bearer(client_token),
    )

    assert response.status_code == 200

    # The account stays registered, but deactivated.
    async with SessionLocal() as db:
        user = await db.scalar(select(User).where(User.email == "cliente@example.com"))

        assert user is not None
        assert user.status == UserStatus.DEACTIVATED

    # The previous token stops working.
    me = await client.get(
        "/api/v1/auth/me",
        headers=bearer(client_token),
    )

    assert me.status_code == 401

    # The account can no longer log in.
    login = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "cliente@example.com",
            "password": "Prueba123",
        },
    )

    assert login.status_code == 401


async def test_deactivate_wrong_password(
    client: AsyncClient,
    client_token: str,
) -> None:

    data = DELETE_DATA | {"current_password": "Incorrecta123"}

    response = await client.request(
        "DELETE",
        URL_DELETE,
        json=data,
        headers=bearer(client_token),
    )

    assert response.status_code == 400

    # The user must remain active.
    me = await client.get(
        "/api/v1/auth/me",
        headers=bearer(client_token),
    )

    assert me.status_code == 200


async def test_deactivate_without_correct_confirmation(
    client: AsyncClient,
    client_token: str,
) -> None:

    data = DELETE_DATA | {"confirmation": "ELIMINAR"}

    response = await client.request(
        "DELETE",
        URL_DELETE,
        json=data,
        headers=bearer(client_token),
    )

    assert response.status_code == 422

    me = await client.get(
        "/api/v1/auth/me",
        headers=bearer(client_token),
    )

    assert me.status_code == 200


async def test_deactivate_without_authentication(
    client: AsyncClient,
) -> None:

    response = await client.request(
        "DELETE",
        URL_DELETE,
        json=DELETE_DATA,
    )

    assert response.status_code == 401


async def test_admin_cannot_deactivate_own_account(
    client: AsyncClient,
    admin_token: str,
) -> None:

    response = await client.request(
        "DELETE",
        URL_DELETE,
        json=DELETE_DATA,
        headers=bearer(admin_token),
    )

    assert response.status_code == 403

    # The administrator remains active.
    me = await client.get(
        "/api/v1/auth/me",
        headers=bearer(admin_token),
    )

    assert me.status_code == 200


async def test_deactivation_revokes_all_sessions(
    client: AsyncClient,
    client_token: str,
) -> None:

    # Create a second session for the same user.
    second_login = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "cliente@example.com",
            "password": "Prueba123",
        },
    )

    assert second_login.status_code == 200

    second_token = second_login.json()["access_token"]

    response = await client.request(
        "DELETE",
        URL_DELETE,
        json=DELETE_DATA,
        headers=bearer(client_token),
    )

    assert response.status_code == 200

    # Both sessions must be invalidated.
    for token in [client_token, second_token]:
        me = await client.get(
            "/api/v1/auth/me",
            headers=bearer(token),
        )

        assert me.status_code == 401

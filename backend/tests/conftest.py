import os

# Antes de importar la app: base de tests y entorno de tests.
os.environ["ENVIRONMENT"] = "test"
os.environ["POSTGRES_DB"] = os.environ.get("POSTGRES_DB_TEST", "pricescope_test")

from collections.abc import AsyncIterator, Iterator  # noqa: E402

import pytest  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402

import app.models  # noqa: E402, F401
from app.api.deps import get_cola  # noqa: E402
from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.core.seguridad import hashear_password  # noqa: E402
from app.main import app as aplicacion  # noqa: E402
from app.models import EstadoUsuario, Rol, Usuario  # noqa: E402

PASSWORD = "Prueba123"


class ColaFalsa:
    """Reemplaza a Redis/ARQ: guarda los trabajos en una lista para poder revisarlos."""

    def __init__(self) -> None:
        self.trabajos: list[tuple[str, tuple]] = []

    async def enqueue_job(self, function: str, *args: object, **kwargs: object) -> None:
        self.trabajos.append((function, args))


@pytest.fixture(autouse=True)
async def base_limpia() -> AsyncIterator[None]:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest.fixture
def cola() -> Iterator[ColaFalsa]:
    falsa = ColaFalsa()
    aplicacion.dependency_overrides[get_cola] = lambda: falsa
    yield falsa
    aplicacion.dependency_overrides.clear()


@pytest.fixture
async def client(cola: ColaFalsa) -> AsyncIterator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=aplicacion), base_url="http://test") as c:
        yield c


async def crear_usuario_activo(correo: str, rol: Rol = Rol.CLIENTE) -> Usuario:
    async with SessionLocal() as db:
        usuario = Usuario(
            nombre="Usuario de prueba",
            empresa="Empresa de prueba",
            correo=correo,
            password_hash=hashear_password(PASSWORD),
            rol=rol,
            estado=EstadoUsuario.ACTIVO,
        )
        db.add(usuario)
        await db.commit()
        return usuario


async def login(client: AsyncClient, correo: str, password: str = PASSWORD) -> str:
    respuesta = await client.post(
        "/api/v1/auth/login", json={"correo": correo, "password": password}
    )
    assert respuesta.status_code == 200, respuesta.text
    return respuesta.json()["access_token"]


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def token_admin(client: AsyncClient) -> str:
    await crear_usuario_activo("admin@example.com", Rol.ADMIN)
    return await login(client, "admin@example.com")


@pytest.fixture
async def token_cliente(client: AsyncClient) -> str:
    await crear_usuario_activo("cliente@example.com")
    return await login(client, "cliente@example.com")

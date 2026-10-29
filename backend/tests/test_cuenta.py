import re
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.seguridad import hash_token
from app.models import CambioCorreo, EstadoUsuario, Usuario
from tests.conftest import ColaFalsa, bearer, crear_usuario_activo

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

#---CAMBIO DE CONTRASEÑA---
URL_CONTRASENA = "/api/v1/cuenta/contrasena"


async def test_cambiar_contrasena_correctamente(
    client: AsyncClient,
    token_cliente: str,
) -> None:
    respuesta = await client.patch(
        URL_CONTRASENA,
        json={
            "contrasena_actual": "Prueba123",
            "contrasena_nueva": "NuevaClave456",
        },
        headers=bearer(token_cliente),
    )

    assert respuesta.status_code == 200

    # La sesión anterior debe quedar invalidada.
    yo = await client.get(
        "/api/v1/auth/yo",
        headers=bearer(token_cliente),
    )
    assert yo.status_code == 401

    # La contraseña anterior ya no debe funcionar.
    login_anterior = await client.post(
        "/api/v1/auth/login",
        json={
            "correo": "cliente@example.com",
            "password": "Prueba123",
        },
    )
    assert login_anterior.status_code == 401

    # La nueva contraseña sí permite ingresar.
    login_nuevo = await client.post(
        "/api/v1/auth/login",
        json={
            "correo": "cliente@example.com",
            "password": "NuevaClave456",
        },
    )
    assert login_nuevo.status_code == 200


async def test_contrasena_actual_incorrecta(
    client: AsyncClient,
    token_cliente: str,
) -> None:
    respuesta = await client.patch(
        URL_CONTRASENA,
        json={
            "contrasena_actual": "Incorrecta123",
            "contrasena_nueva": "NuevaClave456",
        },
        headers=bearer(token_cliente),
    )

    assert respuesta.status_code == 400

    # La contraseña original debe seguir funcionando.
    login = await client.post(
        "/api/v1/auth/login",
        json={
            "correo": "cliente@example.com",
            "password": "Prueba123",
        },
    )

    assert login.status_code == 200


async def test_no_permite_misma_contrasena(
    client: AsyncClient,
    token_cliente: str,
) -> None:
    respuesta = await client.patch(
        URL_CONTRASENA,
        json={
            "contrasena_actual": "Prueba123",
            "contrasena_nueva": "Prueba123",
        },
        headers=bearer(token_cliente),
    )

    assert respuesta.status_code == 400


async def test_contrasena_nueva_invalida(
    client: AsyncClient,
    token_cliente: str,
) -> None:
    respuesta = await client.patch(
        URL_CONTRASENA,
        json={
            "contrasena_actual": "Prueba123",
            "contrasena_nueva": "123",
        },
        headers=bearer(token_cliente),
    )

    assert respuesta.status_code == 422


async def test_cambiar_contrasena_sin_token(
    client: AsyncClient,
) -> None:
    respuesta = await client.patch(
        URL_CONTRASENA,
        json={
            "contrasena_actual": "Prueba123",
            "contrasena_nueva": "NuevaClave456",
        },
    )

    assert respuesta.status_code == 401

#---CAMBIO DE CORREO---
URL_CORREO = "/api/v1/cuenta/correo"
URL_CONFIRMAR = "/api/v1/cuenta/correo/confirmar"


def obtener_token_correo(cola: ColaFalsa) -> str:
    funcion, args = cola.trabajos[-1]

    assert funcion == "enviar_correo"

    coincidencia = re.search(
        r"/confirmar-correo/([A-Za-z0-9_-]+)",
        args[2],
    )
    assert coincidencia is not None

    return coincidencia.group(1)


async def test_cambiar_correo_correctamente(
    client: AsyncClient,
    token_cliente: str,
    cola: ColaFalsa,
) -> None:
    respuesta = await client.post(
        URL_CORREO,
        json={
            "nuevo_correo": "nuevo@example.com",
            "contrasena_actual": "Prueba123",
        },
        headers=bearer(token_cliente),
    )

    assert respuesta.status_code == 202
    assert cola.trabajos[-1][1][0] == "nuevo@example.com"

    # Antes de confirmar, el correo sigue siendo el anterior.
    yo = await client.get(
        "/api/v1/auth/yo",
        headers=bearer(token_cliente),
    )
    assert yo.json()["correo"] == "cliente@example.com"

    token = obtener_token_correo(cola)

    confirmacion = await client.post(
        URL_CONFIRMAR,
        json={"token": token},
    )

    assert confirmacion.status_code == 200

    # La sesión anterior queda revocada.
    yo = await client.get(
        "/api/v1/auth/yo",
        headers=bearer(token_cliente),
    )
    assert yo.status_code == 401

    # Ya no se puede iniciar sesión con el correo anterior.
    anterior = await client.post(
        "/api/v1/auth/login",
        json={
            "correo": "cliente@example.com",
            "password": "Prueba123",
        },
    )
    assert anterior.status_code == 401

    # El nuevo correo sí funciona.
    nuevo = await client.post(
        "/api/v1/auth/login",
        json={
            "correo": "nuevo@example.com",
            "password": "Prueba123",
        },
    )
    assert nuevo.status_code == 200


async def test_correo_duplicado(
    client: AsyncClient,
    token_cliente: str,
) -> None:
    await crear_usuario_activo("ocupado@example.com")

    respuesta = await client.post(
        URL_CORREO,
        json={
            "nuevo_correo": "ocupado@example.com",
            "contrasena_actual": "Prueba123",
        },
        headers=bearer(token_cliente),
    )

    assert respuesta.status_code == 409


async def test_contrasena_incorrecta_para_cambiar_correo(
    client: AsyncClient,
    token_cliente: str,
) -> None:
    respuesta = await client.post(
        URL_CORREO,
        json={
            "nuevo_correo": "nuevo@example.com",
            "contrasena_actual": "Incorrecta123",
        },
        headers=bearer(token_cliente),
    )

    assert respuesta.status_code == 400


async def test_cambio_correo_sin_autenticacion(
    client: AsyncClient,
) -> None:
    respuesta = await client.post(
        URL_CORREO,
        json={
            "nuevo_correo": "nuevo@example.com",
            "contrasena_actual": "Prueba123",
        },
    )

    assert respuesta.status_code == 401


async def test_confirmacion_no_puede_reutilizarse(
    client: AsyncClient,
    token_cliente: str,
    cola: ColaFalsa,
) -> None:
    await client.post(
        URL_CORREO,
        json={
            "nuevo_correo": "nuevo@example.com",
            "contrasena_actual": "Prueba123",
        },
        headers=bearer(token_cliente),
    )

    token = obtener_token_correo(cola)

    primera = await client.post(
        URL_CONFIRMAR,
        json={"token": token},
    )

    segunda = await client.post(
        URL_CONFIRMAR,
        json={"token": token},
    )

    assert primera.status_code == 200
    assert segunda.status_code == 400


async def test_token_correo_invalido(
    client: AsyncClient,
) -> None:
    respuesta = await client.post(
        URL_CONFIRMAR,
        json={"token": "token-inexistente-123456789"},
    )

    assert respuesta.status_code == 400

async def test_token_correo_vencido(
    client: AsyncClient,
    token_cliente: str,
    cola: ColaFalsa,
) -> None:
    respuesta = await client.post(
        URL_CORREO,
        json={
            "nuevo_correo": "nuevo@example.com",
            "contrasena_actual": "Prueba123",
        },
        headers=bearer(token_cliente),
    )

    assert respuesta.status_code == 202

    token = obtener_token_correo(cola)

    # Simulamos que el enlace ya venció.
    async with SessionLocal() as db:
        registro = await db.scalar(
            select(CambioCorreo).where(
                CambioCorreo.token_hash == hash_token(token)
            )
        )

        assert registro is not None

        registro.expira_en = datetime.now(UTC) - timedelta(minutes=1)
        await db.commit()

    confirmacion = await client.post(
        URL_CONFIRMAR,
        json={"token": token},
    )

    assert confirmacion.status_code == 400

    # El correo original debe mantenerse.
    yo = await client.get(
        "/api/v1/auth/yo",
        headers=bearer(token_cliente),
    )

    assert yo.status_code == 200
    assert yo.json()["correo"] == "cliente@example.com"

async def test_nueva_solicitud_invalida_token_anterior(
    client: AsyncClient,
    token_cliente: str,
    cola: ColaFalsa,
) -> None:

    primera = await client.post(
        URL_CORREO,
        json={
            "nuevo_correo": "primero@example.com",
            "contrasena_actual": "Prueba123",
        },
        headers=bearer(token_cliente),
    )

    assert primera.status_code == 202
    token_anterior = obtener_token_correo(cola)

    segunda = await client.post(
        URL_CORREO,
        json={
            "nuevo_correo": "segundo@example.com",
            "contrasena_actual": "Prueba123",
        },
        headers=bearer(token_cliente),
    )

    assert segunda.status_code == 202
    token_nuevo = obtener_token_correo(cola)

    # El primer enlace ya no debe funcionar.
    respuesta_anterior = await client.post(
        URL_CONFIRMAR,
        json={"token": token_anterior},
    )

    assert respuesta_anterior.status_code == 400

    # El segundo enlace debe funcionar.
    respuesta_nueva = await client.post(
        URL_CONFIRMAR,
        json={"token": token_nuevo},
    )

    assert respuesta_nueva.status_code == 200

URL_ELIMINAR = "/api/v1/cuenta"

DATOS_ELIMINACION = {
    "contrasena_actual": "Prueba123",
    "confirmacion": "ELIMINAR MI CUENTA",
}


async def test_eliminar_cuenta_correctamente(
    client: AsyncClient,
    token_cliente: str,
) -> None:

    respuesta = await client.request(
        "DELETE",
        URL_ELIMINAR,
        json=DATOS_ELIMINACION,
        headers=bearer(token_cliente),
    )

    assert respuesta.status_code == 200

    # La cuenta permanece registrada, pero dada de baja.
    async with SessionLocal() as db:
        usuario = await db.scalar(
            select(Usuario).where(
                Usuario.correo == "cliente@example.com"
            )
        )

        assert usuario is not None
        assert usuario.estado == EstadoUsuario.BAJA

    # El token anterior deja de funcionar.
    yo = await client.get(
        "/api/v1/auth/yo",
        headers=bearer(token_cliente),
    )

    assert yo.status_code == 401

    # La cuenta ya no puede iniciar sesión.
    login = await client.post(
        "/api/v1/auth/login",
        json={
            "correo": "cliente@example.com",
            "password": "Prueba123",
        },
    )

    assert login.status_code == 401


async def test_eliminar_contrasena_incorrecta(
    client: AsyncClient,
    token_cliente: str,
) -> None:

    datos = DATOS_ELIMINACION | {
        "contrasena_actual": "Incorrecta123"
    }

    respuesta = await client.request(
        "DELETE",
        URL_ELIMINAR,
        json=datos,
        headers=bearer(token_cliente),
    )

    assert respuesta.status_code == 400

    # El usuario debe continuar activo.
    yo = await client.get(
        "/api/v1/auth/yo",
        headers=bearer(token_cliente),
    )

    assert yo.status_code == 200


async def test_eliminar_sin_confirmacion_correcta(
    client: AsyncClient,
    token_cliente: str,
) -> None:

    datos = DATOS_ELIMINACION | {
        "confirmacion": "ELIMINAR"
    }

    respuesta = await client.request(
        "DELETE",
        URL_ELIMINAR,
        json=datos,
        headers=bearer(token_cliente),
    )

    assert respuesta.status_code == 422

    yo = await client.get(
        "/api/v1/auth/yo",
        headers=bearer(token_cliente),
    )

    assert yo.status_code == 200


async def test_eliminar_sin_autenticacion(
    client: AsyncClient,
) -> None:

    respuesta = await client.request(
        "DELETE",
        URL_ELIMINAR,
        json=DATOS_ELIMINACION,
    )

    assert respuesta.status_code == 401


async def test_admin_no_puede_eliminar_su_cuenta(
    client: AsyncClient,
    token_admin: str,
) -> None:

    respuesta = await client.request(
        "DELETE",
        URL_ELIMINAR,
        json=DATOS_ELIMINACION,
        headers=bearer(token_admin),
    )

    assert respuesta.status_code == 403

    # El administrador sigue activo.
    yo = await client.get(
        "/api/v1/auth/yo",
        headers=bearer(token_admin),
    )

    assert yo.status_code == 200


async def test_baja_revoca_todas_las_sesiones(
    client: AsyncClient,
    token_cliente: str,
) -> None:

    # Creamos una segunda sesión del mismo usuario.
    segundo_login = await client.post(
        "/api/v1/auth/login",
        json={
            "correo": "cliente@example.com",
            "password": "Prueba123",
        },
    )

    assert segundo_login.status_code == 200

    segundo_token = segundo_login.json()["access_token"]

    respuesta = await client.request(
        "DELETE",
        URL_ELIMINAR,
        json=DATOS_ELIMINACION,
        headers=bearer(token_cliente),
    )

    assert respuesta.status_code == 200

    # Las dos sesiones deben quedar invalidadas.
    for token in [token_cliente, segundo_token]:
        yo = await client.get(
            "/api/v1/auth/yo",
            headers=bearer(token),
        )

        assert yo.status_code == 401
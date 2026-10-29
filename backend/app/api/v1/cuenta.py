from fastapi import APIRouter, HTTPException, Response, status

from app.api.deps import Cola, SesionDB, UsuarioActual
from app.schemas.auth import TokenEntrada
from app.schemas.comunes import Mensaje
from app.schemas.cuenta import (
    CambiarContrasenaEntrada,
    CambiarCorreoEntrada,
    DatosCuentaActualizar,
    DatosCuentaSalida,
    EliminarCuentaEntrada,
)
from app.services import cuenta

router = APIRouter(
    prefix="/cuenta",
    tags=["cuenta"],
)


@router.patch(
    "/datos",
    response_model=DatosCuentaSalida,
    summary="Editar mis datos",
    description=("Permite al usuario autenticado actualizar su nombre y el nombre de su empresa."),
)
async def editar_mis_datos(
    datos: DatosCuentaActualizar,
    usuario: UsuarioActual,
    db: SesionDB,
) -> DatosCuentaSalida:

    usuario_actualizado = await cuenta.actualizar_datos(
        db,
        usuario,
        datos,
    )

    return DatosCuentaSalida.model_validate(usuario_actualizado)


@router.patch(
    "/contrasena",
    response_model=Mensaje,
    summary="Cambiar mi contraseña",
    description=(
        "Permite al usuario autenticado cambiar su contraseña y revoca sus sesiones activas."
    ),  # noqa: E501
)
async def cambiar_mi_contrasena(
    datos: CambiarContrasenaEntrada,
    usuario: UsuarioActual,
    db: SesionDB,
    response: Response,
) -> Mensaje:
    await cuenta.cambiar_contrasena(
        db,
        usuario,
        datos,
    )

    response.delete_cookie(
        "ps_refresh",
        path="/api/v1/auth",
    )

    return Mensaje(mensaje=("Contraseña actualizada correctamente. Iniciá sesión nuevamente."))


@router.post(
    "/correo",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=Mensaje,
    summary="Solicitar cambio de correo",
    responses={
        400: {"description": "Solicitud inválida"},
        401: {"description": "No autenticado"},
        409: {"description": "Correo ya registrado"},
        503: {"description": "No se pudo encolar el correo"},
    },
)
async def solicitar_mi_cambio_correo(
    datos: CambiarCorreoEntrada,
    usuario: UsuarioActual,
    db: SesionDB,
    cola: Cola,
) -> Mensaje:
    encolado = await cuenta.solicitar_cambio_correo(
        db,
        usuario,
        datos,
        cola,
    )

    if not encolado:
        raise HTTPException(
            status_code=503,
            detail="No pudimos enviar el correo. Intentá nuevamente.",
        )

    return Mensaje(
        mensaje="Enviamos un enlace de confirmación al nuevo correo."
    )


@router.post(
    "/correo/confirmar",
    response_model=Mensaje,
    summary="Confirmar cambio de correo",
    responses={
        400: {"description": "Token inválido, usado o vencido"},
        409: {"description": "Correo ya registrado"},
    },
)
async def confirmar_mi_correo(
    datos: TokenEntrada,
    db: SesionDB,
    response: Response,
) -> Mensaje:
    await cuenta.confirmar_cambio_correo(
        db,
        datos.token,
    )

    response.delete_cookie(
        "ps_refresh",
        path="/api/v1/auth",
    )

    return Mensaje(
        mensaje="Correo actualizado. Iniciá sesión nuevamente."
    )

#---DAR DE BAJA LA CUENTA---

@router.delete(
    "",
    response_model=Mensaje,
    summary="Dar de baja mi cuenta",
    description=(
        "Permite al cliente autenticado solicitar la baja lógica "
        "de su cuenta. Requiere la contraseña actual y una "
        "confirmación explícita. Revoca sesiones y tokens pendientes."
    ),
    responses={
        400: {"description": "Contraseña incorrecta o cuenta inválida"},
        401: {"description": "No autenticado"},
        403: {"description": "Operación no permitida"},
        422: {"description": "Error de validación"},
    },
)
async def eliminar_mi_cuenta(
    datos: EliminarCuentaEntrada,
    usuario: UsuarioActual,
    db: SesionDB,
    response: Response,
) -> Mensaje:

    await cuenta.dar_de_baja_cuenta(
        db,
        usuario,
        datos,
    )

    response.delete_cookie(
        "ps_refresh",
        path="/api/v1/auth",
    )

    return Mensaje(
        mensaje=(
            "Tu cuenta fue dada de baja correctamente. "
            "Se cerraron todas tus sesiones."
        )
    )
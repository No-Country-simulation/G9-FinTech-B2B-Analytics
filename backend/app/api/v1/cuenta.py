from fastapi import APIRouter

from app.api.deps import SesionDB, UsuarioActual
from app.schemas.cuenta import (
    DatosCuentaActualizar,
    DatosCuentaSalida,
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

    return DatosCuentaSalida.model_validate(
        usuario_actualizado
    )
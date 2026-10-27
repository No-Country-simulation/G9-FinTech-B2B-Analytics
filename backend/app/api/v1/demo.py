from fastapi import APIRouter, status

from app.api.deps import SesionDB
from app.schemas.demo import SolicitudDemoEntrada, SolicitudDemoSalida
from app.services import solicitudes

router = APIRouter(prefix="/demo", tags=["demo"])


@router.post(
    "/solicitudes", response_model=SolicitudDemoSalida, status_code=status.HTTP_201_CREATED
)
async def crear_solicitud(datos: SolicitudDemoEntrada, db: SesionDB) -> SolicitudDemoSalida:
    solicitud = await solicitudes.crear_solicitud(db, datos)
    return SolicitudDemoSalida.model_validate(solicitud)

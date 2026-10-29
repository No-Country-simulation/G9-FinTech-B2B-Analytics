import httpx
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import SesionDB, requiere_admin
from app.schemas.cotizaciones import CotizacionSalida
from app.services import cotizaciones

router = APIRouter(
    prefix="/admin/cotizaciones",
    tags=["admin · cotizaciones"],
    dependencies=[Depends(requiere_admin)],
)


@router.get("", response_model=list[CotizacionSalida])
async def ultimas(db: SesionDB) -> list[CotizacionSalida]:
    return [CotizacionSalida.model_validate(c) for c in await cotizaciones.ultimas_cotizaciones(db)]


@router.post(
    "/actualizar", response_model=list[CotizacionSalida], status_code=status.HTTP_201_CREATED
)
async def actualizar(db: SesionDB) -> list[CotizacionSalida]:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await cotizaciones.ingestar_cotizaciones(db, client)
    except cotizaciones.ErrorFuente:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, "Ninguna fuente de cotizaciones respondió"
        ) from None
    return [CotizacionSalida.model_validate(c) for c in await cotizaciones.ultimas_cotizaciones(db)]

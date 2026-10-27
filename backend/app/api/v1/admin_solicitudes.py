from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import SesionDB, requiere_admin
from app.schemas.comunes import Pagina
from app.schemas.demo import SolicitudDemoSalida
from app.services import solicitudes

router = APIRouter(
    prefix="/admin/solicitudes",
    tags=["admin · solicitudes"],
    dependencies=[Depends(requiere_admin)],
)


@router.get("", response_model=Pagina[SolicitudDemoSalida])
async def listar_solicitudes(
    db: SesionDB,
    pagina: Annotated[int, Query(ge=1)] = 1,
    tamano: Annotated[int, Query(ge=1, le=100)] = 20,
) -> Pagina[SolicitudDemoSalida]:
    items, total = await solicitudes.listar_solicitudes(db, pagina, tamano)
    return Pagina[SolicitudDemoSalida](
        items=[SolicitudDemoSalida.model_validate(s) for s in items],
        total=total,
        pagina=pagina,
        tamano=tamano,
    )

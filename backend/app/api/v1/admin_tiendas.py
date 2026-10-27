from fastapi import APIRouter, Depends

from app.api.deps import SesionDB, requiere_admin
from app.schemas.tiendas import TiendaSalida
from app.services import tiendas

router = APIRouter(
    prefix="/admin/tiendas", tags=["admin · tiendas"], dependencies=[Depends(requiere_admin)]
)


@router.get("", response_model=list[TiendaSalida])
async def listar_catalogo(db: SesionDB) -> list[TiendaSalida]:
    return [TiendaSalida.model_validate(t) for t in await tiendas.listar_catalogo(db)]

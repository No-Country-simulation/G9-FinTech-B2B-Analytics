from fastapi import APIRouter, Depends

from app.api.deps import DbSession, require_admin
from app.schemas.stores import StoreOutput
from app.services import stores

router = APIRouter(
    prefix="/admin/stores", tags=["admin · stores"], dependencies=[Depends(require_admin)]
)


@router.get("", response_model=list[StoreOutput])
async def list_catalog(db: DbSession) -> list[StoreOutput]:
    return [StoreOutput.model_validate(s) for s in await stores.list_catalog(db)]

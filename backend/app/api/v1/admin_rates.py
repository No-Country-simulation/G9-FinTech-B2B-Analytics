import httpx
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import DbSession, require_admin
from app.schemas.rates import RateOutput
from app.services import rates

router = APIRouter(
    prefix="/admin/rates",
    tags=["admin · rates"],
    dependencies=[Depends(require_admin)],
)


@router.get("", response_model=list[RateOutput])
async def latest(db: DbSession) -> list[RateOutput]:
    return [RateOutput.model_validate(r) for r in await rates.latest_rates(db)]


@router.post("/refresh", response_model=list[RateOutput], status_code=status.HTTP_201_CREATED)
async def refresh(db: DbSession) -> list[RateOutput]:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await rates.ingest_rates(db, client)
    except rates.SourceError:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, "Ninguna fuente de cotizaciones respondió"
        ) from None
    return [RateOutput.model_validate(r) for r in await rates.latest_rates(db)]

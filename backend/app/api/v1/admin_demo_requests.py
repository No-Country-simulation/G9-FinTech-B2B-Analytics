from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import DbSession, require_admin
from app.schemas.common import Page
from app.schemas.demo import DemoRequestOutput
from app.services import demo_requests

router = APIRouter(
    prefix="/admin/demo-requests",
    tags=["admin · demo requests"],
    dependencies=[Depends(require_admin)],
)


@router.get("", response_model=Page[DemoRequestOutput])
async def list_demo_requests(
    db: DbSession,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> Page[DemoRequestOutput]:
    items, total = await demo_requests.list_requests(db, page, size)
    return Page[DemoRequestOutput](
        items=[DemoRequestOutput.model_validate(r) for r in items],
        total=total,
        page=page,
        size=size,
    )

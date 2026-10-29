from fastapi import APIRouter, status

from app.api.deps import DbSession
from app.schemas.demo import DemoRequestInput, DemoRequestOutput
from app.services import demo_requests

router = APIRouter(prefix="/demo", tags=["demo"])


@router.post("/requests", response_model=DemoRequestOutput, status_code=status.HTTP_201_CREATED)
async def create_request(data: DemoRequestInput, db: DbSession) -> DemoRequestOutput:
    request = await demo_requests.create_request(db, data)
    return DemoRequestOutput.model_validate(request)

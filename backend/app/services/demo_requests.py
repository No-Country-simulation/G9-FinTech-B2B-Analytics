from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import DemoRequest
from app.schemas.demo import DemoRequestInput


async def create_request(db: AsyncSession, data: DemoRequestInput) -> DemoRequest:
    request = DemoRequest(**data.model_dump())
    request.email = request.email.lower()
    db.add(request)
    await db.commit()
    await db.refresh(request)
    return request


async def list_requests(db: AsyncSession, page: int, size: int) -> tuple[list[DemoRequest], int]:
    total = await db.scalar(select(func.count()).select_from(DemoRequest)) or 0
    rows = await db.scalars(
        select(DemoRequest)
        .order_by(DemoRequest.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    return list(rows), total

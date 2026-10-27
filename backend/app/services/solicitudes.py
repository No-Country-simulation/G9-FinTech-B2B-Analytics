from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import SolicitudDemo
from app.schemas.demo import SolicitudDemoEntrada


async def crear_solicitud(db: AsyncSession, datos: SolicitudDemoEntrada) -> SolicitudDemo:
    solicitud = SolicitudDemo(**datos.model_dump())
    solicitud.correo = solicitud.correo.lower()
    db.add(solicitud)
    await db.commit()
    await db.refresh(solicitud)
    return solicitud


async def listar_solicitudes(
    db: AsyncSession, pagina: int, tamano: int
) -> tuple[list[SolicitudDemo], int]:
    total = await db.scalar(select(func.count()).select_from(SolicitudDemo)) or 0
    filas = await db.scalars(
        select(SolicitudDemo)
        .order_by(SolicitudDemo.creada_en.desc())
        .offset((pagina - 1) * tamano)
        .limit(tamano)
    )
    return list(filas), total

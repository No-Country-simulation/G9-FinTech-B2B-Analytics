import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Precio, Publicacion, TipoCotizacion
from app.services import cotizaciones

CENTAVOS = Decimal("0.01")


@dataclass(frozen=True)
class ObservacionScrapeada:
    """Lo que entrega cada scraper por producto. Es el contrato entre scraping y base."""

    tienda_id: uuid.UUID
    codigo_externo: str
    nombre: str
    url: str
    precio_actual: Decimal | None
    precio_tachado: Decimal | None = None
    disponible: bool = True
    categoria: str | None = None
    gramaje: Decimal | None = None
    unidad: str | None = None


async def registrar_observacion(
    db: AsyncSession, obs: ObservacionScrapeada, capturado_en: datetime | None = None
) -> Precio | None:
    """Guarda la publicación (si es nueva) y el precio. Devuelve None si no hay precio actual."""
    if obs.precio_actual is None or obs.precio_actual <= 0:
        return None

    es_promo = obs.precio_tachado is not None and obs.precio_tachado > obs.precio_actual
    precio_regular = obs.precio_tachado if es_promo else obs.precio_actual

    publicacion_id = await db.scalar(
        insert(Publicacion)
        .values(
            tienda_id=obs.tienda_id,
            codigo_externo=obs.codigo_externo,
            nombre=obs.nombre,
            url=obs.url,
            categoria_origen=obs.categoria,
        )
        .on_conflict_do_update(
            index_elements=["tienda_id", "codigo_externo"],
            set_={
                "nombre": obs.nombre,
                "url": obs.url,
                "categoria_origen": obs.categoria,
                "actualizado_en": func.now(),
            },
        )
        .returning(Publicacion.id)
    )

    ultimas = await cotizaciones.ultimas_cotizaciones(db)
    venta = {c.tipo: c.venta for c in ultimas}
    tc_oficial = venta.get(TipoCotizacion.OFICIAL)
    tc_blue = venta.get(TipoCotizacion.BLUE)

    def a_usd(tc: Decimal | None) -> Decimal | None:
        return (obs.precio_actual / tc).quantize(CENTAVOS) if tc else None

    precio = Precio(
        publicacion_id=publicacion_id,
        capturado_en=capturado_en or datetime.now(UTC),
        precio_local=obs.precio_actual,
        precio_tachado=obs.precio_tachado,
        precio_regular=precio_regular,
        es_promo=es_promo,
        disponible=obs.disponible,
        gramaje=obs.gramaje,
        unidad=obs.unidad,
        tc_oficial=tc_oficial,
        tc_blue=tc_blue,
        cotizado_en=max((c.cotizado_en for c in ultimas), default=None),
        precio_usd_oficial=a_usd(tc_oficial),
        precio_usd_blue=a_usd(tc_blue),
    )
    db.add(precio)
    await db.commit()
    return precio

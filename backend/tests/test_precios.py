import uuid
from datetime import UTC, datetime
from decimal import Decimal

from app.services.precios import ObservacionScrapeada, registrar_observacion
from sqlalchemy import func, select

from app.core.database import SessionLocal
from app.models import Cotizacion, Precio, Publicacion, Rubro, Tienda, TipoCotizacion


async def preparar() -> uuid.UUID:
    async with SessionLocal() as db:
        tienda = Tienda(
            nombre="Tienda T",
            slug="tienda-t",
            url_base="https://t.example.com",
            rubro=Rubro.ELECTRO,
            scraper_clave="tienda_t",
        )
        ahora = datetime.now(UTC)
        db.add_all(
            [
                tienda,
                Cotizacion(
                    fuente="dolarapi",
                    tipo=TipoCotizacion.OFICIAL,
                    cotizado_en=ahora,
                    venta=Decimal("1500"),
                ),
                Cotizacion(
                    fuente="dolarapi",
                    tipo=TipoCotizacion.BLUE,
                    cotizado_en=ahora,
                    venta=Decimal("1600"),
                ),
            ]
        )
        await db.commit()
        return tienda.id


def obs(tienda_id: uuid.UUID, **cambios: object) -> ObservacionScrapeada:
    base = {
        "tienda_id": tienda_id,
        "codigo_externo": "SKU-1",
        "nombre": "Smart TV 50",
        "url": "https://t.example.com/tv",
        "precio_actual": Decimal("750"),
        "precio_tachado": Decimal("1000"),
    }
    return ObservacionScrapeada(**(base | cambios))


async def test_promo_calcula_regular_y_usd() -> None:
    tienda_id = await preparar()
    async with SessionLocal() as db:
        precio = await registrar_observacion(db, obs(tienda_id))

    assert precio is not None
    assert precio.es_promo is True
    assert precio.precio_regular == Decimal("1000")
    assert precio.precio_usd_oficial == Decimal("0.50")
    assert precio.precio_usd_blue == Decimal("0.47")


async def test_sin_tachado_no_es_promo() -> None:
    tienda_id = await preparar()
    async with SessionLocal() as db:
        precio = await registrar_observacion(db, obs(tienda_id, precio_tachado=None))

    assert precio is not None
    assert precio.es_promo is False
    assert precio.precio_regular == Decimal("750")


async def test_sin_precio_actual_no_se_guarda() -> None:
    tienda_id = await preparar()
    async with SessionLocal() as db:
        assert await registrar_observacion(db, obs(tienda_id, precio_actual=None)) is None
        assert await db.scalar(select(func.count()).select_from(Precio)) == 0


async def test_misma_publicacion_se_reutiliza() -> None:
    tienda_id = await preparar()
    async with SessionLocal() as db:
        await registrar_observacion(db, obs(tienda_id))
        await registrar_observacion(db, obs(tienda_id, precio_actual=Decimal("800")))
        assert await db.scalar(select(func.count()).select_from(Publicacion)) == 1
        assert await db.scalar(select(func.count()).select_from(Precio)) == 2

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

import httpx
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Cotizacion, TipoCotizacion

log = logging.getLogger(__name__)

URL_DOLARAPI = "https://dolarapi.com/v1/dolares/{casa}"
URL_BLUELYTICS = "https://api.bluelytics.com.ar/v2/latest"


class ErrorFuente(Exception):
    """Ninguna fuente de cotizaciones respondió bien."""


@dataclass(frozen=True)
class CotizacionLeida:
    fuente: str
    tipo: TipoCotizacion
    compra: Decimal | None
    venta: Decimal
    fecha_fuente: datetime | None


def _dec(valor: object) -> Decimal:
    return Decimal(str(valor))


async def _leer_dolarapi(client: httpx.AsyncClient) -> list[CotizacionLeida]:
    resultado = []
    for tipo in TipoCotizacion:
        respuesta = await client.get(URL_DOLARAPI.format(casa=tipo.value))
        respuesta.raise_for_status()
        datos = respuesta.json()
        resultado.append(
            CotizacionLeida(
                fuente="dolarapi",
                tipo=tipo,
                compra=_dec(datos["compra"]),
                venta=_dec(datos["venta"]),
                fecha_fuente=datetime.fromisoformat(datos["fechaActualizacion"]),
            )
        )
    return resultado


async def _leer_bluelytics(client: httpx.AsyncClient) -> list[CotizacionLeida]:
    respuesta = await client.get(URL_BLUELYTICS)
    respuesta.raise_for_status()
    datos = respuesta.json()
    fecha = datetime.fromisoformat(datos["last_update"])
    return [
        CotizacionLeida(
            fuente="bluelytics",
            tipo=tipo,
            compra=_dec(datos[tipo.value]["value_buy"]),
            venta=_dec(datos[tipo.value]["value_sell"]),
            fecha_fuente=fecha,
        )
        for tipo in TipoCotizacion
    ]


FUENTES = (("dolarapi", _leer_dolarapi), ("bluelytics", _leer_bluelytics))


async def obtener_cotizaciones(client: httpx.AsyncClient) -> list[CotizacionLeida]:
    """Prueba las fuentes en orden y devuelve la primera que responde bien."""
    for nombre, leer in FUENTES:
        try:
            return await leer(client)
        except (httpx.HTTPError, KeyError, ValueError, ArithmeticError) as exc:
            log.warning("La fuente %s falló: %s", nombre, exc)
    raise ErrorFuente("Ninguna fuente de cotizaciones respondió")


async def ingestar_cotizaciones(db: AsyncSession, client: httpx.AsyncClient) -> int:
    """Consulta la fuente y guarda oficial y blue con el mismo cotizado_en.
    Devuelve cuántas guardó."""
    leidas = await obtener_cotizaciones(client)
    ahora = datetime.now(UTC)
    filas = [
        {
            "fuente": c.fuente,
            "tipo": c.tipo,
            "cotizado_en": ahora,
            "compra": c.compra,
            "venta": c.venta,
            "fecha_fuente": c.fecha_fuente,
        }
        for c in leidas
    ]
    await db.execute(insert(Cotizacion).values(filas).on_conflict_do_nothing())
    await db.commit()
    return len(filas)


async def ultimas_cotizaciones(db: AsyncSession) -> list[Cotizacion]:
    """La cotización más reciente de cada tipo."""
    filas = await db.scalars(
        select(Cotizacion)
        .distinct(Cotizacion.tipo)
        .order_by(Cotizacion.tipo, Cotizacion.cotizado_en.desc())
    )
    return list(filas)

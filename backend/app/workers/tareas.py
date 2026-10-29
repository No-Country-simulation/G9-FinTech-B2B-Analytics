import logging

import aiosmtplib
import httpx
from arq import Retry, cron

from app.core.cache import ajustes_arq
from app.core.database import SessionLocal
from app.services import cotizaciones
from app.services.correo import enviar_smtp

log = logging.getLogger(__name__)

MAX_INTENTOS = 5


async def iniciar(ctx: dict) -> None:
    """Se ejecuta una vez al arrancar el worker. Crea el cliente HTTP compartido."""
    ctx["http"] = httpx.AsyncClient(timeout=10)


async def cerrar(ctx: dict) -> None:
    await ctx["http"].aclose()


async def enviar_correo(ctx: dict, para: str, asunto: str, texto: str, cuerpo_html: str) -> None:
    try:
        await enviar_smtp(para, asunto, texto, cuerpo_html)
    except (aiosmtplib.SMTPException, OSError) as exc:
        if ctx["job_try"] >= MAX_INTENTOS:
            raise
        raise Retry(defer=ctx["job_try"] * 30) from exc


async def ingestar_cotizaciones(ctx: dict) -> int:
    """Job horario: guarda la cotización oficial y blue. Si no hay fuente, registra y sigue."""
    try:
        async with SessionLocal() as db:
            return await cotizaciones.ingestar_cotizaciones(db, ctx["http"])
    except cotizaciones.ErrorFuente:
        log.error("Ingesta de cotizaciones: ninguna fuente respondió")
        return 0


class WorkerSettings:
    functions = [enviar_correo]
    cron_jobs = [cron(ingestar_cotizaciones, minute=0)]  # al minuto 0 de cada hora
    on_startup = iniciar
    on_shutdown = cerrar
    redis_settings = ajustes_arq
    max_tries = MAX_INTENTOS

import logging

import aiosmtplib
import httpx
from arq import Retry, cron

from app.core.cache import arq_settings
from app.core.database import SessionLocal
from app.services import mail, rates

log = logging.getLogger(__name__)

MAX_TRIES = 5


async def startup(ctx: dict) -> None:
    """Runs once when the worker starts. Creates the shared HTTP client."""
    ctx["http"] = httpx.AsyncClient(timeout=10)


async def shutdown(ctx: dict) -> None:
    await ctx["http"].aclose()


async def send_email(ctx: dict, to: str, subject: str, text: str, body_html: str) -> None:
    try:
        await mail.send_smtp(to, subject, text, body_html)
    except (aiosmtplib.SMTPException, OSError) as exc:
        if ctx["job_try"] >= MAX_TRIES:
            raise
        raise Retry(defer=ctx["job_try"] * 30) from exc


async def ingest_rates(ctx: dict) -> int:
    """Hourly job: stores the official and blue rates. If there is no source, logs and moves on."""
    try:
        async with SessionLocal() as db:
            return await rates.ingest_rates(db, ctx["http"])
    except rates.SourceError:
        log.error("Rate ingestion: no source answered")
        return 0


class WorkerSettings:
    functions = [send_email]
    cron_jobs = [cron(ingest_rates, minute=0)]  # at minute 0 of every hour
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = arq_settings
    max_tries = MAX_TRIES

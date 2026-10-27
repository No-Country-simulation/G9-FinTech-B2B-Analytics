import aiosmtplib
from arq import Retry

from app.core.cache import ajustes_arq
from app.services.correo import enviar_smtp

MAX_INTENTOS = 5


async def enviar_correo(ctx: dict, para: str, asunto: str, texto: str, cuerpo_html: str) -> None:
    try:
        await enviar_smtp(para, asunto, texto, cuerpo_html)
    except (aiosmtplib.SMTPException, OSError) as exc:
        if ctx["job_try"] >= MAX_INTENTOS:
            raise
        raise Retry(defer=ctx["job_try"] * 30) from exc


class WorkerSettings:
    functions = [enviar_correo]
    redis_settings = ajustes_arq
    max_tries = MAX_INTENTOS

import html
import logging
from email.message import EmailMessage
from typing import Protocol

import aiosmtplib

from app.core.config import settings
from app.models import User

log = logging.getLogger(__name__)


class TaskQueue(Protocol):
    async def enqueue_job(self, function: str, *args: object, **kwargs: object) -> object: ...


def _build_message(name: str, intro: str, link: str, button: str) -> tuple[str, str]:
    text = (
        f"Hola {name}:\n\n{intro}\n\n{link}\n\n"
        "Si no esperabas este correo, podés ignorarlo.\n\nEquipo de PriceScope"
    )
    body_html = (
        f"<p>Hola {html.escape(name)}:</p><p>{intro}</p>"
        f'<p><a href="{link}">{button}</a></p>'
        "<p>Si no esperabas este correo, podés ignorarlo.</p><p>Equipo de PriceScope</p>"
    )
    return text, body_html


async def _enqueue(queue: TaskQueue, to: str, subject: str, text: str, body_html: str) -> bool:
    try:
        await queue.enqueue_job("send_email", to, subject, text, body_html)
        return True
    except Exception:
        log.exception("Could not enqueue email for %s", to)
        return False


async def enqueue_welcome(queue: TaskQueue, user: User, token: str) -> bool:
    link = f"{settings.frontend_url}/definir-contrasena/{token}"
    intro = (
        "Creamos tu cuenta de PriceScope. Para ingresar, definí tu contraseña con este enlace "
        f"(vence en {settings.set_password_token_hours} horas):"
    )
    text, body_html = _build_message(user.name, intro, link, "Definir mi contraseña")
    return await _enqueue(queue, user.email, "Tu cuenta de PriceScope está lista", text, body_html)


async def enqueue_recovery(queue: TaskQueue, user: User, token: str) -> bool:
    link = f"{settings.frontend_url}/restablecer/{token}"
    intro = (
        "Recibimos un pedido para restablecer tu contraseña. Usá este enlace "
        f"(vence en {settings.reset_token_minutes} minutos):"
    )
    text, body_html = _build_message(user.name, intro, link, "Restablecer mi contraseña")
    return await _enqueue(
        queue, user.email, "Restablecé tu contraseña de PriceScope", text, body_html
    )


async def send_smtp(to: str, subject: str, text: str, body_html: str) -> None:
    message = EmailMessage()
    message["From"] = settings.mail_sender
    message["To"] = to
    message["Subject"] = subject
    message.set_content(text)
    message.add_alternative(body_html, subtype="html")
    await aiosmtplib.send(
        message,
        hostname=settings.smtp_host,
        port=settings.smtp_port,
        username=settings.smtp_user,
        password=settings.smtp_password,
        start_tls=settings.smtp_tls,
    )


async def enqueue_email_change_confirmation(
    queue: TaskQueue,
    name: str,
    new_email: str,
    token: str,
) -> bool:
    link = f"{settings.frontend_url}/confirmar-correo/{token}"

    intro = (
        "Solicitaste cambiar el correo de tu cuenta de PriceScope. "
        "Confirmá tu nueva dirección con este enlace "
        f"(vence en {settings.email_change_token_minutes} minutos):"
    )

    text, body_html = _build_message(
        name,
        intro,
        link,
        "Confirmar mi nuevo correo",
    )

    return await _enqueue(
        queue,
        new_email,
        "Confirmá tu nuevo correo de PriceScope",
        text,
        body_html,
    )

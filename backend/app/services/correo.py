import html
import logging
from email.message import EmailMessage
from typing import Protocol

import aiosmtplib

from app.core.config import settings
from app.models import Usuario

log = logging.getLogger(__name__)


class ColaDeTareas(Protocol):
    async def enqueue_job(self, function: str, *args: object, **kwargs: object) -> object: ...


def _armar(nombre: str, intro: str, enlace: str, boton: str) -> tuple[str, str]:
    texto = (
        f"Hola {nombre}:\n\n{intro}\n\n{enlace}\n\n"
        "Si no esperabas este correo, podés ignorarlo.\n\nEquipo de PriceScope"
    )
    cuerpo_html = (
        f"<p>Hola {html.escape(nombre)}:</p><p>{intro}</p>"
        f'<p><a href="{enlace}">{boton}</a></p>'
        "<p>Si no esperabas este correo, podés ignorarlo.</p><p>Equipo de PriceScope</p>"
    )
    return texto, cuerpo_html


async def _encolar(
    cola: ColaDeTareas, para: str, asunto: str, texto: str, cuerpo_html: str
) -> bool:
    try:
        await cola.enqueue_job("enviar_correo", para, asunto, texto, cuerpo_html)
        return True
    except Exception:
        log.exception("No se pudo encolar el correo para %s", para)
        return False


async def encolar_bienvenida(cola: ColaDeTareas, usuario: Usuario, token: str) -> bool:
    enlace = f"{settings.frontend_url}/definir-contrasena/{token}"
    intro = (
        "Creamos tu cuenta de PriceScope. Para ingresar, definí tu contraseña con este enlace "
        f"(vence en {settings.token_definir_horas} horas):"
    )
    texto, cuerpo = _armar(usuario.nombre, intro, enlace, "Definir mi contraseña")
    return await _encolar(cola, usuario.correo, "Tu cuenta de PriceScope está lista", texto, cuerpo)


async def encolar_recuperacion(cola: ColaDeTareas, usuario: Usuario, token: str) -> bool:
    enlace = f"{settings.frontend_url}/restablecer/{token}"
    intro = (
        "Recibimos un pedido para restablecer tu contraseña. Usá este enlace "
        f"(vence en {settings.token_restablecer_minutos} minutos):"
    )
    texto, cuerpo = _armar(usuario.nombre, intro, enlace, "Restablecer mi contraseña")
    return await _encolar(
        cola, usuario.correo, "Restablecé tu contraseña de PriceScope", texto, cuerpo
    )


async def enviar_smtp(para: str, asunto: str, texto: str, cuerpo_html: str) -> None:
    mensaje = EmailMessage()
    mensaje["From"] = settings.correo_remitente
    mensaje["To"] = para
    mensaje["Subject"] = asunto
    mensaje.set_content(texto)
    mensaje.add_alternative(cuerpo_html, subtype="html")
    await aiosmtplib.send(
        mensaje,
        hostname=settings.smtp_host,
        port=settings.smtp_port,
        username=settings.smtp_usuario,
        password=settings.smtp_password,
        start_tls=settings.smtp_tls,
    )

async def encolar_confirmacion_cambio_correo(
    cola: ColaDeTareas,
    nombre: str,
    correo_nuevo: str,
    token: str,
) -> bool:
    enlace = f"{settings.frontend_url}/confirmar-correo/{token}"

    intro = (
        "Solicitaste cambiar el correo de tu cuenta de PriceScope. "
        "Confirmá tu nueva dirección con este enlace "
        f"(vence en {settings.token_cambio_correo_minutos} minutos):"
    )

    texto, cuerpo = _armar(
        nombre,
        intro,
        enlace,
        "Confirmar mi nuevo correo",
    )

    return await _encolar(
        cola,
        correo_nuevo,
        "Confirmá tu nuevo correo de PriceScope",
        texto,
        cuerpo,
    )
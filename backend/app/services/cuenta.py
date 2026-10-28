import asyncio
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.seguridad import generar_token_opaco, hash_token, hashear_password, verificar_password
from app.models import CambioCorreo, EstadoUsuario, Sesion, Usuario
from app.schemas.cuenta import CambiarContrasenaEntrada, CambiarCorreoEntrada, DatosCuentaActualizar
from app.services import correo
from app.services.correo import ColaDeTareas
from app.services.errores import Conflicto, ErrorNegocio


async def actualizar_datos(
    db: AsyncSession,
    usuario: Usuario,
    datos: DatosCuentaActualizar,
) -> Usuario:
    """Actualiza nombre y empresa del usuario autenticado."""

    cambios = datos.model_dump(exclude_unset=True)

    if not cambios:
        raise ErrorNegocio("Debés enviar al menos un dato para actualizar")

    if "nombre" in cambios:
        usuario.nombre = cambios["nombre"]

    if "empresa" in cambios:
        usuario.empresa = cambios["empresa"]

    await db.commit()
    await db.refresh(usuario)

    return usuario


async def cambiar_contrasena(
    db: AsyncSession,
    usuario: Usuario,
    datos: CambiarContrasenaEntrada,
) -> None:
    """Cambia la contraseña y revoca todas las sesiones del usuario."""

    if usuario.password_hash is None:
        raise ErrorNegocio("La cuenta no tiene una contraseña configurada")

    es_correcta = await asyncio.to_thread(
        verificar_password,
        datos.contrasena_actual,
        usuario.password_hash,
    )

    if not es_correcta:
        raise ErrorNegocio("La contraseña actual es incorrecta")

    es_igual = await asyncio.to_thread(
        verificar_password,
        datos.contrasena_nueva,
        usuario.password_hash,
    )

    if es_igual:
        raise ErrorNegocio("La nueva contraseña debe ser diferente de la actual")

    usuario.password_hash = await asyncio.to_thread(
        hashear_password,
        datos.contrasena_nueva,
    )

    ahora = datetime.now(UTC)

    await db.execute(
        update(Sesion)
        .where(
            Sesion.usuario_id == usuario.id,
            Sesion.revocada_en.is_(None),
        )
        .values(revocada_en=ahora)
    )

    await db.commit()
    

async def solicitar_cambio_correo(
    db: AsyncSession,
    usuario: Usuario,
    datos: CambiarCorreoEntrada,
    cola: ColaDeTareas,
) -> bool:
    """Solicita un cambio y envía un enlace al correo nuevo."""

    cuenta = await db.scalar(
        select(Usuario)
        .where(Usuario.id == usuario.id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )

    if cuenta is None or cuenta.estado != EstadoUsuario.ACTIVO:
        raise ErrorNegocio("La cuenta no está activa")

    if cuenta.password_hash is None:
        raise ErrorNegocio("La cuenta no tiene contraseña configurada")

    valida = await asyncio.to_thread(
        verificar_password,
        datos.contrasena_actual,
        cuenta.password_hash,
    )

    if not valida:
        raise ErrorNegocio("La contraseña actual es incorrecta")

    nuevo = datos.nuevo_correo.lower()

    if nuevo == cuenta.correo.lower():
        raise ErrorNegocio("El nuevo correo debe ser diferente del actual")

    existe = await db.scalar(
        select(Usuario.id).where(func.lower(Usuario.correo) == nuevo)
    )

    if existe is not None:
        raise Conflicto("El correo ya está registrado")

    ahora = datetime.now(UTC)

    # Anula las solicitudes anteriores del mismo usuario.
    await db.execute(
        update(CambioCorreo)
        .where(
            CambioCorreo.usuario_id == cuenta.id,
            CambioCorreo.usado_en.is_(None),
        )
        .values(usado_en=ahora)
    )

    token, token_hash = generar_token_opaco()

    db.add(
        CambioCorreo(
            usuario_id=cuenta.id,
            correo_nuevo=nuevo,
            token_hash=token_hash,
            expira_en=ahora
            + timedelta(minutes=settings.token_cambio_correo_minutos),
        )
    )

    await db.commit()

    return await correo.encolar_confirmacion_cambio_correo(
        cola,
        cuenta.nombre,
        nuevo,
        token,
    )

async def confirmar_cambio_correo(
    db: AsyncSession,
    token: str,
) -> None:
    """Confirma el correo y revoca las sesiones existentes."""

    registro = await db.scalar(
        select(CambioCorreo).where(
            CambioCorreo.token_hash == hash_token(token)
        )
    )

    if registro is None:
        raise ErrorNegocio("El enlace no es válido")

    # Primero bloqueamos al usuario para serializar sus cambios.
    usuario = await db.scalar(
        select(Usuario)
        .where(Usuario.id == registro.usuario_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )

    if usuario is None or usuario.estado != EstadoUsuario.ACTIVO:
        raise ErrorNegocio("La cuenta no está activa")

    # Volvemos a leer el registro bloqueado.
    registro = await db.scalar(
        select(CambioCorreo)
        .where(CambioCorreo.id == registro.id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )

    ahora = datetime.now(UTC)

    if registro is None or registro.usado_en is not None:
        raise ErrorNegocio("El enlace ya fue utilizado o no es válido")

    if registro.expira_en <= ahora:
        raise ErrorNegocio("El enlace de confirmación venció")

    existe = await db.scalar(
        select(Usuario.id).where(
            func.lower(Usuario.correo) == registro.correo_nuevo,
            Usuario.id != usuario.id,
        )
    )

    if existe is not None:
        raise Conflicto("El correo ya está registrado")

    usuario.correo = registro.correo_nuevo

    # Invalida todos los enlaces pendientes del usuario.
    await db.execute(
        update(CambioCorreo)
        .where(
            CambioCorreo.usuario_id == usuario.id,
            CambioCorreo.usado_en.is_(None),
        )
        .values(usado_en=ahora)
    )

    # Revoca todas las sesiones.
    await db.execute(
        update(Sesion)
        .where(
            Sesion.usuario_id == usuario.id,
            Sesion.revocada_en.is_(None),
        )
        .values(revocada_en=ahora)
    )

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise Conflicto("El correo ya está registrado") from None

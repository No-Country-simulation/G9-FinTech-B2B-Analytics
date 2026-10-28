from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Usuario
from app.schemas.cuenta import DatosCuentaActualizar
from app.services.errores import ErrorNegocio


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
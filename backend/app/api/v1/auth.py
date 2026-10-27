from fastapi import APIRouter, HTTPException, Request, Response, status

from app.api.deps import Cola, SesionDB, UsuarioActual
from app.core.config import settings
from app.schemas.auth import (
    CorreoEntrada,
    DefinirPasswordEntrada,
    EstadoTokenSalida,
    LoginEntrada,
    TokenEntrada,
    TokenSalida,
    UsuarioActualSalida,
)
from app.schemas.comunes import Mensaje
from app.services import autenticacion, tiendas, tokens, usuarios

router = APIRouter(prefix="/auth", tags=["auth"])

COOKIE_REFRESH = "ps_refresh"
RUTA_COOKIE = "/api/v1/auth"


def _guardar_refresh(response: Response, refresh: str) -> None:
    response.set_cookie(
        COOKIE_REFRESH,
        refresh,
        httponly=True,
        secure=settings.cookies_seguras,
        samesite="lax",
        max_age=settings.sesion_duracion_max_horas * 3600,
        path=RUTA_COOKIE,
    )


def _token_salida(access: str, rol: str) -> TokenSalida:
    return TokenSalida(access_token=access, expira_en=settings.access_token_minutos * 60, rol=rol)


@router.post("/login", response_model=TokenSalida)
async def login(
    datos: LoginEntrada, request: Request, response: Response, db: SesionDB
) -> TokenSalida:
    usuario = await autenticacion.autenticar(db, datos.correo, datos.password)
    if usuario is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Correo o contraseña incorrectos")
    access, refresh = await autenticacion.abrir_sesion(
        db, usuario, request.headers.get("user-agent")
    )
    _guardar_refresh(response, refresh)
    return _token_salida(access, usuario.rol)


@router.post("/refresh", response_model=TokenSalida)
async def refresh(request: Request, response: Response, db: SesionDB) -> TokenSalida:
    token = request.cookies.get(COOKIE_REFRESH)
    resultado = await autenticacion.renovar_sesion(db, token) if token else None
    if resultado is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Tu sesión venció. Ingresá de nuevo.")
    usuario, access, nuevo_refresh = resultado
    _guardar_refresh(response, nuevo_refresh)
    return _token_salida(access, usuario.rol)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request, response: Response, usuario: UsuarioActual, db: SesionDB
) -> None:
    await autenticacion.cerrar_sesion(db, request.state.sesion_id)
    response.delete_cookie(COOKIE_REFRESH, path=RUTA_COOKIE)


@router.get("/yo", response_model=UsuarioActualSalida)
async def yo(usuario: UsuarioActual, db: SesionDB) -> UsuarioActualSalida:
    ids = [t.id for t in await tiendas.tiendas_de_usuario(db, usuario.id)]
    return UsuarioActualSalida(
        id=usuario.id,
        nombre=usuario.nombre,
        empresa=usuario.empresa,
        correo=usuario.correo,
        rol=usuario.rol,
        tienda_ids=ids,
    )


@router.post("/token/verificar", response_model=EstadoTokenSalida)
async def verificar_token(datos: TokenEntrada, db: SesionDB) -> EstadoTokenSalida:
    estado, tipo = await tokens.estado_token(db, datos.token)
    return EstadoTokenSalida(estado=estado, tipo=tipo)


@router.post("/password", response_model=Mensaje)
async def definir_password(datos: DefinirPasswordEntrada, db: SesionDB) -> Mensaje:
    await tokens.consumir_token(db, datos.token, datos.password)
    return Mensaje(mensaje="Tu contraseña quedó guardada. Ya podés ingresar.")


@router.post("/recuperar", response_model=Mensaje, status_code=status.HTTP_202_ACCEPTED)
async def recuperar(datos: CorreoEntrada, db: SesionDB, cola: Cola) -> Mensaje:
    await usuarios.solicitar_recuperacion(db, cola, datos.correo)
    return Mensaje(
        mensaje=(
            "Si el correo corresponde a una cuenta, "
            "te enviamos un enlace para restablecer la contraseña."
        )
    )

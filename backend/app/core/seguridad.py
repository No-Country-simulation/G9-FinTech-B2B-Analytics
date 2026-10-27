import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from pwdlib import PasswordHash

from app.core.config import settings

_hasher = PasswordHash.recommended()  # argon2

# Hash de una contraseña cualquiera: se verifica contra él cuando el correo no existe,
# para que el login tarde lo mismo exista o no la cuenta.
HASH_FALSO = _hasher.hash("contraseña-que-nunca-coincide")


def hashear_password(password: str) -> str:
    return _hasher.hash(password)


def verificar_password(password: str, password_hash: str) -> bool:
    return _hasher.verify(password, password_hash)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def generar_token_opaco() -> tuple[str, str]:
    """Devuelve (token para el usuario, hash para la base)."""
    token = secrets.token_urlsafe(32)
    return token, hash_token(token)


def crear_access_token(usuario_id: uuid.UUID, rol: str, sesion_id: uuid.UUID) -> str:
    ahora = datetime.now(UTC)
    payload = {
        "sub": str(usuario_id),
        "rol": str(rol),
        "sid": str(sesion_id),
        "iat": ahora,
        "exp": ahora + timedelta(minutes=settings.access_token_minutos),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algoritmo)


def decodificar_access_token(token: str) -> dict[str, Any]:
    """Lanza jwt.PyJWTError si la firma no es válida o el token venció."""
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algoritmo])

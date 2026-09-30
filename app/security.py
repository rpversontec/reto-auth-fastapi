"""La criptografía, en un solo archivo. Compara con `_auth.js` de la API del curso:
son las mismas cuatro piezas, con librerías de Python en vez de WebCrypto.

  · hash_password / verify_password — Argon2id. Mejor que el PBKDF2 del Worker
    (ahí era el único algoritmo disponible); aquí no hay razón para no usar Argon2.
  · sign_jwt / verify_jwt           — el token de acceso, HS256 con PyJWT.
  · random_token                    — el token de refresco: 32 bytes al azar.
  · sha256                          — cómo se guarda el refresh: hasheado, como una contraseña.
"""

import hashlib
import secrets
import time
from typing import Any

import jwt
from pwdlib import PasswordHash

# `recommended()` es Argon2id con parámetros razonables. No los ajustes sin leer por qué.
_hasher = PasswordHash.recommended()

ALGORITMO = "HS256"


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return _hasher.verify(password, password_hash)


def sign_jwt(usuario: str, rol: str, ttl_s: int, secret: str) -> str:
    """Un JWT es JSON firmado, no cifrado: cualquiera lo lee, nadie lo altera."""
    ahora = int(time.time())
    payload = {"sub": usuario, "rol": rol, "iat": ahora, "exp": ahora + ttl_s}
    return jwt.encode(payload, secret, algorithm=ALGORITMO)


class TokenInvalido(Exception):
    """`reason` es "expirado" o "invalido". Se traduce a un 401 en `deps.py`."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


def verify_jwt(token: str, secret: str) -> dict[str, Any]:
    """PyJWT verifica la firma Y la fecha. El orden importa: un token alterado ni se lee."""
    try:
        return jwt.decode(token, secret, algorithms=[ALGORITMO])
    except jwt.ExpiredSignatureError as e:
        raise TokenInvalido("expirado") from e
    except jwt.InvalidTokenError as e:
        raise TokenInvalido("invalido") from e


def random_token() -> str:
    """32 bytes al azar en base64url. No dice nada de nadie: es una llave, no una credencial."""
    return secrets.token_urlsafe(32)


def sha256(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()

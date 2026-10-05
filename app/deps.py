"""Las dependencias que protegen rutas. Se usan así:

    @router.get("/avisos")
    def listar(quien: Identidad = Depends(usuario_actual)): ...

    @router.post("/avisos")
    def crear(quien: Identidad = Depends(requiere_profesor)): ...

Autenticación (¿quién eres?) y autorización (¿puedes?) son dos dependencias
distintas, y responden con códigos distintos: 401 y 403.
"""

from dataclasses import dataclass

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import settings
from .errors import ApiError
from .security import TokenInvalido, verify_jwt


@dataclass
class Identidad:
    usuario: str
    rol: str
    exp: int


# Declarar el esquema Bearer es lo que hace aparecer «Authorize» y los candados en /docs.
# auto_error=False: si falta el token, el 401 lo da usuario_actual con la forma del
# contrato ({error, code, hint}), no FastAPI con {"detail": ...}, que la app no lee.
_bearer = HTTPBearer(auto_error=False)


def usuario_actual(credenciales: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> Identidad:
    """Lee `Authorization: Bearer <jwt>`, verifica la firma y la fecha."""
    if credenciales is None:
        raise ApiError(401, "Falta el token de acceso", "falta_token", "Manda `Authorization: Bearer <accessToken>`.")
    token = credenciales.credentials
    try:
        payload = verify_jwt(token, settings.jwt_secret)
    except TokenInvalido as e:
        if e.reason == "expirado":
            raise ApiError(401, "El token de acceso expiró", "token_expirado", "Pide otro con POST /api/auth/refresh.")
        raise ApiError(401, "El token no es válido", "token_invalido", "La firma no coincide o el token está mal formado.")
    return Identidad(usuario=payload["sub"], rol=payload["rol"], exp=payload["exp"])


def requiere_profesor(quien: Identidad = Depends(usuario_actual)) -> Identidad:
    """La app puede esconder el botón; el servidor no confía en que lo haya hecho."""
    if quien.rol != "profesor":
        raise ApiError(
            403,
            "Solo un profesor puede publicar o borrar avisos",
            hint=f'Tu sesión es de "{quien.usuario}" con rol "{quien.rol}".',
        )
    return quien

import time
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_db
from ..deps import Identidad, usuario_actual
from ..errors import ApiError
from ..models import Sesion, Usuario
from ..schemas import Credenciales, Me, RefreshBody, Registro, Tokens
from ..security import hash_password, random_token, sha256, sign_jwt, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


def ahora() -> int:
    return int(time.time())


def emitir_tokens(db: Session, usuario: str, rol: str) -> Tokens:
    """Emite el par y registra la sesión. Se usa en register, login y refresh."""
    access = sign_jwt(usuario, rol, settings.access_ttl_s, settings.jwt_secret)
    refresh = random_token()
    db.add(Sesion(usuario=usuario, refresh_hash=sha256(refresh), expires_at=ahora() + settings.refresh_ttl_s))
    db.commit()
    return Tokens(accessToken=access, refreshToken=refresh, expiresIn=settings.access_ttl_s, usuario=usuario, rol=rol)


@router.post("/register", response_model=Tokens, status_code=201)
def register(body: Registro, db: Session = Depends(get_db)) -> Tokens:
    if db.get(Usuario, body.usuario):
        raise ApiError(409, f'El usuario "{body.usuario}" ya existe', hint="Elige otro, o entra con POST /api/auth/login.")

    # El rol lo decide el servidor, nunca el cliente. "profesor" solo con el código
    # que se da en clase; cualquier otra cosa —incluido mandar rol: "profesor"— es alumno.
    rol = "profesor" if body.codigoProfesor and body.codigoProfesor == settings.codigo_profesor else "alumno"

    db.add(Usuario(usuario=body.usuario, password_hash=hash_password(body.password), rol=rol))
    db.commit()
    return emitir_tokens(db, body.usuario, rol)


@router.post("/login", response_model=Tokens)
def login(body: Credenciales, db: Session = Depends(get_db)) -> Tokens:
    fila = db.get(Usuario, body.usuario)
    # Un solo mensaje para "no existe" y "contraseña mal": no se le dice a un
    # atacante cuál de las dos cosas acertó.
    if fila is None or not verify_password(body.password, fila.password_hash):
        raise ApiError(401, "Usuario o contraseña incorrectos", "credenciales", "Revisa los dos; el mensaje es el mismo a propósito.")
    return emitir_tokens(db, fila.usuario, fila.rol)


@router.post("/refresh", response_model=Tokens)
def refresh(body: RefreshBody, db: Session = Depends(get_db)) -> Tokens:
    sesion = db.scalar(select(Sesion).where(Sesion.refresh_hash == sha256(body.refreshToken)))
    if sesion is None or sesion.revoked_at is not None or sesion.expires_at <= ahora():
        raise ApiError(401, "El refresh token no sirve", "refresh_invalido", "Fue revocado, ya expiró, o nunca existió. Hay que volver a entrar.")

    # Rotación: el token usado se retira y sale uno nuevo. Si alguien lo copió,
    # solo uno de los dos —el ladrón o el dueño— logra usarlo.
    sesion.revoked_at = datetime.now(timezone.utc)
    usuario = db.get(Usuario, sesion.usuario)
    assert usuario is not None
    return emitir_tokens(db, usuario.usuario, usuario.rol)


@router.post("/logout")
def logout(body: RefreshBody, db: Session = Depends(get_db)) -> dict[str, int]:
    sesion = db.scalar(select(Sesion).where(Sesion.refresh_hash == sha256(body.refreshToken), Sesion.revoked_at.is_(None)))
    if sesion is None:
        return {"revoked": 0}
    sesion.revoked_at = datetime.now(timezone.utc)
    db.commit()
    return {"revoked": 1}


@router.get("/me", response_model=Me)
def me(quien: Identidad = Depends(usuario_actual), db: Session = Depends(get_db)) -> Me:
    activas = db.scalar(
        select(func.count()).select_from(Sesion).where(
            Sesion.usuario == quien.usuario, Sesion.revoked_at.is_(None), Sesion.expires_at > ahora()
        )
    )
    return Me(usuario=quien.usuario, rol=quien.rol, exp=quien.exp, sesionesActivas=activas or 0)


@router.delete("/sesiones")
def cerrar_todas(quien: Identidad = Depends(usuario_actual), db: Session = Depends(get_db)) -> dict[str, int]:
    """Cerrar sesión en todos lados: revoca todos los refresh del usuario. Los access vivos caducan solos."""
    filas = db.scalars(select(Sesion).where(Sesion.usuario == quien.usuario, Sesion.revoked_at.is_(None))).all()
    for s in filas:
        s.revoked_at = datetime.now(timezone.utc)
    db.commit()
    return {"revoked": len(filas)}

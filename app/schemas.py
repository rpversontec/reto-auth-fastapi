"""Lo que entra y lo que sale, con los MISMOS nombres que la API del curso
(camelCase donde el contrato lo usa), para que los DTO de la app no cambien."""

import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

USUARIO_RE = re.compile(r"^[a-z0-9._-]{3,32}$")
PASSWORD_MIN = 8
TITULO_MIN, TITULO_MAX = 3, 60
CUERPO_MIN, CUERPO_MAX = 10, 400


class Credenciales(BaseModel):
    """Para entrar. Solo normaliza el usuario: una contraseña corta en el login
    es un 401 como cualquier otra, no un 422 que delate la regla."""

    usuario: str
    password: str

    @field_validator("usuario")
    @classmethod
    def usuario_normalizado(cls, v: str) -> str:
        return v.strip().lower()


class Registro(Credenciales):
    """Para registrarse. Aquí sí se validan las reglas, y se acepta el código de profesor."""

    codigoProfesor: str | None = None

    @field_validator("usuario")
    @classmethod
    def usuario_valido(cls, v: str) -> str:
        v = v.strip().lower()
        if not USUARIO_RE.match(v):
            raise ValueError("usuario: de 3 a 32 caracteres, solo letras, números, punto, guion y guion bajo")
        return v

    @field_validator("password")
    @classmethod
    def password_valida(cls, v: str) -> str:
        if len(v) < PASSWORD_MIN:
            raise ValueError(f"password debe tener al menos {PASSWORD_MIN} caracteres")
        return v


class Tokens(BaseModel):
    accessToken: str
    refreshToken: str
    tokenType: str = "Bearer"
    expiresIn: int
    usuario: str
    rol: str


class RefreshBody(BaseModel):
    refreshToken: str


class Me(BaseModel):
    usuario: str
    rol: str
    exp: int
    sesionesActivas: int


class NuevoAviso(BaseModel):
    titulo: str
    cuerpo: str

    @field_validator("titulo")
    @classmethod
    def titulo_valido(cls, v: str) -> str:
        v = v.strip()
        if not TITULO_MIN <= len(v) <= TITULO_MAX:
            raise ValueError(f"titulo debe tener entre {TITULO_MIN} y {TITULO_MAX} caracteres")
        return v

    @field_validator("cuerpo")
    @classmethod
    def cuerpo_valido(cls, v: str) -> str:
        v = v.strip()
        if not CUERPO_MIN <= len(v) <= CUERPO_MAX:
            raise ValueError(f"cuerpo debe tener entre {CUERPO_MIN} y {CUERPO_MAX} caracteres")
        return v


class AvisoOut(BaseModel):
    # from_attributes: se construye directo desde el objeto de SQLAlchemy.
    model_config = ConfigDict(from_attributes=True)

    id: int
    titulo: str
    cuerpo: str
    autor: str
    # La columna se llama created_at (estilo Python); el contrato dice createdAt (estilo JSON).
    createdAt: datetime = Field(validation_alias="created_at")

    @field_serializer("createdAt")
    def fecha_como_texto(self, v: datetime) -> str:
        # El mismo formato que SQLite en el Worker: "2026-09-21 16:51:55".
        return v.strftime("%Y-%m-%d %H:%M:%S")

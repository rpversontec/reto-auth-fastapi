from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


class Usuario(Base):
    """Quién es quién. La contraseña NO está: está su hash Argon2 (que ya trae su sal adentro)."""

    __tablename__ = "usuarios"

    usuario: Mapped[str] = mapped_column(String(32), primary_key=True)
    password_hash: Mapped[str] = mapped_column(Text)
    rol: Mapped[str] = mapped_column(String(16))  # "alumno" | "profesor"
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Sesion(Base):
    """Una fila por login. Guarda el HASH del refresh token, nunca el token."""

    __tablename__ = "sesiones"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    usuario: Mapped[str] = mapped_column(ForeignKey("usuarios.usuario"), index=True)
    refresh_hash: Mapped[str] = mapped_column(String(64), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    expires_at: Mapped[int] = mapped_column(BigInteger)  # epoch en segundos
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Aviso(Base):
    """El tablón. Cualquiera con sesión lo lee; solo un profesor escribe."""

    __tablename__ = "avisos"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    titulo: Mapped[str] = mapped_column(String(60))
    cuerpo: Mapped[str] = mapped_column(String(400))
    autor: Mapped[str] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

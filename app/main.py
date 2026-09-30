"""Módulo de autenticación y autorización de referencia para el reto de TC2007B.

Mismo contrato que https://startdroid.com/api (Práctica 6): la app de Android
funciona contra este servidor cambiando solo `BASE_URL`.

    uv sync
    cp .env.example .env        # y cambia JWT_SECRET
    uv run uvicorn app.main:app --reload
    → http://localhost:8000/api/health   ·   http://localhost:8000/docs
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from . import errors
from .config import settings
from .db import Base, SessionLocal, engine
from .models import Aviso
from .routers import auth, avisos


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Crea las tablas si no existen. Para el reto alcanza; el día que cambies una
    # columna con datos reales, eso se llama migración y se hace con Alembic.
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        if db.scalar(select(Aviso).limit(1)) is None:
            db.add(Aviso(titulo="Bienvenidos al tablón", cuerpo="Este aviso lo publicó el servidor al crear la tabla. Los siguientes los publica un profesor desde la app.", autor="profesor"))
            db.commit()
    yield


app = FastAPI(title="Avisos · auth de referencia", lifespan=lifespan)
errors.instalar(app)

# Abierto a cualquier origen para desarrollo (la consola del curso, tu navegador).
# En producción, lista aquí solo los orígenes que de verdad te llaman.
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

app.include_router(auth.router, prefix="/api")
app.include_router(avisos.router, prefix="/api")


@app.get("/api/health")
def health() -> dict:
    return {
        "ok": True,
        "api": "Avisos · auth de referencia (FastAPI + PostgreSQL)",
        "identidad": "usuario y contraseña en /auth/login; después `Authorization: Bearer <accessToken>`",
        "accessTokenSegundos": settings.access_ttl_s,
        "refreshTokenSegundos": settings.refresh_ttl_s,
        "endpoints": [
            "POST   /api/auth/register   { usuario, password, codigoProfesor? }",
            "POST   /api/auth/login      { usuario, password }",
            "POST   /api/auth/refresh    { refreshToken }",
            "POST   /api/auth/logout     { refreshToken }",
            "DELETE /api/auth/sesiones   (Bearer) cierra todas tus sesiones",
            "GET    /api/auth/me         (Bearer)",
            "GET    /api/avisos?desde=:id (Bearer) solo los avisos con id mayor a :id",
            "GET    /api/avisos/stream   (Bearer) SSE: un evento `aviso` por cada aviso nuevo, hasta que el token expira",
            "POST   /api/avisos          (Bearer, rol profesor) { titulo, cuerpo }",
            "DELETE /api/avisos/:id      (Bearer, rol profesor)",
        ],
    }

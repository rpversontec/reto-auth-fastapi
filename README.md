# auth-fastapi — módulo de identidad de referencia

Autenticación y autorización para el reto de TC2007B: **FastAPI + PostgreSQL**,
con el mismo contrato que `https://startdroid.com/api` (Práctica 6). La app de
Android de la práctica funciona contra este servidor cambiando solo `BASE_URL`.

    docker compose up -d                 # PostgreSQL 16 (o usa tu instalación local)
    cp .env.example .env                 # y cambia JWT_SECRET y CODIGO_PROFESOR
    uv sync
    uv run uvicorn app.main:app --reload # http://localhost:8000/docs
    bash smoke.sh                        # los 20 casos del contrato, con sus códigos

`.env` nunca se sube al repositorio. `smoke.sh` lee de ahí el código de profesor.

La guía de lectura es el anexo del curso: https://startdroid.com/practicas/anexo-auth

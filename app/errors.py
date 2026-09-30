"""Los errores con la MISMA forma que la API del curso, para que la app de la
Práctica 6 los entienda sin cambios:

    { "error": "texto para el usuario", "code": "slug", "hint": "para el programador" }

FastAPI por omisión responde `{"detail": ...}`, que `mensajeDe()` en Android no lee.
"""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class ApiError(Exception):
    def __init__(self, status: int, error: str, code: str | None = None, hint: str | None = None) -> None:
        super().__init__(error)
        self.status = status
        self.error = error
        self.code = code
        self.hint = hint


def instalar(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def api_error(_: Request, e: ApiError) -> JSONResponse:
        cuerpo: dict[str, str] = {"error": e.error}
        if e.code:
            cuerpo["code"] = e.code
        if e.hint:
            cuerpo["hint"] = e.hint
        headers = {}
        if e.status == 401:
            # El estándar: un 401 dice CÓMO autenticarse. Los clientes serios lo leen.
            headers["WWW-Authenticate"] = 'Bearer realm="reto"'
        return JSONResponse(cuerpo, status_code=e.status, headers=headers)

    @app.exception_handler(RequestValidationError)
    async def validation_error(_: Request, e: RequestValidationError) -> JSONResponse:
        # Pydantic reporta una lista; el contrato del curso reporta UN campo y UN mensaje.
        primero = e.errors()[0]
        campo = str(primero["loc"][-1]) if primero.get("loc") else "body"
        mensaje = str(primero.get("msg", "dato inválido")).removeprefix("Value error, ")
        return JSONResponse({"field": campo, "error": mensaje}, status_code=422)

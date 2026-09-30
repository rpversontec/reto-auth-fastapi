from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Todo lo que cambia entre tu máquina y el servidor vive en el entorno, no en el código.

    Se lee de variables de entorno o de un archivo `.env` (que nunca se sube al repo).
    Si falta `JWT_SECRET` o `CODIGO_PROFESOR`, la app no arranca — a propósito.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/avisos"
    jwt_secret: str
    codigo_profesor: str

    # Cinco minutos de acceso y siete días de refresco: los mismos números de la Práctica 6.
    access_ttl_s: int = 5 * 60
    refresh_ttl_s: int = 7 * 24 * 60 * 60


settings = Settings()

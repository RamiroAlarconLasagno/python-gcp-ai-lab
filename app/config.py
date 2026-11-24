# app/config.py
"""Configuración de la app: variables de entorno y, en local, el archivo .env."""

from functools import lru_cache
from typing import Self

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


class Settings(BaseSettings):
    """Valores de configuración; las variables de entorno tienen prioridad sobre .env.

    En local se usa DATABASE_URL. En Cloud Run no hay DATABASE_URL: la URL se arma
    con DB_USER, DB_PASSWORD, DB_NAME e INSTANCE_CONNECTION_NAME (socket Unix que
    monta la conexión integrada de Cloud SQL en /cloudsql/<instancia>).
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = ""
    db_user: str = ""
    db_password: str = ""
    db_name: str = ""
    instance_connection_name: str = ""

    @model_validator(mode="after")
    def build_database_url(self) -> Self:
        """Si falta DATABASE_URL, la arma desde sus partes; si tampoco están, falla."""
        if self.database_url:
            return self
        parts = {
            "DB_USER": self.db_user,
            "DB_PASSWORD": self.db_password,
            "DB_NAME": self.db_name,
            "INSTANCE_CONNECTION_NAME": self.instance_connection_name,
        }
        missing = [name for name, value in parts.items() if not value]
        if missing:
            msg = f"Falta DATABASE_URL o estas variables: {', '.join(missing)}"
            raise ValueError(msg)
        url = URL.create(
            "postgresql+asyncpg",
            username=self.db_user,
            password=self.db_password,
            database=self.db_name,
            query={"host": f"/cloudsql/{self.instance_connection_name}"},
        )
        self.database_url = url.render_as_string(hide_password=False)
        return self


@lru_cache
def get_settings() -> Settings:
    """Lee la configuración una sola vez, la primera vez que se necesita."""
    return Settings()

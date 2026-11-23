# app/config.py
"""Configuración de la app: variables de entorno y, en local, el archivo .env."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Valores de configuración; las variables de entorno tienen prioridad sobre .env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str


@lru_cache
def get_settings() -> Settings:
    """Lee la configuración una sola vez, la primera vez que se necesita."""
    return Settings()  # type: ignore[call-arg]  # los valores vienen del entorno

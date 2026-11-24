# tests/test_config.py
"""Tests de la configuración: DATABASE_URL directa o armada desde sus partes."""

import pytest
from pydantic import ValidationError
from sqlalchemy.engine import make_url

from app.config import Settings

CLOUD_PARTS = {
    "DB_USER": "quotes",
    "DB_PASSWORD": "p@ss/w%rd",
    "DB_NAME": "quotes",
    "INSTANCE_CONNECTION_NAME": "proj:us-central1:quotes-abc",
}


@pytest.fixture(autouse=True)
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Quita las variables de la base del entorno para que cada test parta de cero."""
    for name in ("DATABASE_URL", *CLOUD_PARTS):
        monkeypatch.delenv(name, raising=False)


def make_settings() -> Settings:
    """Settings sin leer el .env local, solo con el entorno del test."""
    return Settings(_env_file=None)  # type: ignore[call-arg]


def test_database_url_is_used_as_is(monkeypatch: pytest.MonkeyPatch) -> None:
    url = "postgresql+asyncpg://quotes:quotes@localhost:5432/quotes"
    monkeypatch.setenv("DATABASE_URL", url)
    assert make_settings().database_url == url


def test_url_is_built_from_parts(monkeypatch: pytest.MonkeyPatch) -> None:
    for name, value in CLOUD_PARTS.items():
        monkeypatch.setenv(name, value)
    url = make_url(make_settings().database_url)
    assert url.drivername == "postgresql+asyncpg"
    assert url.username == "quotes"
    assert url.password == "p@ss/w%rd"  # los caracteres especiales sobreviven
    assert url.database == "quotes"
    assert url.query["host"] == "/cloudsql/proj:us-central1:quotes-abc"


def test_database_url_wins_over_parts(monkeypatch: pytest.MonkeyPatch) -> None:
    for name, value in CLOUD_PARTS.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://a:b@localhost/c")
    assert make_settings().database_url == "postgresql+asyncpg://a:b@localhost/c"


def test_missing_parts_are_named(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DB_USER", "quotes")
    with pytest.raises(ValidationError, match="DB_PASSWORD, DB_NAME, INSTANCE_CONNECTION_NAME"):
        make_settings()

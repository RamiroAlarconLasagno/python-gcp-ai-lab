# tests/test_api.py
"""Pruebas HTTP de la API contra la base de docker compose (marcadas integration).

Requieren PostgreSQL levantado y migrado: docker compose up -d db y
uv run alembic upgrade head (o docker compose up, que migra al arrancar).
"""

import uuid
from collections.abc import AsyncIterator
from datetime import datetime, timedelta
from typing import Any

import httpx
import pytest

from app.db import get_engine
from app.main import app

pytestmark = pytest.mark.integration

VALID_REQUEST: dict[str, Any] = {
    "zone": "amba",
    "weight_kg": 2.5,
    "length_cm": 20,
    "width_cm": 15,
    "height_cm": 10,
    "mode": "standard",
}


BREAKDOWN_KEYS = (
    "zone",
    "mode",
    "length_cm",
    "width_cm",
    "height_cm",
    "currency",
    "actual_weight_kg",
    "volumetric_weight_kg",
    "billable_weight_kg",
    "freight",
    "urgent_surcharge",
    "total",
    "delivery_days",
)


def assert_business_rule(response: httpx.Response, message_start: str) -> None:
    """Comprueba un 422 del cotizador con el mismo formato que los de Pydantic."""
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert len(errors) == 1
    assert errors[0]["loc"] == ["body"]
    assert errors[0]["type"] == "business_rule"
    assert errors[0]["msg"].startswith(message_start)


@pytest.fixture
def anyio_backend() -> str:
    """Corre las pruebas async solo con asyncio (trio no está instalado)."""
    return "asyncio"


@pytest.fixture
async def client() -> AsyncIterator[httpx.AsyncClient]:
    """Cliente HTTP que llama a la app en memoria, sin servidor.

    Al terminar cierra el pool de la base: cada test corre en su propio event
    loop y las conexiones de asyncpg no se pueden reutilizar entre loops.
    """
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    await get_engine().dispose()


@pytest.mark.anyio
async def test_health(client: httpx.AsyncClient) -> None:
    """GET /health responde 200 con status ok."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.anyio
async def test_valid_quote(client: httpx.AsyncClient) -> None:
    """AMBA, 2,5 kg, 20x15x10, standard: 200 con id, vence en 48 h y total "12800.00"."""
    response = await client.post("/quotes", json=VALID_REQUEST)
    assert response.status_code == 200
    body = response.json()
    uuid.UUID(body["id"])
    created_at = datetime.fromisoformat(body["created_at"])
    expires_at = datetime.fromisoformat(body["expires_at"])
    assert expires_at - created_at == timedelta(hours=48)
    assert {k: body[k] for k in BREAKDOWN_KEYS} == {
        "zone": "amba",
        "mode": "standard",
        "length_cm": "20",
        "width_cm": "15",
        "height_cm": "10",
        "currency": "ARS",
        "actual_weight_kg": "2.5",
        "volumetric_weight_kg": "0.6",
        "billable_weight_kg": "3",
        "freight": "12800.00",
        "urgent_surcharge": "0.00",
        "total": "12800.00",
        "delivery_days": 4,
    }


@pytest.mark.anyio
async def test_saved_quote_can_be_read(client: httpx.AsyncClient) -> None:
    """Lo que devuelve POST /quotes se lee igual con GET /quotes/{id}."""
    created = await client.post("/quotes", json={**VALID_REQUEST, "mode": "urgent"})
    assert created.status_code == 200
    response = await client.get(f"/quotes/{created.json()['id']}")
    assert response.status_code == 200
    assert response.json() == created.json()
    assert response.json()["total"] == "19200.00"


@pytest.mark.anyio
async def test_unknown_id_returns_404(client: httpx.AsyncClient) -> None:
    """Un id que no existe responde 404 con el mismo formato de error."""
    quote_id = uuid.uuid4()
    response = await client.get(f"/quotes/{quote_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == [
        {
            "loc": ["path", "quote_id"],
            "msg": f"No existe una cotización con id {quote_id}",
            "type": "not_found",
        }
    ]


@pytest.mark.anyio
async def test_incomplete_json_is_rejected(client: httpx.AsyncClient) -> None:
    """Sin weight_kg: 422 de validación que señala el campo faltante."""
    body = {k: v for k, v in VALID_REQUEST.items() if k != "weight_kg"}
    response = await client.post("/quotes", json=body)
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert errors[0]["type"] == "missing"
    assert errors[0]["loc"] == ["body", "weight_kg"]


@pytest.mark.anyio
async def test_negative_weight_is_rejected(client: httpx.AsyncClient) -> None:
    """weight_kg negativo: 422 de validación (debe ser > 0)."""
    response = await client.post("/quotes", json={**VALID_REQUEST, "weight_kg": -1})
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert errors[0]["type"] == "greater_than"
    assert errors[0]["loc"] == ["body", "weight_kg"]


@pytest.mark.anyio
async def test_unknown_zone_is_rejected(client: httpx.AsyncClient) -> None:
    """Zona inexistente: 422 con el mensaje del cotizador."""
    response = await client.post("/quotes", json={**VALID_REQUEST, "zone": "mars"})
    assert_business_rule(response, "Zona inexistente: 'mars'")


@pytest.mark.anyio
async def test_invalid_mode_is_rejected(client: httpx.AsyncClient) -> None:
    """Modalidad inválida: 422 con el mensaje del cotizador."""
    response = await client.post("/quotes", json={**VALID_REQUEST, "mode": "express"})
    assert_business_rule(response, "Modalidad inexistente: 'express'")


@pytest.mark.anyio
async def test_balloon_is_rejected(client: httpx.AsyncClient) -> None:
    """Globo (0,2 kg en 100x100x100): 422 por peso facturable de 200 kg."""
    body = {
        **VALID_REQUEST,
        "weight_kg": 0.2,
        "length_cm": 100,
        "width_cm": 100,
        "height_cm": 100,
    }
    response = await client.post("/quotes", json=body)
    assert_business_rule(response, "El peso facturable (200 kg)")

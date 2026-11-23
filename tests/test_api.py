# tests/test_api.py
"""Pruebas HTTP de la API: health, cotización válida y rechazos con 422."""

from collections.abc import AsyncIterator
from typing import Any

import httpx
import pytest

from app.main import app

VALID_REQUEST: dict[str, Any] = {
    "zone": "amba",
    "weight_kg": 2.5,
    "length_cm": 20,
    "width_cm": 15,
    "height_cm": 10,
    "mode": "standard",
}


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
    """Cliente HTTP que llama a la app en memoria, sin red ni servidor."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.anyio
async def test_health(client: httpx.AsyncClient) -> None:
    """GET /health responde 200 con status ok."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.anyio
async def test_valid_quote(client: httpx.AsyncClient) -> None:
    """AMBA, 2,5 kg, 20x15x10, standard: 200 con total "12800.00" en texto."""
    response = await client.post("/quotes", json=VALID_REQUEST)
    assert response.status_code == 200
    assert response.json() == {
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

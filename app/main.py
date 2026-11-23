# app/main.py
"""API HTTP del cotizador: health, crear cotizaciones (se guardan) y leerlas por id."""

import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime
from decimal import Decimal
from typing import Annotated

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from app.db import get_engine, get_quote, save_quote
from app.quoting import calculate_quote

PositiveDecimal = Annotated[Decimal, Field(gt=0)]


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Al apagar la app cierra el pool de conexiones a la base."""
    yield
    await get_engine().dispose()


app = FastAPI(
    title="Shipping quote API",
    description="Fictional shipping quotes in ARS (portfolio lab).",
    lifespan=lifespan,
)


class QuoteRequest(BaseModel):
    """Datos para cotizar: zona, peso real (kg), medidas (cm) y modalidad.

    Acá solo se valida la forma (campos obligatorios y números > 0). Las reglas
    del negocio (zonas, modalidades, límites de peso) las valida el cotizador.
    """

    zone: str
    weight_kg: PositiveDecimal
    length_cm: PositiveDecimal
    width_cm: PositiveDecimal
    height_cm: PositiveDecimal
    mode: str


class QuoteResponse(BaseModel):
    """Cotización guardada: id, vigencia, lo pedido y el desglose.

    Los Decimal viajan como texto para no perder precisión.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    expires_at: datetime
    zone: str
    mode: str
    length_cm: Decimal
    width_cm: Decimal
    height_cm: Decimal
    currency: str
    actual_weight_kg: Decimal
    volumetric_weight_kg: Decimal
    billable_weight_kg: Decimal
    freight: Decimal
    urgent_surcharge: Decimal
    total: Decimal
    delivery_days: int


def error_detail(loc: list[str], msg: str, error_type: str) -> list[dict[str, object]]:
    """Arma el detail de un error con el mismo formato que usa Pydantic."""
    return [{"loc": loc, "msg": msg, "type": error_type}]


@app.get("/health")
async def health() -> dict[str, str]:
    """Indica que el servicio responde (no consulta la base)."""
    return {"status": "ok"}


@app.post("/quotes")
async def create_quote(request: QuoteRequest) -> QuoteResponse:
    """Calcula una cotización, la guarda y la devuelve con su id y vencimiento.

    Un error de negocio del cotizador responde 422 con el mismo formato que los
    errores de Pydantic: una lista de {loc, msg, type}.
    """
    try:
        quote = calculate_quote(
            zone=request.zone,
            weight_kg=request.weight_kg,
            length_cm=request.length_cm,
            width_cm=request.width_cm,
            height_cm=request.height_cm,
            mode=request.mode,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=error_detail(["body"], str(error), "business_rule"),
        ) from error
    record = await save_quote(
        zone=request.zone,
        mode=request.mode,
        length_cm=request.length_cm,
        width_cm=request.width_cm,
        height_cm=request.height_cm,
        quote=quote,
    )
    return QuoteResponse.model_validate(record)


@app.get("/quotes/{quote_id}")
async def read_quote(quote_id: uuid.UUID) -> QuoteResponse:
    """Devuelve una cotización guardada; 404 si el id no existe."""
    record = await get_quote(quote_id)
    if record is None:
        raise HTTPException(
            status_code=404,
            detail=error_detail(
                ["path", "quote_id"],
                f"No existe una cotización con id {quote_id}",
                "not_found",
            ),
        )
    return QuoteResponse.model_validate(record)

# app/main.py
"""API HTTP del cotizador: GET /health y POST /quotes sobre la función pura."""

from dataclasses import asdict
from decimal import Decimal
from typing import Annotated

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.quoting import calculate_quote

PositiveDecimal = Annotated[Decimal, Field(gt=0)]

app = FastAPI(
    title="Shipping quote API",
    description="Fictional shipping quotes in ARS (portfolio lab).",
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
    """Cotización con todos los campos de Quote; los Decimal viajan como texto."""

    currency: str
    actual_weight_kg: Decimal
    volumetric_weight_kg: Decimal
    billable_weight_kg: Decimal
    freight: Decimal
    urgent_surcharge: Decimal
    total: Decimal
    delivery_days: int


@app.get("/health")
async def health() -> dict[str, str]:
    """Indica que el servicio responde."""
    return {"status": "ok"}


@app.post("/quotes")
async def create_quote(request: QuoteRequest) -> QuoteResponse:
    """Calcula una cotización; un error de negocio del cotizador responde 422."""
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
        raise HTTPException(status_code=422, detail=str(error)) from error
    return QuoteResponse(**asdict(quote))

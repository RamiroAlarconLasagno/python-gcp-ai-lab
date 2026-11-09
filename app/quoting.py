# app/quoting.py
"""Cotizador puro de envíos: pesos, flete, recargo urgente y plazo, todo con Decimal."""

from dataclasses import dataclass
from decimal import ROUND_CEILING, ROUND_HALF_UP, Decimal

from app.tariffs import (
    CURRENCY,
    MAX_WEIGHT_KG,
    MIN_WEIGHT_KG,
    MODES,
    URGENT_SURCHARGE_RATE,
    VOLUMETRIC_DIVISOR,
    ZONES,
)

CENT = Decimal("0.01")


@dataclass(frozen=True)
class Quote:
    """Resultado de una cotización.

    Pesos en kg (el facturable ya redondeado al kilo siguiente), importes en
    `currency` con 2 decimales y plazo en días hábiles.
    """

    currency: str
    actual_weight_kg: Decimal
    volumetric_weight_kg: Decimal
    billable_weight_kg: Decimal
    freight: Decimal
    urgent_surcharge: Decimal
    total: Decimal
    delivery_days: int


def round_money(amount: Decimal) -> Decimal:
    """Redondea un importe a 2 decimales con ROUND_HALF_UP (0.125 -> 0.13)."""
    return amount.quantize(CENT, rounding=ROUND_HALF_UP)


def calculate_quote(
    *,
    zone: str,
    weight_kg: Decimal,
    length_cm: Decimal,
    width_cm: Decimal,
    height_cm: Decimal,
    mode: str,
) -> Quote:
    """Calcula la cotización de un envío.

    Peso facturable = máximo entre el real y el volumétrico, redondeado hacia
    arriba al kilo siguiente. Flete = base + tarifa por kg x facturable; el
    recargo urgente es un porcentaje del flete ya redondeado. El total es la
    suma de las líneas redondeadas.

    Lanza ValueError si la zona o la modalidad no existen, si el peso real
    está fuera de rango, si alguna dimensión no es positiva o si el peso
    facturable supera el máximo.
    """
    tariff = ZONES.get(zone)
    if tariff is None:
        raise ValueError(
            f"Zona inexistente: {zone!r}. Zonas válidas: {', '.join(ZONES)}"
        )
    if mode not in MODES:
        raise ValueError(
            f"Modalidad inexistente: {mode!r}. Modalidades válidas: {', '.join(MODES)}"
        )
    if not MIN_WEIGHT_KG <= weight_kg <= MAX_WEIGHT_KG:
        raise ValueError(
            f"El peso real ({weight_kg} kg) debe estar entre "
            f"{MIN_WEIGHT_KG} y {MAX_WEIGHT_KG} kg"
        )
    for name, value in (("largo", length_cm), ("ancho", width_cm), ("alto", height_cm)):
        if value <= 0:
            raise ValueError(f"El {name} debe ser mayor que 0 cm (recibido: {value})")

    volumetric_kg = length_cm * width_cm * height_cm / VOLUMETRIC_DIVISOR
    billable_kg = max(weight_kg, volumetric_kg).to_integral_value(
        rounding=ROUND_CEILING
    )
    if billable_kg > MAX_WEIGHT_KG:
        raise ValueError(
            f"El peso facturable ({billable_kg} kg) supera el máximo de {MAX_WEIGHT_KG} kg"
        )

    freight = round_money(tariff.base + tariff.per_kg * billable_kg)
    if mode == "urgent":
        urgent_surcharge = round_money(freight * URGENT_SURCHARGE_RATE)
        delivery_days = tariff.urgent_days
    else:
        urgent_surcharge = round_money(Decimal(0))
        delivery_days = tariff.standard_days

    return Quote(
        currency=CURRENCY,
        actual_weight_kg=weight_kg,
        volumetric_weight_kg=volumetric_kg,
        billable_weight_kg=billable_kg,
        freight=freight,
        urgent_surcharge=urgent_surcharge,
        total=freight + urgent_surcharge,
        delivery_days=delivery_days,
    )

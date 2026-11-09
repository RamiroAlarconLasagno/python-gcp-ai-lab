# app/tariffs.py
"""Tarifas ficticias del cotizador de envíos (ARS). Solo datos, sin lógica."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class ZoneTariff:
    """Tarifa de una zona: precio base, precio por kg y plazos en días hábiles."""

    base: Decimal
    per_kg: Decimal
    standard_days: int
    urgent_days: int


CURRENCY = "ARS"
MODES = ("standard", "urgent")

VOLUMETRIC_DIVISOR = Decimal(5000)
MIN_WEIGHT_KG = Decimal("0.1")
MAX_WEIGHT_KG = Decimal(30)
URGENT_SURCHARGE_RATE = Decimal("0.50")

ZONES: dict[str, ZoneTariff] = {
    "local": ZoneTariff(
        base=Decimal(3500), per_kg=Decimal(800), standard_days=2, urgent_days=1
    ),
    "amba": ZoneTariff(
        base=Decimal(9500), per_kg=Decimal(1100), standard_days=4, urgent_days=2
    ),
    "national": ZoneTariff(
        base=Decimal(14000), per_kg=Decimal(1500), standard_days=6, urgent_days=3
    ),
    "international": ZoneTariff(
        base=Decimal(45000), per_kg=Decimal(5000), standard_days=12, urgent_days=6
    ),
}

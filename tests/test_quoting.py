# tests/test_quoting.py
"""Pruebas del cotizador puro: casos del plan, límites, validaciones y redondeo."""

from decimal import Decimal

import pytest

from app.quoting import Quote, calculate_quote, round_money


def quote(
    zone: str = "amba",
    weight: str = "2.5",
    dims: tuple[str, str, str] = ("20", "15", "10"),
    mode: str = "standard",
) -> Quote:
    """Arma una cotización a partir de textos, para escribir los casos sin floats."""
    length, width, height = dims
    return calculate_quote(
        zone=zone,
        weight_kg=Decimal(weight),
        length_cm=Decimal(length),
        width_cm=Decimal(width),
        height_cm=Decimal(height),
        mode=mode,
    )


# Los importes se comparan como texto para exigir exactamente 2 decimales:
# Decimal("12800") == Decimal("12800.00") es True y no lo detectaría.


def test_amba_standard() -> None:
    """AMBA, 2,5 kg, 20x15x10: se cobran 3 kg -> 12800.00 en 4 días."""
    q = quote()
    assert q.currency == "ARS"
    assert str(q.actual_weight_kg) == "2.5"
    assert str(q.volumetric_weight_kg) == "0.6"
    assert str(q.billable_weight_kg) == "3"
    assert str(q.freight) == "12800.00"
    assert str(q.urgent_surcharge) == "0.00"
    assert str(q.total) == "12800.00"
    assert q.delivery_days == 4


def test_amba_urgent() -> None:
    """Mismo caso urgente: recargo del 50 % -> 19200.00 en 2 días."""
    q = quote(mode="urgent")
    assert str(q.freight) == "12800.00"
    assert str(q.urgent_surcharge) == "6400.00"
    assert str(q.total) == "19200.00"
    assert q.delivery_days == 2


def test_volumetric_weight_wins() -> None:
    """AMBA, 2,5 kg, 40x30x20: volumétrico 4,8 -> se cobran 5 kg -> 15000.00."""
    q = quote(dims=("40", "30", "20"))
    assert str(q.volumetric_weight_kg) == "4.8"
    assert str(q.billable_weight_kg) == "5"
    assert str(q.total) == "15000.00"


def test_whole_weight_is_not_rounded_up() -> None:
    """Local, 2,0 kg, 10x10x10: se cobran 2 kg, no 3 -> 5100.00."""
    q = quote(zone="local", weight="2.0", dims=("10", "10", "10"))
    assert str(q.billable_weight_kg) == "2"
    assert str(q.total) == "5100.00"


def test_minimum_weight_is_accepted() -> None:
    """Local, 0,1 kg, 10x10x10: el mínimo se acepta y se cobra 1 kg -> 4300.00."""
    q = quote(zone="local", weight="0.1", dims=("10", "10", "10"))
    assert str(q.billable_weight_kg) == "1"
    assert str(q.total) == "4300.00"


def test_volumetric_29_2_is_accepted() -> None:
    """AMBA, 100x73x20: volumétrico 29,2 -> se cobran 30 kg, justo en el límite."""
    q = quote(dims=("100", "73", "20"))
    assert str(q.volumetric_weight_kg) == "29.2"
    assert str(q.billable_weight_kg) == "30"
    assert str(q.total) == "42500.00"


def test_volumetric_30_2_is_rejected() -> None:
    """AMBA, 100x151x10: volumétrico 30,2 -> se cobrarían 31 kg, supera el máximo."""
    with pytest.raises(ValueError, match=r"facturable \(31 kg\)"):
        quote(dims=("100", "151", "10"))


def test_balloon_is_rejected() -> None:
    """El globo: 0,2 kg en 100x100x100 tiene volumétrico 200 kg > 30."""
    with pytest.raises(ValueError, match=r"facturable \(200 kg\)"):
        quote(weight="0.2", dims=("100", "100", "100"))


@pytest.mark.parametrize("weight", ["0.05", "31"])
def test_actual_weight_out_of_range_is_rejected(weight: str) -> None:
    """El peso real debe estar entre 0,1 y 30 kg."""
    with pytest.raises(ValueError, match="peso real"):
        quote(weight=weight)


@pytest.mark.parametrize(
    "dims", [("0", "15", "10"), ("20", "0", "10"), ("20", "15", "0")]
)
def test_zero_dimension_is_rejected(dims: tuple[str, str, str]) -> None:
    """Largo, ancho y alto deben ser mayores que 0."""
    with pytest.raises(ValueError, match="mayor que 0"):
        quote(dims=dims)


def test_unknown_zone_is_rejected() -> None:
    """Una zona que no está en la tabla se rechaza."""
    with pytest.raises(ValueError, match="Zona inexistente"):
        quote(zone="mars")


def test_unknown_mode_is_rejected() -> None:
    """Una modalidad distinta de standard o urgent se rechaza."""
    with pytest.raises(ValueError, match="Modalidad inexistente"):
        quote(mode="express")


@pytest.mark.parametrize(("amount", "expected"), [("0.125", "0.13"), ("0.124", "0.12")])
def test_round_money_half_up(amount: str, expected: str) -> None:
    """ROUND_HALF_UP: 0.125 sube a 0.13 (el redondeo por defecto daría 0.12)."""
    assert str(round_money(Decimal(amount))) == expected

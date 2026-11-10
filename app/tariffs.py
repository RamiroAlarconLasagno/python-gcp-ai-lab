# app/tariffs.py
"""Tarifas del cotizador de envíos: se cargan y validan desde app/tariffs.toml."""

import tomllib
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final


@dataclass(frozen=True)
class ZoneTariff:
    """Tarifa de una zona: precio base, precio por kg y plazos en días hábiles."""

    base: Decimal
    per_kg: Decimal
    standard_days: int
    urgent_days: int


@dataclass(frozen=True)
class TariffTable:
    """Tabla de tarifas completa, ya validada."""

    volumetric_divisor: Decimal
    min_weight_kg: Decimal
    max_weight_kg: Decimal
    urgent_surcharge_rate: Decimal
    zones: Mapping[str, ZoneTariff]


CURRENCY: Final = "ARS"
MODES: Final = ("standard", "urgent")
TARIFFS_PATH: Final = Path(__file__).with_name("tariffs.toml")

_GENERAL_KEYS = (
    "volumetric_divisor",
    "min_weight_kg",
    "max_weight_kg",
    "urgent_surcharge_rate",
)
_ZONE_KEYS = ("base", "per_kg", "standard_days", "urgent_days")


def load_tariffs(path: Path) -> TariffTable:
    """Lee y valida un archivo TOML de tarifas.

    Los números con decimales se leen como Decimal (nunca float). Lanza
    ValueError con un mensaje que nombra el archivo y el campo con problemas.
    """
    try:
        with path.open("rb") as file:
            data = tomllib.load(file, parse_float=Decimal)
    except OSError as error:
        raise ValueError(
            f"No se pudo leer el archivo de tarifas {path}: {error}"
        ) from error
    except tomllib.TOMLDecodeError as error:
        raise ValueError(
            f"El archivo de tarifas {path} no es TOML válido: {error}"
        ) from error
    try:
        return _parse(data)
    except ValueError as error:
        raise ValueError(f"Tarifas inválidas en {path}: {error}") from error


def _parse(data: dict[str, Any]) -> TariffTable:
    """Convierte el TOML ya leído en una TariffTable, validando cada campo."""
    _check_keys(data, {"modes", "zones", *_GENERAL_KEYS}, "")
    modes = data["modes"]
    if not (
        isinstance(modes, list)
        and all(isinstance(mode, str) for mode in modes)
        and sorted(modes) == sorted(MODES)
    ):
        raise ValueError(
            f"'modes' debe ser {list(MODES)}, las modalidades que el cotizador sabe "
            f"calcular; recibido: {modes!r}"
        )

    general = {key: _positive_decimal(data, key, "") for key in _GENERAL_KEYS}
    if general["min_weight_kg"] >= general["max_weight_kg"]:
        raise ValueError("'min_weight_kg' debe ser menor que 'max_weight_kg'")

    zones_data = data["zones"]
    if not isinstance(zones_data, dict) or not zones_data:
        raise ValueError("'zones' debe tener al menos una zona")
    zones: dict[str, ZoneTariff] = {}
    for name, zone in zones_data.items():
        prefix = f"zones.{name}."
        if not isinstance(zone, dict):
            raise ValueError(f"'zones.{name}' debe ser una tabla")  # noqa: TRY004 (dato inválido en el archivo)
        _check_keys(zone, set(_ZONE_KEYS), prefix)
        zones[name] = ZoneTariff(
            base=_positive_decimal(zone, "base", prefix),
            per_kg=_positive_decimal(zone, "per_kg", prefix),
            standard_days=_positive_int(zone, "standard_days", prefix),
            urgent_days=_positive_int(zone, "urgent_days", prefix),
        )

    return TariffTable(
        volumetric_divisor=general["volumetric_divisor"],
        min_weight_kg=general["min_weight_kg"],
        max_weight_kg=general["max_weight_kg"],
        urgent_surcharge_rate=general["urgent_surcharge_rate"],
        zones=MappingProxyType(zones),
    )


def _check_keys(table: dict[str, Any], expected: set[str], prefix: str) -> None:
    """Exige exactamente los campos esperados: ni faltantes ni desconocidos."""
    where = prefix.rstrip(".") or "la raíz"
    missing = sorted(expected - table.keys())
    if missing:
        raise ValueError(f"faltan campos en '{where}': {', '.join(missing)}")
    unknown = sorted(table.keys() - expected)
    if unknown:
        raise ValueError(f"campos desconocidos en '{where}': {', '.join(unknown)}")


def _positive_decimal(table: dict[str, Any], key: str, prefix: str) -> Decimal:
    """Lee un número (entero o decimal) finito y mayor que 0 como Decimal."""
    value = table[key]
    if isinstance(value, bool) or not isinstance(value, int | Decimal):
        raise ValueError(  # noqa: TRY004 (dato inválido en el archivo)
            f"'{prefix}{key}' debe ser un número; recibido: {value!r}"
        )
    number = Decimal(value)
    if not number.is_finite() or number <= 0:
        raise ValueError(f"'{prefix}{key}' debe ser mayor que 0; recibido: {value}")
    return number


def _positive_int(table: dict[str, Any], key: str, prefix: str) -> int:
    """Lee un entero mayor que 0 (los plazos son días hábiles enteros)."""
    value = table[key]
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(  # noqa: TRY004 (dato inválido en el archivo)
            f"'{prefix}{key}' debe ser un entero; recibido: {value!r}"
        )
    if value <= 0:
        raise ValueError(f"'{prefix}{key}' debe ser mayor que 0; recibido: {value}")
    return value


_TABLE: Final = load_tariffs(TARIFFS_PATH)

VOLUMETRIC_DIVISOR: Final = _TABLE.volumetric_divisor
MIN_WEIGHT_KG: Final = _TABLE.min_weight_kg
MAX_WEIGHT_KG: Final = _TABLE.max_weight_kg
URGENT_SURCHARGE_RATE: Final = _TABLE.urgent_surcharge_rate
ZONES: Final[Mapping[str, ZoneTariff]] = _TABLE.zones

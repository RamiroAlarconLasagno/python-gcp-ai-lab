# tests/test_tariffs.py
"""Pruebas de la carga de tarifas: el archivo real y archivos TOML inválidos."""

from decimal import Decimal
from pathlib import Path

import pytest

from app.tariffs import TARIFFS_PATH, ZONES, ZoneTariff, load_tariffs

VALID_TOML = """\
modes = ["standard", "urgent"]
volumetric_divisor = 5000
min_weight_kg = 0.1
max_weight_kg = 30
urgent_surcharge_rate = 0.50

[zones.amba]
base = 9500
per_kg = 1100
standard_days = 4
urgent_days = 2
"""


def write_toml(tmp_path: Path, text: str) -> Path:
    """Escribe un archivo de tarifas temporal y devuelve su ruta."""
    path = tmp_path / "tariffs.toml"
    path.write_text(text, encoding="utf-8")
    return path


def test_real_file_loads() -> None:
    """app/tariffs.toml carga con las cuatro zonas y los números como Decimal."""
    table = load_tariffs(TARIFFS_PATH)
    assert set(table.zones) == {"local", "amba", "national", "international"}
    assert table.zones["amba"] == ZoneTariff(
        base=Decimal(9500), per_kg=Decimal(1100), standard_days=4, urgent_days=2
    )
    assert table.volumetric_divisor == Decimal(5000)
    assert str(table.min_weight_kg) == "0.1"
    assert table.max_weight_kg == Decimal(30)
    assert str(table.urgent_surcharge_rate) == "0.50"
    assert isinstance(table.min_weight_kg, Decimal)


def test_zones_are_read_only() -> None:
    """ZONES no se puede modificar en tiempo de ejecución."""
    with pytest.raises(TypeError):
        ZONES["mars"] = ZONES["amba"]  # type: ignore[index]


def test_valid_template_loads(tmp_path: Path) -> None:
    """La plantilla de los casos inválidos es válida antes de romperla."""
    table = load_tariffs(write_toml(tmp_path, VALID_TOML))
    assert set(table.zones) == {"amba"}


@pytest.mark.parametrize(
    ("old", "new", "message"),
    [
        ("[zones.amba]", "[zones.amba", "no es TOML válido"),
        ("per_kg = 1100\n", "", r"faltan campos en 'zones\.amba': per_kg"),
        ("urgent_days = 2", "urgent_days = 2\nexpress_days = 1", "campos desconocidos"),
        ("base = 9500", "base = 0", r"'zones\.amba\.base' debe ser mayor que 0"),
        ("max_weight_kg = 30", "max_weight_kg = -1", "'max_weight_kg' debe ser mayor"),
        ("base = 9500", 'base = "9500"', r"'zones\.amba\.base' debe ser un número"),
        ("standard_days = 4", "standard_days = 4.5", "debe ser un entero"),
        ('modes = ["standard", "urgent"]', 'modes = ["standard"]', "'modes' debe ser"),
        ("min_weight_kg = 0.1", "min_weight_kg = 40", "debe ser menor que"),
    ],
)
def test_invalid_toml_fails_clearly(
    tmp_path: Path, old: str, new: str, message: str
) -> None:
    """Un archivo inválido falla con ValueError que nombra el archivo y el problema."""
    assert old in VALID_TOML
    path = write_toml(tmp_path, VALID_TOML.replace(old, new))
    with pytest.raises(ValueError, match=message) as error:
        load_tariffs(path)
    assert str(path) in str(error.value)


def test_missing_file_fails_clearly(tmp_path: Path) -> None:
    """Si el archivo no existe, el error lo dice con la ruta."""
    path = tmp_path / "missing.toml"
    with pytest.raises(ValueError, match="No se pudo leer"):
        load_tariffs(path)

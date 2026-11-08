# tests/test_smoke.py
"""Prueba mínima: confirma que el paquete app se puede importar."""

import app


def test_app_is_importable() -> None:
    """El paquete app se importa y es el de este repositorio."""
    assert app.__name__ == "app"

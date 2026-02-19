"""Utilidades de manejo de errores.

Responsabilidad:
- Estandarizar presentación/serialización de errores.
"""


def error_to_text(error: Exception) -> str:
    """Convierte excepción a texto amigable."""
    return f"{type(error).__name__}: {error}"

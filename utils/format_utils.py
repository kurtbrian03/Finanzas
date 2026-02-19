"""Utilidades de formato.

Responsabilidad:
- Formato de números, porcentajes y textos de salida.
"""


def format_percent(value: float) -> str:
    """Formatea porcentaje con 2 decimales."""
    return f"{value:.2f}%"

"""Fábrica de registros de auditoría.

Responsabilidad:
- Construir eventos homogéneos para logs e historial.
"""

from datetime import datetime


def build_record(accion: str, detalle: str) -> dict[str, str]:
    """Crea un registro de auditoría consistente."""
    return {
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "accion": accion,
        "detalle": detalle,
    }

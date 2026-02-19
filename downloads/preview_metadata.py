"""Métricas de previsualización para descargas.

Responsabilidad:
- Calcular resumen previo (cantidad, tamaño, tipos) antes de descarga manual.
"""

from __future__ import annotations

import pandas as pd


def resumen_previsualizacion(df: pd.DataFrame) -> dict[str, float | int]:
    """Retorna métricas resumidas para panel de previsualización."""
    if df.empty:
        return {"documentos": 0, "tamano_kb": 0.0, "tipos": 0}
    return {
        "documentos": int(len(df)),
        "tamano_kb": float(df["tamano_kb"].sum()),
        "tipos": int(df["extension"].nunique()),
    }

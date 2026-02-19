"""Utilidades específicas de Excel.

Responsabilidad:
- Clasificación de tipos semánticos de columnas.
"""

from __future__ import annotations

import pandas as pd


def clasificar_columna(serie: pd.Series) -> str:
    """Clasifica una columna como numérica/fecha/categórica/texto."""
    if pd.api.types.is_numeric_dtype(serie):
        return "numérica"
    if pd.api.types.is_datetime64_any_dtype(serie):
        return "fecha"
    muestra = serie.dropna().astype(str).head(40)
    if muestra.empty:
        return "texto"
    parseadas = pd.to_datetime(muestra, errors="coerce", dayfirst=True)
    if parseadas.notna().mean() > 0.7:
        return "fecha"
    cardinalidad = serie.nunique(dropna=True)
    if cardinalidad <= max(10, int(len(serie) * 0.1)):
        return "categórica"
    return "texto"

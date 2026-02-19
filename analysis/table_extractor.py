"""Extracción de tablas en PDF y utilidades tabulares.

Responsabilidad:
- Extraer tablas desde páginas PDF.
- Calcular outliers y correlaciones para datasets.
"""

from __future__ import annotations

import fitz
import numpy as np
import pandas as pd


def extraer_tablas_pdf(page: fitz.Page, max_tables: int = 2) -> list[list[list[str]]]:
    """Extrae tablas detectadas en una página PDF."""
    tablas_detectadas: list[list[list[str]]] = []
    try:
        tables = page.find_tables().tables
        if tables:
            for table in tables[:max_tables]:
                extract = table.extract()
                if extract:
                    tablas_detectadas.append(extract[:5])
    except Exception:
        return []
    return tablas_detectadas


def detectar_outliers_iqr(df: pd.DataFrame, numeric_cols: list[str]) -> list[dict[str, int | str]]:
    """Calcula conteo de outliers por columna numérica."""
    outliers = []
    for col in numeric_cols:
        series = df[col].dropna()
        if series.empty:
            continue
        q1, q3 = series.quantile(0.25), series.quantile(0.75)
        iqr = q3 - q1
        if iqr == 0:
            continue
        lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        qty = int(((series < lo) | (series > hi)).sum())
        if qty > 0:
            outliers.append({"columna": col, "outliers": qty})
    return outliers


def correlacion_numerica(df: pd.DataFrame, numeric_cols: list[str]) -> pd.DataFrame:
    """Retorna matriz de correlación para columnas numéricas."""
    if len(numeric_cols) < 2:
        return pd.DataFrame()
    return df[numeric_cols].corr(numeric_only=True)


def encontrar_correlaciones_fuertes(corr: pd.DataFrame, threshold: float = 0.7) -> bool:
    """Evalúa si existen correlaciones de magnitud alta."""
    if corr.empty:
        return False
    upper = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool)).stack()
    return not upper[upper.abs() >= threshold].empty

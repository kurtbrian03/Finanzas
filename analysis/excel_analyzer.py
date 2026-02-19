"""Análisis automático avanzado de Excel.

Responsabilidad:
- Generar perfilado de columnas, estadísticas, outliers, correlaciones e insights.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .table_extractor import correlacion_numerica, detectar_outliers_iqr, encontrar_correlaciones_fuertes
from utils.excel_utils import clasificar_columna


def analizar_excel(df: pd.DataFrame) -> dict[str, object]:
    """Ejecuta análisis integral de dataset Excel."""
    calidad = pd.DataFrame(
        {
            "columna": df.columns.astype(str),
            "tipo": [clasificar_columna(df[col]) for col in df.columns],
            "dtype": [str(df[col].dtype) for col in df.columns],
            "nulos": [int(df[col].isna().sum()) for col in df.columns],
            "nulos_%": [round(float(df[col].isna().mean() * 100), 2) for col in df.columns],
            "duplicados_valor": [int(df[col].duplicated().sum()) for col in df.columns],
            "ejemplo": [str(df[col].dropna().head(1).iloc[0]) if not df[col].dropna().empty else "" for col in df.columns],
        }
    )

    num_cols = df.select_dtypes(include=["number"]).columns.tolist()
    estadisticas = pd.DataFrame()
    if num_cols:
        estadisticas = pd.DataFrame(
            {
                "media": df[num_cols].mean(numeric_only=True),
                "mediana": df[num_cols].median(numeric_only=True),
                "min": df[num_cols].min(numeric_only=True),
                "max": df[num_cols].max(numeric_only=True),
                "std": df[num_cols].std(numeric_only=True),
                "conteo": df[num_cols].count(),
            }
        )

    outliers = detectar_outliers_iqr(df, num_cols)
    corr = correlacion_numerica(df, num_cols)

    duplicados_fila = int(df.duplicated().sum())
    celdas_totales = int(df.shape[0] * df.shape[1])
    nulos_total = int(df.isna().sum().sum())
    nulos_pct = round((nulos_total / celdas_totales * 100), 2) if celdas_totales else 0.0

    resumen = (
        f"Dataset con {len(df):,} filas y {len(df.columns):,} columnas. "
        f"Nulos totales: {nulos_total:,} ({nulos_pct}%). "
        f"Duplicados por fila: {duplicados_fila:,}."
    )

    insights: list[str] = []
    if nulos_pct > 20:
        insights.append("Calidad de datos comprometida por alto porcentaje de valores nulos.")
    if duplicados_fila > 0:
        insights.append("Existen filas duplicadas; revisar consolidación de registros.")
    if outliers:
        insights.append("Se detectaron valores atípicos en columnas numéricas clave.")
    if encontrar_correlaciones_fuertes(corr, 0.7):
        insights.append("Hay correlaciones fuertes que sugieren relaciones entre variables.")
    if not insights:
        insights.append("Calidad general estable sin anomalías críticas automáticas.")

    return {
        "calidad": calidad,
        "estadisticas": estadisticas,
        "outliers": pd.DataFrame(outliers),
        "correlacion": corr,
        "resumen": resumen,
        "insights": insights,
        "num_cols": num_cols,
        "nulos_total": nulos_total,
        "duplicados": duplicados_fila,
    }

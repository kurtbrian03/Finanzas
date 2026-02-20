"""Análisis automático avanzado de PDF.

Responsabilidad:
- Consolidar extracción de texto, estructura, entidades, tablas, patrones y tono.
"""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

import pymupdf as fitz
import numpy as np
import streamlit as st

from .entity_detector import extraer_entidades
from .table_extractor import extraer_tablas_pdf
from .tone_analyzer import analizar_tono_y_proposito
from utils.pdf_utils import limpiar_tokens


@st.cache_data(show_spinner=False)
def analizar_pdf(path_str: str, max_paginas: int) -> dict[str, object]:
    """Ejecuta análisis integral de un PDF."""
    path = Path(path_str)
    doc = fitz.open(path)
    total_paginas = doc.page_count
    paginas_analisis = min(max_paginas, total_paginas)
    textos: list[str] = []
    lineas: list[str] = []
    tablas_total = 0
    tablas_detectadas: list[list[list[str]]] = []

    for i in range(paginas_analisis):
        page = doc.load_page(i)
        txt = page.get_text("text")
        textos.append(txt)
        lineas.extend([ln.strip() for ln in txt.splitlines() if ln.strip()])
        tables = extraer_tablas_pdf(page)
        if tables:
            tablas_total += len(tables)
            tablas_detectadas.extend(tables)

    doc.close()
    texto_total = "\n".join(textos)
    top_tokens = [p for p, _ in Counter(limpiar_tokens(texto_total)).most_common(12)]

    parrafos = [p.strip() for p in texto_total.split("\n\n") if p.strip()]
    resumen = " ".join(parrafos[:3])[:1800] if parrafos else "No se encontró texto suficiente."

    hallazgos: list[str] = []
    for ln in lineas:
        ln_lower = ln.lower()
        if any(k in ln_lower for k in ["total", "importe", "venc", "riesgo", "conclus", "impuesto"]):
            hallazgos.append(ln)
        if len(hallazgos) >= 10:
            break

    encabezados = [
        ln for ln in lineas
        if len(ln) < 120 and (ln.isupper() or re.match(r"^\d+(\.\d+)*\s+", ln))
    ][:25]
    subsecciones = [h for h in encabezados if re.match(r"^\d+\.\d+", h)]

    montos_numericos: list[float] = []
    for m in re.findall(r"\$?\s?\d{1,3}(?:[,.]\d{3})*(?:[.,]\d{2})", texto_total):
        limpio = m.replace("$", "").replace(" ", "").replace(",", "")
        limpio = limpio.replace(".", "", max(0, limpio.count(".") - 1))
        try:
            montos_numericos.append(float(limpio))
        except ValueError:
            continue

    repetitivas = [linea for linea, n in Counter(lineas).items() if n > 2][:20]
    anomalias: list[str] = []
    if montos_numericos:
        q1, q3 = np.percentile(montos_numericos, [25, 75])
        iqr = q3 - q1
        low, high = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        outliers = [x for x in montos_numericos if x < low or x > high]
        if outliers:
            anomalias.append(f"Montos atípicos detectados: {len(outliers)}")
    if repetitivas:
        anomalias.append(f"Líneas repetitivas detectadas: {len(repetitivas)}")

    tono, proposito = analizar_tono_y_proposito(texto_total, len(encabezados))
    entidades = extraer_entidades(texto_total)

    insights: list[str] = []
    if "cfdi" in texto_total.lower() or "factura" in texto_total.lower():
        insights.append("El contenido sugiere documentación fiscal o comprobantes de pago.")
    if anomalias:
        insights.append("Se identificaron patrones que requieren revisión manual adicional.")
    if len(entidades["Identificadores"]) > 8:
        insights.append("Alta densidad de identificadores; revisar consistencia entre RFC/UUID.")
    if not insights:
        insights.append("No se detectan señales críticas evidentes en el análisis automático.")

    return {
        "total_paginas": total_paginas,
        "paginas_analizadas": paginas_analisis,
        "resumen": resumen,
        "hallazgos": hallazgos,
        "secciones": encabezados,
        "subsecciones": subsecciones,
        "tablas_total": tablas_total,
        "tablas_detectadas": tablas_detectadas,
        "entidades": entidades,
        "anomalias": anomalias,
        "tono": tono,
        "proposito": proposito,
        "tokens": top_tokens,
        "insights": insights,
        "texto_len": len(texto_total),
    }

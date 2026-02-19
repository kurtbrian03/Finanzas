"""Componentes visuales reutilizables.

Responsabilidad:
- Renderizar previews y paneles de análisis para documentos.
"""

from __future__ import annotations

from pathlib import Path

import fitz
import pandas as pd
import streamlit as st

from analysis.excel_analyzer import analizar_excel
from analysis.pdf_analyzer import analizar_pdf
from config.constants import CARPETAS_FORMATO
from downloads.downloader import descargar_archivo, mime_for
from utils.file_utils import read_text_safe


def render_top_bar(usuario: str) -> None:
    """Renderiza barra superior con estado de sistema."""
    c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
    with c1:
        st.title("💰 Sistema Fiscal Documental")
    with c2:
        st.metric("Estado", "Operativo")
    with c3:
        st.metric("Usuario", usuario if usuario else "Invitado")
    with c4:
        st.metric("Conexión", "Local")


def render_footer(logs_count: int, version: str) -> None:
    """Renderiza pie de página estándar."""
    st.divider()
    f1, f2, f3 = st.columns([2, 1, 1])
    with f1:
        st.caption(f"Logs internos: {logs_count} registros")
    with f2:
        st.caption(f"Versión: {version}")
    with f3:
        st.caption("Conexión: estable")


@st.cache_data(show_spinner=False)
def listar_archivos_por_formato(carpeta_base: str) -> dict[str, list[str]]:
    """Lista archivos por formato según subcarpetas de FACTURACION."""
    base = Path(carpeta_base)
    resultado: dict[str, list[str]] = {k: [] for k in CARPETAS_FORMATO}
    if not base.exists() or not base.is_dir():
        return resultado
    for categoria, extensiones in CARPETAS_FORMATO.items():
        sub = base / categoria
        if not sub.exists() or not sub.is_dir():
            continue
        archivos = [
            str(p)
            for p in sub.rglob("*")
            if p.is_file() and p.suffix.lower() in extensiones
        ]
        resultado[categoria] = sorted(archivos, key=lambda x: Path(x).name.lower())
    return resultado


def render_pdf_preview(path: Path, zoom: float, max_paginas_analisis: int) -> dict[str, object] | None:
    """Renderiza PDF en panel principal y retorna análisis."""
    try:
        doc = fitz.open(path)
    except Exception as error:
        st.error(f"No se pudo abrir el PDF: {error}")
        return None

    total = doc.page_count
    if total == 0:
        st.warning("El PDF no contiene páginas.")
        doc.close()
        return None

    st.write("### Vista previa integrada (solo lectura)")
    nav_col1, nav_col2 = st.columns([1, 1])
    with nav_col1:
        pagina_actual = st.number_input("Navegar a página", 1, total, 1, 1, key=f"nav_{path}")
    with nav_col2:
        mostrar_todas = st.checkbox("Mostrar todas las páginas", value=True, key=f"all_{path}")

    indices = list(range(total)) if mostrar_todas else [int(pagina_actual) - 1]
    for idx in indices:
        page = doc.load_page(idx)
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
        st.image(
            pix.tobytes("png"),
            caption=f"Página {idx + 1} de {total}",
            use_container_width=True,
        )
    doc.close()
    return analizar_pdf(str(path), max_paginas_analisis)


def render_excel_preview(path: Path) -> tuple[dict[str, object] | None, str]:
    """Renderiza Excel de solo lectura y retorna análisis + hoja seleccionada."""
    try:
        excel = pd.ExcelFile(path)
    except Exception as error:
        st.error(f"No se pudo abrir el Excel: {error}")
        return None, ""

    hojas = excel.sheet_names
    if not hojas:
        st.warning("El archivo Excel no contiene hojas.")
        return None, ""

    hoja = st.selectbox("Hoja", hojas, key=f"hoja_{path}")
    try:
        df = pd.read_excel(excel, sheet_name=hoja)
    except Exception as error:
        st.error(f"No se pudo leer la hoja seleccionada: {error}")
        return None, hoja

    st.write("### Vista previa integrada (solo lectura)")
    st.dataframe(df, use_container_width=True, height=560)
    return analizar_excel(df), hoja


def render_text_code_preview(path: Path, formato: str) -> None:
    """Renderiza vista de texto/código en solo lectura."""
    st.write("### Vista previa integrada (solo lectura)")
    contenido = read_text_safe(path)
    if formato == "PYTHON":
        st.code(contenido, language="python")
    elif formato == "POWERSHELL":
        st.code(contenido, language="powershell")
    else:
        st.text_area("Contenido", value=contenido, height=560)


def render_image_preview(path: Path) -> None:
    """Renderiza vista de imagen con metadatos básicos."""
    st.write("### Vista previa integrada (solo lectura)")
    st.image(str(path), caption=path.name, use_container_width=True)
    try:
        size = path.stat().st_size
    except Exception:
        size = 0
    st.caption(f"Ruta: {path}")
    st.caption(f"Tamaño: {size:,} bytes")


def render_download_control(path: Path) -> None:
    """Renderiza control de descarga manual para archivo seleccionado."""
    descargar_archivo(path, mime_for(path))


def render_pdf_analysis_panel(analisis: dict[str, object]) -> None:
    """Renderiza resultados del análisis PDF."""
    st.write("### Análisis PDF")
    st.write("**Resumen ejecutivo detallado**")
    st.write(analisis["resumen"])
    st.write("**Puntos clave y hallazgos**")
    if analisis["hallazgos"]:
        for item in analisis["hallazgos"][:10]:
            st.write(f"- {item}")
    else:
        st.write("- Sin hallazgos textuales destacados en la extracción automática.")
    st.write("**Análisis de estructura**")
    st.write(f"- Páginas totales: {analisis['total_paginas']}")
    st.write(f"- Páginas analizadas: {analisis['paginas_analizadas']}")
    st.write(f"- Secciones detectadas: {len(analisis['secciones'])}")
    st.write(f"- Subsecciones detectadas: {len(analisis['subsecciones'])}")
    st.write(f"- Tablas detectadas: {analisis['tablas_total']}")
    st.write("**Detección de entidades**")
    for clave, valores in analisis["entidades"].items():
        st.write(f"- {clave}: {', '.join(valores[:5]) if valores else 'No detectado'}")
    st.write("**Extracción de tablas**")
    if analisis["tablas_detectadas"]:
        for i, table in enumerate(analisis["tablas_detectadas"][:2], start=1):
            st.write(f"Tabla {i}")
            st.dataframe(pd.DataFrame(table), use_container_width=True)
    else:
        st.write("- No se detectaron tablas estructuradas de forma automática.")
    st.write("**Patrones y anomalías**")
    if analisis["anomalias"]:
        for item in analisis["anomalias"]:
            st.write(f"- {item}")
    else:
        st.write("- No se detectaron anomalías críticas evidentes.")
    st.write("**Tono y propósito**")
    st.write(f"- Enfoque: {analisis['tono']}")
    st.write(f"- Propósito: {analisis['proposito']}")
    st.write("**Insights adicionales**")
    for insight in analisis["insights"]:
        st.write(f"- {insight}")


def render_excel_analysis_panel(analisis: dict[str, object]) -> None:
    """Renderiza resultados del análisis Excel."""
    st.write("### Análisis Excel")
    st.write("**Resumen ejecutivo**")
    st.write(analisis["resumen"])
    st.write("**Descripción de columnas**")
    st.dataframe(analisis["calidad"], use_container_width=True, height=220)
    st.write("**Estadísticas descriptivas**")
    if not analisis["estadisticas"].empty:
        st.dataframe(analisis["estadisticas"], use_container_width=True, height=220)
    else:
        st.write("- No hay columnas numéricas para estadística descriptiva.")
    st.write("**Outliers y calidad de datos**")
    st.write(f"- Nulos totales: {analisis['nulos_total']}")
    st.write(f"- Filas duplicadas: {analisis['duplicados']}")
    if not analisis["outliers"].empty:
        st.dataframe(analisis["outliers"], use_container_width=True)
    else:
        st.write("- Sin outliers detectados por IQR.")
    st.write("**Correlaciones**")
    if not analisis["correlacion"].empty:
        st.dataframe(analisis["correlacion"], use_container_width=True, height=220)
    else:
        st.write("- No hay suficientes columnas numéricas para correlación.")
    st.write("**Insights basados en datos**")
    for insight in analisis["insights"]:
        st.write(f"- {insight}")

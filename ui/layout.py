"""Layouts por módulo/pantalla.

Responsabilidad:
- Orquestar composición de UI usando componentes y servicios de dominio.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None

from core.state_manager import StateManager
from dropbox_integration.analytics_engine import analizar_documentos, construir_resumen_analitico
from dropbox_integration.audit_diff import (
    compare_auditoria_snapshots,
    export_auditoria_diff_csv,
    export_auditoria_diff_json,
    export_auditoria_diff_txt,
)
from dropbox_integration.folder_tree import (
    aplicar_filtros_virtuales,
    breadcrumbs_virtuales,
    construir_arbol_virtual,
    opciones_filtros_virtuales,
    resumen_arbol,
)
from dropbox_integration.metrics import bytes_humanos, calcular_metricas
from dropbox_integration.image_viewer import mostrar_en_streamlit as mostrar_imagen_streamlit
from dropbox_integration.aspel_invoice_menu import _find_pdf_invoices
from dropbox_integration.content_extractor import extraer_contenido_archivo
from dropbox_integration.dropbox_structure import (
    move_invoices_to_provider_folders,
    validate_dropbox_structure,
)
from dropbox_integration.image_renamer import _rename_images_by_folder
from dropbox_integration.invoice_provider_classifier import classify_invoice_provider
from dropbox_integration.invoice_receptor_analytics import build_invoices_dataset, summarize_by_receptor
from dropbox_integration.report_generator import generar_paquete_reportes
from dropbox_integration.search_engine import SearchEngine, construir_estadisticas_busqueda
from downloads.download_filters import aplicar_filtros, indexar_documentos
from downloads.file_packager import construir_zip_memoria
from downloads.preview_metadata import resumen_previsualizacion
from history.history_manager import register_action
from ui.components import (
    listar_archivos_por_formato,
    render_download_control,
    render_excel_analysis_panel,
    render_excel_preview,
    render_image_preview,
    render_pdf_analysis_panel,
    render_pdf_preview,
    render_text_code_preview,
)
from validation.folio_validator import validar_folio
from validation.rfc_validator import validar_rfc
from validation.cfdi_sat_api import _validate_cfdi_sat


logger = logging.getLogger(__name__)


def _load_env_for_dropbox_auth() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    env_path = repo_root / ".env"
    if not env_path.exists():
        env_path.write_text("DROPBOX_ADMIN_PASS=pinpirin666\n", encoding="utf-8")

    if load_dotenv is not None:
        load_dotenv(dotenv_path=env_path, override=False)
    else:
        logging.warning("python-dotenv no está instalado; no se pudo cargar .env")


def _default_boosting_weights() -> dict[str, float]:
    """Pesos por defecto para boosting contextual y ponderadores de score."""
    return {
        "boost_proveedor": 1.0,
        "boost_hospital": 1.0,
        "boost_mes": 1.0,
        "boost_anio": 1.0,
        "boost_tipo": 1.0,
        "boost_temporal": 1.0,
        "score_exacto": 1.0,
        "score_fuzzy": 1.0,
        "score_semantico": 1.0,
        "score_contenido": 1.0,
        "score_tokens": 1.0,
        "score_temporal": 1.0,
        "score_estructural": 1.0,
    }


def _render_search_audit_panel(
    engine: SearchEngine,
    resultados_df: pd.DataFrame,
    audit_log: list[dict[str, object]],
    weights_aplicados: dict[str, Any],
    boost_aplicado: dict[str, Any],
    out_dir: Path,
) -> None:
    """Renderiza panel de auditoría visual para ranking híbrido avanzado."""
    st.markdown("### Auditoría avanzada del ranking")

    score_cols = [
        "score_exacto",
        "score_fuzzy",
        "score_semantico",
        "score_tokens",
        "score_temporal",
        "score_estructural",
        "score_boosting",
        "score_final",
    ]
    cols_presentes = [c for c in score_cols if c in resultados_df.columns]
    if cols_presentes:
        base_cols = [c for c in ["nombre", "tipo", "carpeta", "relevancia"] if c in resultados_df.columns]
        st.caption("Descomposición de score por resultado")
        st.dataframe(resultados_df[base_cols + cols_presentes], use_container_width=True, height=260)

        d1, d2 = st.columns(2)
        with d1:
            if "score_final" in resultados_df.columns:
                st.caption("Distribución score final")
                st.bar_chart(resultados_df["score_final"])
        with d2:
            factores = {
                "exacto": float(resultados_df.get("score_exacto", pd.Series(dtype=float)).mean() or 0.0),
                "fuzzy": float(resultados_df.get("score_fuzzy", pd.Series(dtype=float)).mean() or 0.0),
                "semantico": float(resultados_df.get("score_semantico", pd.Series(dtype=float)).mean() or 0.0),
                "tokens": float(resultados_df.get("score_tokens", pd.Series(dtype=float)).mean() or 0.0),
                "temporal": float(resultados_df.get("score_temporal", pd.Series(dtype=float)).mean() or 0.0),
                "estructural": float(resultados_df.get("score_estructural", pd.Series(dtype=float)).mean() or 0.0),
                "boosting": float(resultados_df.get("score_boosting", pd.Series(dtype=float)).mean() or 0.0),
            }
            st.caption("Top factores promedio")
            st.bar_chart(pd.Series(factores).sort_values(ascending=False))
    else:
        st.info("La auditoría de score no está disponible para este conjunto de resultados.")

    p1, p2 = st.columns(2)
    with p1:
        st.caption("Pesos aplicados")
        st.dataframe(pd.DataFrame([weights_aplicados]), use_container_width=True, height=120)
    with p2:
        st.caption("Boosting aplicado")
        st.dataframe(pd.DataFrame([boost_aplicado]), use_container_width=True, height=120)

    st.caption("Logs del motor de búsqueda")
    if audit_log:
        st.dataframe(pd.DataFrame(audit_log), use_container_width=True, height=240)
    else:
        st.info("No hay eventos de auditoría para mostrar.")

    st.caption("Exportación de auditoría")
    e1, e2 = st.columns(2)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"dropbox_search_audit_{ts}.json"
    csv_path = out_dir / f"dropbox_search_audit_{ts}.csv"

    with e1:
        if st.button("Exportar auditoría (JSON)", key=f"export_audit_json_{ts}", use_container_width=True):
            try:
                exportado = engine.export_auditoria_json(str(json_path))
                st.success(f"JSON exportado: {exportado.name}")
            except Exception as error:
                st.error(f"Error al exportar JSON de auditoría: {error}")

        if json_path.exists():
            st.download_button(
                "Descargar auditoría JSON",
                data=json_path.read_bytes(),
                file_name=json_path.name,
                mime="application/json",
                use_container_width=True,
                key=f"download_audit_json_{ts}",
            )

    with e2:
        if st.button("Exportar auditoría (CSV)", key=f"export_audit_csv_{ts}", use_container_width=True):
            try:
                exportado = engine.export_auditoria_csv(str(csv_path))
                st.success(f"CSV exportado: {exportado.name}")
            except Exception as error:
                st.error(f"Error al exportar CSV de auditoría: {error}")

        if csv_path.exists():
            st.download_button(
                "Descargar auditoría CSV",
                data=csv_path.read_bytes(),
                file_name=csv_path.name,
                mime="text/csv",
                use_container_width=True,
                key=f"download_audit_csv_{ts}",
            )


def _render_search_performance_panel(engine: SearchEngine, out_dir: Path) -> None:
    """Renderiza panel de perfilado de performance del motor de búsqueda."""
    st.markdown("### Perfil de performance del motor")

    perf = engine.get_last_performance_metrics()
    if not isinstance(perf, dict) or not perf:
        st.info("No hay métricas de performance disponibles. Ejecuta una búsqueda con profiling activo.")
        return

    total_ms = float(perf.get("total_time_ms", 0.0) or 0.0)
    timestamp = str(perf.get("timestamp", ""))
    version = str(perf.get("version_motor", ""))
    components = perf.get("components", {}) if isinstance(perf.get("components", {}), dict) else {}

    rows: list[dict[str, object]] = []
    for component, value in components.items():
        comp_ms = float(value or 0.0)
        pct = (comp_ms / total_ms * 100.0) if total_ms > 0 else 0.0
        rows.append({"component": str(component), "time_ms": round(comp_ms, 4), "share_pct": round(pct, 2)})

    perf_df = pd.DataFrame(rows)
    if perf_df.empty:
        st.info("No se encontraron componentes de performance para mostrar.")
        return

    perf_df = perf_df.sort_values(by="time_ms", ascending=False).reset_index(drop=True)
    top_component = str(perf_df.iloc[0]["component"]) if not perf_df.empty else ""
    top_component_ms = float(perf_df.iloc[0]["time_ms"]) if not perf_df.empty else 0.0

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Tiempo total", f"{total_ms:.2f} ms")
    m2.metric("Componentes", f"{len(perf_df):,}")
    m3.metric("Componente más costoso", top_component)
    m4.metric("Tiempo componente top", f"{top_component_ms:.2f} ms")
    st.caption(f"Versión motor: {version} · Timestamp: {timestamp}")

    p1, p2 = st.columns(2)
    with p1:
        st.caption("Tabla de componentes")
        st.dataframe(perf_df, use_container_width=True, height=280)
    with p2:
        st.caption("Tiempo por componente (ms)")
        st.vega_lite_chart(
            perf_df,
            {
                "mark": {"type": "bar", "color": "#1E88E5"},
                "encoding": {
                    "x": {"field": "component", "type": "nominal", "sort": "-y"},
                    "y": {"field": "time_ms", "type": "quantitative"},
                    "tooltip": [
                        {"field": "component", "type": "nominal"},
                        {"field": "time_ms", "type": "quantitative"},
                        {"field": "share_pct", "type": "quantitative"},
                    ],
                },
            },
            use_container_width=True,
        )

    st.caption("Exportación de performance")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir.mkdir(parents=True, exist_ok=True)
    perf_json = out_dir / f"dropbox_search_performance_{ts}.json"
    perf_csv = out_dir / f"dropbox_search_performance_{ts}.csv"
    e1, e2 = st.columns(2)

    with e1:
        if st.button("Exportar performance (JSON)", key=f"export_perf_json_{ts}", use_container_width=True):
            try:
                exportado = engine.export_performance_json(str(perf_json))
                st.success(f"JSON exportado: {exportado.name}")
            except Exception as error:
                st.error(f"Error al exportar JSON de performance: {error}")

        if perf_json.exists():
            st.download_button(
                "Descargar performance JSON",
                data=perf_json.read_bytes(),
                file_name=perf_json.name,
                mime="application/json",
                use_container_width=True,
                key=f"download_perf_json_{ts}",
            )

    with e2:
        if st.button("Exportar performance (CSV)", key=f"export_perf_csv_{ts}", use_container_width=True):
            try:
                exportado = engine.export_performance_csv(str(perf_csv))
                st.success(f"CSV exportado: {exportado.name}")
            except Exception as error:
                st.error(f"Error al exportar CSV de performance: {error}")

        if perf_csv.exists():
            st.download_button(
                "Descargar performance CSV",
                data=perf_csv.read_bytes(),
                file_name=perf_csv.name,
                mime="text/csv",
                use_container_width=True,
                key=f"download_perf_csv_{ts}",
            )


def _render_cfdi_validation_result(result: dict[str, object]) -> None:
    """Renderiza estado de validación CFDI SAT en UI."""
    estado = str(result.get("estado", "")).strip().lower()
    mensaje = str(result.get("mensaje", "")).strip()
    fecha_consulta = str(result.get("fecha_consulta", "")).strip()

    if estado == "vigente":
        st.success(f"CFDI vigente. {mensaje}")
    elif estado == "cancelado":
        st.warning(f"CFDI cancelado. {mensaje}")
    else:
        st.error(f"CFDI no encontrado/indeterminado. {mensaje}")

    st.caption(f"Fecha consulta: {fecha_consulta}")
    st.json(
        {
            "uuid": result.get("uuid", ""),
            "rfc_emisor": result.get("rfc_emisor", ""),
            "rfc_receptor": result.get("rfc_receptor", ""),
            "total": result.get("total", ""),
            "estado": result.get("estado", ""),
            "provider": result.get("provider", ""),
        }
    )


def load_audit_snapshot(path: Path) -> dict[str, object]:
    """Carga snapshot de auditoría de forma segura."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return {}
    return payload


def _find_audit_snapshots(docs_dir: Path) -> list[Path]:
    """Descubre snapshots históricos de auditoría en docs/versions y reportes."""
    versioned = sorted((docs_dir / "versions").glob("**/*search_audit*.json")) if (docs_dir / "versions").exists() else []
    reportes = sorted((docs_dir / "reportes").glob("*search_audit*.json")) if (docs_dir / "reportes").exists() else []
    candidatos = [p for p in [*versioned, *reportes] if p.is_file() and "diff" not in p.name.lower()]
    unicos: dict[str, Path] = {str(p.resolve()): p for p in candidatos}
    return sorted(unicos.values(), key=lambda p: p.stat().st_mtime)


def _snapshot_score_summary(snapshot_payload: dict[str, object]) -> dict[str, float]:
    resultados = snapshot_payload.get("resultados_scores", [])
    if not isinstance(resultados, list) or not resultados:
        return {
            "score_final_avg": 0.0,
            "score_exacto_avg": 0.0,
            "score_fuzzy_avg": 0.0,
            "score_semantico_avg": 0.0,
            "score_temporal_avg": 0.0,
            "score_estructural_avg": 0.0,
            "score_boosting_avg": 0.0,
        }

    df = pd.DataFrame(resultados)

    def _avg(col: str) -> float:
        if col not in df.columns:
            return 0.0
        return float(pd.to_numeric(df[col], errors="coerce").fillna(0.0).mean())

    return {
        "score_final_avg": _avg("score_final"),
        "score_exacto_avg": _avg("score_exacto"),
        "score_fuzzy_avg": _avg("score_fuzzy"),
        "score_semantico_avg": _avg("score_semantico"),
        "score_temporal_avg": _avg("score_temporal"),
        "score_estructural_avg": _avg("score_estructural"),
        "score_boosting_avg": _avg("score_boosting"),
    }


def _render_search_historical_panel(docs_dir: Path) -> None:
    """Panel histórico de auditoría del motor de búsqueda."""
    st.markdown("<h3 style='color:#1565C0'>Auditoría histórica del motor de búsqueda</h3>", unsafe_allow_html=True)
    st.caption("Compara snapshots históricos para evaluar evolución de relevancia, ranking y componentes de score.")

    snapshots = _find_audit_snapshots(docs_dir)
    if not snapshots:
        st.info("No se encontraron snapshots de auditoría histórica.")
        return

    evo_rows: list[dict[str, object]] = []
    for p in snapshots:
        try:
            payload = load_audit_snapshot(p)
            score = _snapshot_score_summary(payload)
            evo_rows.append(
                {
                    "snapshot": p.name,
                    "path": str(p),
                    "score_final_avg": score["score_final_avg"],
                    "score_exacto_avg": score["score_exacto_avg"],
                    "score_fuzzy_avg": score["score_fuzzy_avg"],
                    "score_semantico_avg": score["score_semantico_avg"],
                    "score_temporal_avg": score["score_temporal_avg"],
                    "score_estructural_avg": score["score_estructural_avg"],
                    "score_boosting_avg": score["score_boosting_avg"],
                }
            )
        except Exception:
            continue

    if not evo_rows:
        st.info("No fue posible cargar snapshots de auditoría válidos.")
        return

    evo_df = pd.DataFrame(evo_rows)
    st.vega_lite_chart(
        evo_df,
        {
            "mark": {"type": "line", "point": True, "color": "#1E88E5"},
            "encoding": {
                "x": {"field": "snapshot", "type": "nominal", "sort": None},
                "y": {"field": "score_final_avg", "type": "quantitative"},
                "tooltip": [
                    {"field": "snapshot", "type": "nominal"},
                    {"field": "score_final_avg", "type": "quantitative"},
                ],
            },
            "title": "Evolución score_final promedio por snapshot",
        },
        use_container_width=True,
    )

    if len(evo_df) < 2:
        st.info("Se requieren al menos 2 snapshots para comparación A/B.")
        return

    opciones = list(evo_df["path"].astype(str))
    default_a = max(0, len(opciones) - 2)
    default_b = len(opciones) - 1
    s1, s2 = st.columns(2)
    with s1:
        snap_a = st.selectbox("Snapshot A (anterior)", opciones, index=default_a, key="audit_hist_a")
    with s2:
        snap_b = st.selectbox("Snapshot B (actual)", opciones, index=default_b, key="audit_hist_b")

    if snap_a == snap_b:
        st.warning("Selecciona snapshots diferentes para comparar.")
        return

    try:
        diff = compare_auditoria_snapshots(
            snapshot_a_path=snap_a,
            snapshot_b_path=snap_b,
            snapshot_name_a=Path(snap_a).name,
            snapshot_name_b=Path(snap_b).name,
            top_n=25,
        )
    except Exception as error:
        st.error(f"No se pudo comparar snapshots: {error}")
        return

    summary = diff.get("summary", {}) if isinstance(diff, dict) else {}
    ranking = summary.get("ranking", {}) if isinstance(summary, dict) else {}
    score = summary.get("score", {}) if isinstance(summary, dict) else {}

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("% mejora", f"{float(ranking.get('up_pct', 0.0)):.2f}%")
    k2.metric("% caída", f"{float(ranking.get('down_pct', 0.0)):.2f}%")
    k3.metric("% sin cambio", f"{float(ranking.get('same_pct', 0.0)):.2f}%")
    k4.metric("Δ score final promedio", f"{float(score.get('avg_delta_score_final', 0.0)):.4f}")

    comp_df = pd.DataFrame(
        [
            {"componente": "exacto", "delta": float(score.get("avg_delta_score_exacto", 0.0))},
            {"componente": "fuzzy", "delta": float(score.get("avg_delta_score_fuzzy", 0.0))},
            {"componente": "semantico", "delta": float(score.get("avg_delta_score_semantico", 0.0))},
            {"componente": "temporal", "delta": float(score.get("avg_delta_score_temporal", 0.0))},
            {"componente": "estructural", "delta": float(score.get("avg_delta_score_estructural", 0.0))},
            {"componente": "boosting", "delta": float(score.get("avg_delta_score_boosting", 0.0))},
        ]
    )
    st.vega_lite_chart(
        comp_df,
        {
            "mark": {"type": "bar", "color": "#1565C0"},
            "encoding": {
                "x": {"field": "componente", "type": "nominal", "sort": None},
                "y": {"field": "delta", "type": "quantitative"},
                "tooltip": [
                    {"field": "componente", "type": "nominal"},
                    {"field": "delta", "type": "quantitative"},
                ],
            },
            "title": "Delta promedio por componente (B - A)",
        },
        use_container_width=True,
    )

    docs = [x for x in diff.get("documents", []) if isinstance(x, dict)] if isinstance(diff, dict) else []
    common_df = pd.DataFrame([x for x in docs if x.get("status") == "common"])
    if not common_df.empty and {"delta_pos", "delta_score_final"}.issubset(common_df.columns):
        common_df["delta_pos"] = pd.to_numeric(common_df["delta_pos"], errors="coerce")
        common_df["delta_score_final"] = pd.to_numeric(common_df["delta_score_final"], errors="coerce")
        st.vega_lite_chart(
            common_df,
            {
                "mark": {"type": "point", "color": "#64B5F6", "filled": True, "size": 90},
                "encoding": {
                    "x": {"field": "delta_pos", "type": "quantitative"},
                    "y": {"field": "delta_score_final", "type": "quantitative"},
                    "tooltip": [
                        {"field": "ruta", "type": "nominal"},
                        {"field": "delta_pos", "type": "quantitative"},
                        {"field": "delta_score_final", "type": "quantitative"},
                    ],
                },
                "title": "Dispersión: delta_pos vs delta_score_final",
            },
            use_container_width=True,
        )

    st.caption("Top cambios de ranking")
    st.dataframe(pd.DataFrame(diff.get("top_rank_changes", [])), use_container_width=True, height=220)

    new_removed = [x for x in docs if str(x.get("status", "")) in {"new", "removed"}]
    if new_removed:
        st.caption("Documentos nuevos/removidos")
        st.dataframe(pd.DataFrame(new_removed), use_container_width=True, height=200)

    st.caption("Exportación de diff histórico")
    out_dir = docs_dir / "reportes"
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_json = out_dir / f"dropbox_search_audit_diff_{ts}.json"
    out_csv = out_dir / f"dropbox_search_audit_diff_{ts}.csv"
    out_txt = out_dir / f"dropbox_search_audit_diff_{ts}.txt"

    e1, e2, e3 = st.columns(3)
    with e1:
        if st.button("Exportar diff JSON", key=f"hist_diff_json_{ts}", use_container_width=True):
            try:
                p = export_auditoria_diff_json(diff, out_json)
                st.success(f"Diff JSON exportado: {p.name}")
            except Exception as error:
                st.error(f"No se pudo exportar diff JSON: {error}")
        if out_json.exists():
            st.download_button(
                "Descargar diff JSON",
                data=out_json.read_bytes(),
                file_name=out_json.name,
                mime="application/json",
                use_container_width=True,
                key=f"hist_diff_json_dl_{ts}",
            )
    with e2:
        if st.button("Exportar diff CSV", key=f"hist_diff_csv_{ts}", use_container_width=True):
            try:
                p = export_auditoria_diff_csv(diff, out_csv)
                st.success(f"Diff CSV exportado: {p.name}")
            except Exception as error:
                st.error(f"No se pudo exportar diff CSV: {error}")
        if out_csv.exists():
            st.download_button(
                "Descargar diff CSV",
                data=out_csv.read_bytes(),
                file_name=out_csv.name,
                mime="text/csv",
                use_container_width=True,
                key=f"hist_diff_csv_dl_{ts}",
            )
    with e3:
        if st.button("Exportar diff TXT", key=f"hist_diff_txt_{ts}", use_container_width=True):
            try:
                p = export_auditoria_diff_txt(diff, out_txt)
                st.success(f"Diff TXT exportado: {p.name}")
            except Exception as error:
                st.error(f"No se pudo exportar diff TXT: {error}")
        if out_txt.exists():
            st.download_button(
                "Descargar diff TXT",
                data=out_txt.read_bytes(),
                file_name=out_txt.name,
                mime="text/plain",
                use_container_width=True,
                key=f"hist_diff_txt_dl_{ts}",
            )


def render_document_viewer(state: StateManager, carpeta: Path) -> None:
    """Pantalla principal de vista previa documental."""
    archivos = listar_archivos_por_formato(str(carpeta))
    total = sum(len(v) for v in archivos.values())
    st.metric("Documentos detectados", f"{total:,}")

    c_main, c_right = st.columns([2.2, 1.3], gap="large")
    analisis_resultado: dict[str, object] | None = None
    tipo_analisis = ""

    with c_main:
        formato = st.selectbox("Formato", list(archivos.keys()), index=0)
        lista = archivos.get(formato, [])
        if not lista:
            st.warning(f"No hay archivos válidos en FACTURACION/{formato}.")
            return

        mapa = {str(Path(p).relative_to(carpeta)): Path(p) for p in lista}
        elegido_rel = st.selectbox(f"Archivo {formato}", list(mapa.keys()))
        path = mapa[elegido_rel]
        st.caption(f"Archivo seleccionado: {path}")

        if formato == "PDF":
            render_download_control(path)
            analisis_resultado = render_pdf_preview(
                path,
                state.get("cfg")["zoom_pdf"],
                state.get("cfg")["max_paginas_pdf"],
            )
            tipo_analisis = "pdf"
            register_action(state, "visualizacion_pdf", str(path))
        elif formato == "EXCEL":
            render_download_control(path)
            analisis_resultado, hoja = render_excel_preview(path)
            tipo_analisis = "excel"
            register_action(state, "visualizacion_excel", f"{path} | hoja={hoja}")
        elif formato == "JPG":
            render_download_control(path)
            render_image_preview(path)
            register_action(state, "visualizacion_imagen", str(path))
        elif formato in {"PYTHON", "POWERSHELL", "TEXTO"}:
            render_download_control(path)
            render_text_code_preview(path, formato)
            register_action(state, "visualizacion_texto_codigo", str(path))
        else:
            render_download_control(path)
            st.info("Vista previa de ZIP restringida. Archivo disponible para descarga controlada.")
            register_action(state, "visualizacion_zip", str(path))

    with c_right:
        st.subheader("Panel de análisis")
        if tipo_analisis == "pdf" and analisis_resultado is not None:
            render_pdf_analysis_panel(analisis_resultado)
        elif tipo_analisis == "excel" and analisis_resultado is not None:
            render_excel_analysis_panel(analisis_resultado)
        else:
            st.info("Selecciona un PDF o Excel para análisis automático profundo.")


def render_validation_page(state: StateManager) -> None:
    """Pantalla de validación RFC y folio fiscal."""
    st.subheader("Validación RFC y Folio Fiscal")
    col1, col2 = st.columns(2)
    with col1:
        rfc = st.text_input("RFC a validar", value="")
        if st.button("Validar RFC", use_container_width=True):
            resultado = validar_rfc(rfc)
            if resultado["valido"]:
                st.success(f"RFC válido: {resultado['rfc']}")
                st.write("**Desglose completo**")
                for d in resultado["detalles"]:
                    st.write(f"- {d}")
                for o in resultado["observaciones"]:
                    st.write(f"- {o}")
            else:
                st.error(f"RFC inválido: {resultado['rfc']}")
                st.write("**Motivo exacto**")
                for m in resultado["motivos"]:
                    st.write(f"- {m}")
                st.write("**Sugerencias de corrección**")
                for s in resultado["sugerencias"]:
                    st.write(f"- {s}")
            register_action(state, "validacion_rfc", json.dumps(resultado, ensure_ascii=False))

    with col2:
        folio = st.text_input("UUID/Folio fiscal", value="")
        if st.button("Validar Folio", use_container_width=True):
            valido, mensaje = validar_folio(folio)
            if valido:
                st.success(mensaje)
                register_action(state, "validacion_folio", f"valido:{folio}")
            else:
                st.error(mensaje)
                st.write("Ejemplo: 123e4567-e89b-12d3-a456-426614174000")
                register_action(state, "validacion_folio", f"invalido:{folio}")


def render_downloads_page(state: StateManager, carpeta: Path) -> None:
    """Pantalla de descargas controladas con filtros."""
    st.subheader("Descarga de metadatos y facturas")
    docs = indexar_documentos(str(carpeta))
    if not docs:
        st.warning("No se encontraron documentos descargables en la carpeta FACTURACION.")
        return

    df = pd.DataFrame(docs)
    min_date = pd.to_datetime(df["fecha_mod"]).min().date()
    max_date = pd.to_datetime(df["fecha_mod"]).max().date()

    f1, f2, f3 = st.columns(3)
    with f1:
        rango = st.date_input("Rango de fechas", value=(min_date, max_date))
    with f2:
        rfc_emisor = st.text_input("RFC emisor")
        rfc_receptor = st.text_input("RFC receptor")
    with f3:
        uuid = st.text_input("UUID")
        folio = st.text_input("Folio fiscal")

    g1, g2, g3 = st.columns(3)
    with g1:
        monto = st.text_input("Monto contiene")
    with g2:
        tipo = st.selectbox("Tipo comprobante", ["TODOS", "I", "E", "T", "N", "P", "OTRO"])
    with g3:
        ext = st.multiselect("Tipos de archivo", sorted(df["extension"].unique()), default=sorted(df["extension"].unique()))

    filtrado = aplicar_filtros(df, rango, rfc_emisor, rfc_receptor, uuid, folio, monto, tipo, ext)
    meta = resumen_previsualizacion(filtrado)

    st.write("### Previsualización antes de descargar")
    a1, a2, a3 = st.columns(3)
    a1.metric("Documentos", f"{meta['documentos']:,}")
    a2.metric("Tamaño estimado", f"{meta['tamano_kb']:,.2f} KB")
    a3.metric("Tipos", f"{meta['tipos']}")
    st.dataframe(filtrado, use_container_width=True, height=260)

    if filtrado.empty:
        st.info("No hay resultados para los filtros seleccionados.")
        return

    st.write("### Descarga individual")
    seleccionado = Path(st.selectbox("Documento", filtrado["path"].tolist()))
    render_download_control(seleccionado)
    st.success("Descarga preparada. Se ejecuta únicamente al presionar el botón.")
    register_action(state, "preparacion_descarga_individual", str(seleccionado))

    st.write("### Descarga masiva")
    paths = [Path(p) for p in filtrado["path"].tolist()]
    zip_bytes = construir_zip_memoria(paths)
    st.download_button(
        label="Descargar ZIP masivo",
        data=zip_bytes,
        file_name=f"facturacion_lote_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
        mime="application/zip",
        use_container_width=True,
    )
    st.info("La descarga masiva solo se inicia cuando presionas el botón.")
    register_action(state, "preparacion_descarga_masiva", f"documentos={len(paths)}")


def render_history_page(state: StateManager) -> None:
    """Pantalla de historial de acciones."""
    st.subheader("Historial de acciones")
    historial = state.get("historial", [])
    if not historial:
        st.info("Aún no hay acciones registradas.")
        return
    st.dataframe(pd.DataFrame(historial), use_container_width=True, height=420)


def render_settings_page(state: StateManager) -> None:
    """Pantalla de configuración de aplicación."""
    st.subheader("Configuración")
    cfg = state.get("cfg")
    c1, c2 = st.columns(2)
    with c1:
        idioma = st.selectbox("Idioma", ["Español", "English"], index=0 if cfg["idioma"] == "Español" else 1)
        analisis_profundo = st.checkbox("Análisis profundo", value=cfg["analisis_profundo"])
    with c2:
        zoom_pdf = st.slider("Zoom PDF", min_value=1.0, max_value=3.0, value=float(cfg["zoom_pdf"]), step=0.1)
        max_pag = st.slider("Máximo páginas análisis PDF", min_value=5, max_value=80, value=int(cfg["max_paginas_pdf"]), step=1)

    if st.button("Guardar configuración", use_container_width=True):
        state.set(
            "cfg",
            {
                "idioma": idioma,
                "analisis_profundo": analisis_profundo,
                "zoom_pdf": zoom_pdf,
                "max_paginas_pdf": max_pag,
            },
        )
        st.success("Configuración actualizada.")
        register_action(state, "configuracion", json.dumps(state.get("cfg"), ensure_ascii=False))


def render_dropbox_page(state: StateManager, carpeta: Path) -> None:
    """Pantalla de integración Dropbox IA con ejecución y exploración."""
    st.subheader("Integración Dropbox + Clasificación IA")
    st.caption("Lectura recursiva, clasificación, asignación a módulos y previsualización.")

    root = Path(__file__).resolve().parents[1]
    script = root / "integrar_dropbox.py"
    docs_dir = root / "docs"
    salida_json = docs_dir / "dropbox_asignacion_app.json"

    c1, c2 = st.columns([2, 1])
    with c1:
        ruta_objetivo = st.text_input("Ruta FACTURACION a procesar", value=str(carpeta))
    with c2:
        verbose = st.checkbox("Verbose", value=True)

    col_run, col_dash = st.columns(2)

    if col_run.button("Procesar Dropbox ahora", use_container_width=True):
        cmd = [sys.executable, str(script), "--ruta", ruta_objetivo, "--validate"]
        if verbose:
            cmd.append("--verbose")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            output = (result.stdout or "") + ("\n" + result.stderr if result.stderr else "")
            if result.returncode == 0:
                st.success("Procesamiento Dropbox completado.")
                register_action(state, "dropbox_sync", f"ok ruta={ruta_objetivo}")
            else:
                st.error("El procesamiento Dropbox terminó con errores.")
                register_action(state, "dropbox_sync", f"error ruta={ruta_objetivo}")
            st.text_area("Salida del proceso", value=output.strip(), height=220)
        except Exception as error:
            st.error(f"No fue posible ejecutar integrar_dropbox.py: {error}")

    if col_dash.button("Abrir dashboard local (opcional)", use_container_width=True):
        cmd = [sys.executable, str(script), "--ruta", ruta_objetivo, "--dashboard"]
        if verbose:
            cmd.append("--verbose")
        try:
            subprocess.Popen(cmd)
            st.info("Dashboard local lanzado en proceso separado.")
        except Exception as error:
            st.error(f"No se pudo abrir el dashboard local: {error}")

    if not salida_json.exists():
        st.info("No hay resultados aún. Ejecuta 'Procesar Dropbox ahora'.")
        return

    try:
        registros = json.loads(salida_json.read_text(encoding="utf-8"))
    except Exception as error:
        st.error(f"No se pudo leer {salida_json.name}: {error}")
        return

    if not isinstance(registros, list) or not registros:
        st.warning("El mapeo está vacío o no tiene formato válido.")
        return

    analytics_json_path = docs_dir / "dropbox_analytics.json"
    folder_tree_json_path = docs_dir / "dropbox_folder_tree.json"
    snapshot_dir = docs_dir / "versions" / "latest" / "dropbox" / "analytics"
    reportes_json_path = docs_dir / "dropbox_analytics_reportes.json"

    s1, s2, s3, s4 = st.columns(4)
    with s1:
        if analytics_json_path.exists():
            st.success("analytics.json cargado")
        else:
            st.warning("analytics.json ausente")
    with s2:
        if folder_tree_json_path.exists():
            st.success("folder_tree.json cargado")
        else:
            st.warning("folder_tree.json ausente")
    with s3:
        if snapshot_dir.exists():
            st.success("Snapshot detectado")
        else:
            st.warning("Snapshot no detectado")
    with s4:
        if reportes_json_path.exists():
            st.success("Reportes disponibles")
        else:
            st.warning("Reportes no disponibles")

    arbol_virtual_base = construir_arbol_virtual(registros)
    opciones_virtuales = opciones_filtros_virtuales(registros)
    df = pd.DataFrame(registros)
    metricas = calcular_metricas(registros)
    analitica_detallada = analizar_documentos(registros)
    resumen_analitico = construir_resumen_analitico(analitica_detallada)
    resumen_virtual = resumen_arbol(arbol_virtual_base)

    tipos = sorted(df.get("categoria", pd.Series(dtype=str)).dropna().astype(str).unique().tolist())
    carpetas = sorted(df.get("carpeta", pd.Series(dtype=str)).dropna().astype(str).unique().tolist())
    extensiones = sorted(df.get("extension", pd.Series(dtype=str)).dropna().astype(str).unique().tolist())
    etiquetas_disponibles = sorted(
        {
            str(tag).lower()
            for item in registros
            for tag in (item.get("etiquetas", []) if isinstance(item.get("etiquetas", []), list) else [])
            if str(tag).strip()
        }
    )

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total archivos", f"{metricas['total_archivos']:,}")
    m2.metric("Tipos", f"{len(tipos):,}")
    m3.metric("Carpetas", f"{len(carpetas):,}")
    m4.metric("Tamaño total", bytes_humanos(int(metricas["tamano_total_bytes"])))

    st.markdown("### Explorador virtual documental")
    fv1, fv2, fv3, fv4 = st.columns(4)
    with fv1:
        proveedor_sel = st.selectbox("Proveedor", ["TODOS", *opciones_virtuales["proveedores"]], key="dropbox_virtual_proveedor")
    with fv2:
        anio_sel = st.selectbox("Año", ["TODOS", *opciones_virtuales["anios"]], key="dropbox_virtual_anio")
    with fv3:
        hospital_sel = st.selectbox("Hospital", ["TODOS", *opciones_virtuales["hospitales"]], key="dropbox_virtual_hospital")
    with fv4:
        mes_sel = st.selectbox("Mes", ["TODOS", *opciones_virtuales["meses"]], key="dropbox_virtual_mes")

    registros_filtrados_virtuales = aplicar_filtros_virtuales(
        registros,
        proveedor=proveedor_sel,
        anio=anio_sel,
        hospital=hospital_sel,
        mes=mes_sel,
    )

    left_tree, right_tree = st.columns([1.1, 1.9], gap="large")
    with left_tree:
        st.caption("Árbol colapsable (PROVEEDOR / AÑO / HOSPITAL / MES)")
        arbol_filtrado = construir_arbol_virtual(registros_filtrados_virtuales)
        for proveedor, p_nodo in arbol_filtrado.get("children", {}).items():
            with st.expander(f"{proveedor} ({p_nodo.get('stats', {}).get('archivos', 0)})", expanded=False):
                for anio, y_nodo in p_nodo.get("children", {}).items():
                    with st.expander(f"{anio} ({y_nodo.get('stats', {}).get('archivos', 0)})", expanded=False):
                        for hospital, h_nodo in y_nodo.get("children", {}).items():
                            with st.expander(f"{hospital} ({h_nodo.get('stats', {}).get('archivos', 0)})", expanded=False):
                                for mes, m_nodo in h_nodo.get("children", {}).items():
                                    st.caption(f"{mes}: {m_nodo.get('stats', {}).get('archivos', 0)} archivos")
    with right_tree:
        st.caption("Archivos (orden carpeta→archivo)")
        if registros_filtrados_virtuales:
            tabla_virtual = pd.DataFrame(registros_filtrados_virtuales)
            tabla_virtual["breadcrumb"] = tabla_virtual.apply(lambda r: breadcrumbs_virtuales(r.to_dict()), axis=1)
            columnas = ["breadcrumb", "nombre_archivo", "categoria", "extension", "tamaño", "fecha_modificacion"]
            existentes = [c for c in columnas if c in tabla_virtual.columns]
            tabla_virtual = tabla_virtual[existentes]
            orden_sel = st.selectbox(
                "Ordenar archivos por",
                ["nombre", "fecha", "tamaño", "tipo"],
                index=0,
                key="dropbox_virtual_order",
            )
            sort_col = "nombre_archivo"
            if orden_sel == "fecha":
                sort_col = "fecha_modificacion"
            elif orden_sel == "tamaño":
                sort_col = "tamaño"
            elif orden_sel == "tipo":
                sort_col = "categoria"
            tabla_virtual = tabla_virtual.sort_values(by=["breadcrumb", sort_col], ascending=[True, True])
            st.dataframe(tabla_virtual, use_container_width=True, height=280)
        else:
            st.info("No hay archivos en el nodo virtual seleccionado.")

    st.markdown("### Analítica documental")
    a1, a2, a3, a4 = st.columns(4)
    a1.metric("PDF páginas", f"{int(resumen_analitico.get('pdf_paginas', 0)):,}")
    a2.metric("Excel hojas", f"{int(resumen_analitico.get('excel_hojas', 0)):,}")
    a3.metric("Imágenes logo probable", f"{int(resumen_analitico.get('imagenes_logo_probable', 0)):,}")
    a4.metric("Texto palabras", f"{int(resumen_analitico.get('texto_palabras', 0)):,}")

    d1, d2 = st.columns(2)
    with d1:
        st.caption("Top proveedores")
        st.bar_chart(pd.Series(resumen_virtual.get("proveedores_top", {})))
    with d2:
        st.caption("Serie temporal por mes")
        st.bar_chart(pd.Series(resumen_virtual.get("meses_top", {})))

    analitica_df = pd.DataFrame(registros_filtrados_virtuales)
    if not analitica_df.empty:
        p1, p2 = st.columns(2)
        with p1:
            st.caption("Conteo por tipo (pie)")
            tipo_counts = analitica_df["categoria"].astype(str).value_counts().reset_index()
            tipo_counts.columns = ["tipo", "count"]
            st.vega_lite_chart(
                tipo_counts,
                {
                    "mark": {"type": "arc", "innerRadius": 40},
                    "encoding": {
                        "theta": {"field": "count", "type": "quantitative"},
                        "color": {"field": "tipo", "type": "nominal"},
                        "tooltip": [{"field": "tipo", "type": "nominal"}, {"field": "count", "type": "quantitative"}],
                    },
                },
                use_container_width=True,
            )
        with p2:
            st.caption("Conteo por proveedor (pie)")
            proveedor_counts = analitica_df["proveedor_virtual"].astype(str).value_counts().reset_index()
            proveedor_counts.columns = ["proveedor", "count"]
            st.vega_lite_chart(
                proveedor_counts,
                {
                    "mark": {"type": "arc", "innerRadius": 40},
                    "encoding": {
                        "theta": {"field": "count", "type": "quantitative"},
                        "color": {"field": "proveedor", "type": "nominal"},
                        "tooltip": [{"field": "proveedor", "type": "nominal"}, {"field": "count", "type": "quantitative"}],
                    },
                },
                use_container_width=True,
            )

        z1, z2, z3, z4 = st.columns(4)
        z1.metric("Conteo hospitales", f"{analitica_df['hospital_virtual'].nunique():,}")
        z2.metric("Conteo meses", f"{analitica_df['mes_virtual'].nunique():,}")
        z3.metric("Conteo proveedores", f"{analitica_df['proveedor_virtual'].nunique():,}")
        z4.metric("Conteo tipos", f"{analitica_df['categoria'].nunique():,}")

        top1, top2 = st.columns(2)
        with top1:
            st.caption("Top 10 archivos más grandes")
            st.dataframe(
                analitica_df.sort_values(by="tamaño", ascending=False).head(10)[["nombre_archivo", "tamaño", "categoria", "fecha_modificacion"]],
                use_container_width=True,
                height=220,
            )
        with top2:
            st.caption("Top 10 archivos más recientes")
            st.dataframe(
                analitica_df.sort_values(by="fecha_modificacion", ascending=False).head(10)[["nombre_archivo", "fecha_modificacion", "categoria", "tamaño"]],
                use_container_width=True,
                height=220,
            )

    if st.button("Generar reporte analítico (PDF/Excel/ZIP/TXT)", use_container_width=True):
        reportes = generar_paquete_reportes(
            resumen=resumen_analitico,
            analitica_detallada=analitica_detallada,
            tree_summary=resumen_virtual,
            out_dir=docs_dir / "reportes",
        )
        st.success("Reportes analíticos generados correctamente.")
        st.json(reportes)

    st.markdown("### Menú inteligente de facturas Aspel")
    facturas_aspel = _find_pdf_invoices(registros_filtrados_virtuales)
    if facturas_aspel:
        df_facturas = pd.DataFrame(facturas_aspel)
        providers = sorted(df_facturas.get("proveedor_detectado", pd.Series(dtype=str)).astype(str).unique().tolist())
        provider_sel_menu = st.selectbox("Proveedor detectado", ["TODOS", *providers], index=0, key="aspel_provider_filter")
        if provider_sel_menu != "TODOS":
            df_facturas = df_facturas[df_facturas["proveedor_detectado"].astype(str) == provider_sel_menu]

        cols_factura = [c for c in ["nombre_archivo", "proveedor_detectado", "proveedor", "fecha", "total", "uuid"] if c in df_facturas.columns]
        if cols_factura:
            st.dataframe(df_facturas[cols_factura], use_container_width=True, height=180)

        if df_facturas.empty:
            st.info("No hay facturas para el proveedor seleccionado.")
        else:
            facturas_view = df_facturas.to_dict(orient="records")
            seleccion_label = [
                f"{row.get('nombre_archivo', '')} | UUID: {row.get('uuid', '') or 'N/A'}"
                for row in facturas_view
            ]
            selected_idx = st.selectbox(
                "Factura Aspel detectada",
                options=list(range(len(seleccion_label))),
                format_func=lambda i: seleccion_label[i],
                key="aspel_invoice_selector",
            )
            selected = facturas_view[int(selected_idx)]

            ccfdi1, ccfdi2, ccfdi3, ccfdi4 = st.columns(4)
            with ccfdi1:
                uuid_cfdi = st.text_input("UUID CFDI", value=str(selected.get("uuid", "")), key="aspel_uuid")
            with ccfdi2:
                rfc_emisor_cfdi = st.text_input("RFC emisor", value=str(selected.get("rfc_emisor", "")), key="aspel_rfc_emisor")
            with ccfdi3:
                rfc_receptor_cfdi = st.text_input("RFC receptor", value=str(selected.get("rfc_receptor", "")), key="aspel_rfc_receptor")
            with ccfdi4:
                total_cfdi = st.text_input("Total CFDI", value=str(selected.get("total", "")), key="aspel_total")

            if st.button("Validar Folio (SAT)", use_container_width=True, key="aspel_cfdi_sat_validate"):
                sat_result = _validate_cfdi_sat(
                    uuid=uuid_cfdi,
                    rfc_emisor=rfc_emisor_cfdi,
                    rfc_receptor=rfc_receptor_cfdi,
                    total=total_cfdi,
                )
                _render_cfdi_validation_result(sat_result)
    else:
        st.info("No se detectaron facturas Aspel PDF con metadatos suficientes en el conjunto filtrado.")

    st.markdown("### Renombrado automático de imágenes")
    if st.button("Renombrar imágenes ahora", use_container_width=True, key="dropbox_rename_jpg"):
        base_rename = Path(ruta_objetivo) if str(ruta_objetivo).strip() else carpeta
        try:
            renames = _rename_images_by_folder(base_rename)
            if renames:
                st.success(f"Renombrado completado. Archivos procesados: {len(renames)}")
                st.dataframe(pd.DataFrame(renames), use_container_width=True, height=220)
            else:
                st.info("No se encontraron imágenes JPG/JPEG para renombrar.")
        except Exception as error:
            st.error(f"No se pudo ejecutar renombrado automático: {error}")

    st.markdown("### Búsqueda avanzada")
    b1, b2, b3 = st.columns(3)
    with b1:
        query = st.text_input("Texto de búsqueda", value="", key="dropbox_search_query")
        tipo_sel = st.selectbox("Tipo", ["TODOS", *tipos], index=0, key="dropbox_tipo")
    with b2:
        ext_sel = st.selectbox("Extensión", ["TODOS", *extensiones], index=0, key="dropbox_ext")
        carpeta_sel = st.selectbox("Carpeta", ["TODOS", *carpetas], index=0, key="dropbox_carpeta")
    with b3:
        etiquetas_sel = st.multiselect("Etiquetas", etiquetas_disponibles, default=[])
        modo_label = st.radio(
            "Modo de búsqueda",
            ["Modo estricto (exacto + filtros)", "Modo flexible (híbrido avanzado)"],
            index=1,
            key="dropbox_modo_busqueda",
        )
        modo_busqueda = "estricta" if modo_label.startswith("Modo estricto") else "flexible"
        fuzzy = st.checkbox("Búsqueda difusa", value=True)
        por_contenido = st.checkbox("Búsqueda por contenido", value=True)
        semantico = st.checkbox("Búsqueda semántica (IA)", value=False)
        mostrar_auditoria = st.checkbox("Mostrar auditoría avanzada", value=False, key="dropbox_show_audit")
        activar_profiling = st.checkbox("Activar modo profiling", value=False, key="dropbox_enable_profiling")

    weights_busqueda = _default_boosting_weights()
    with st.expander("Ajustes de boosting contextual", expanded=False):
        w1, w2, w3 = st.columns(3)
        with w1:
            weights_busqueda["boost_proveedor"] = st.slider("boost_proveedor", 0.0, 3.0, 1.0, 0.1, key="boost_proveedor")
            weights_busqueda["boost_hospital"] = st.slider("boost_hospital", 0.0, 3.0, 1.0, 0.1, key="boost_hospital")
            weights_busqueda["boost_mes"] = st.slider("boost_mes", 0.0, 3.0, 1.0, 0.1, key="boost_mes")
        with w2:
            weights_busqueda["boost_anio"] = st.slider("boost_anio", 0.0, 3.0, 1.0, 0.1, key="boost_anio")
            weights_busqueda["boost_tipo"] = st.slider("boost_tipo", 0.0, 3.0, 1.0, 0.1, key="boost_tipo")
            weights_busqueda["boost_temporal"] = st.slider("boost_temporal", 0.0, 3.0, 1.0, 0.1, key="boost_temporal")
        with w3:
            weights_busqueda["score_exacto"] = st.slider("peso_exacto", 0.0, 3.0, 1.0, 0.1, key="score_exacto")
            weights_busqueda["score_fuzzy"] = st.slider("peso_fuzzy", 0.0, 3.0, 1.0, 0.1, key="score_fuzzy")
            weights_busqueda["score_semantico"] = st.slider("peso_semantico", 0.0, 3.0, 1.0, 0.1, key="score_semantico")
            weights_busqueda["score_tokens"] = st.slider("peso_tokens", 0.0, 3.0, 1.0, 0.1, key="score_tokens")
            weights_busqueda["score_temporal"] = st.slider("peso_temporal", 0.0, 3.0, 1.0, 0.1, key="score_temporal")
            weights_busqueda["score_estructural"] = st.slider("peso_estructural", 0.0, 3.0, 1.0, 0.1, key="score_estructural")
            weights_busqueda["score_contenido"] = st.slider("peso_contenido", 0.0, 3.0, 1.0, 0.1, key="score_contenido")

    filtros_activos = {
        "tipo": tipo_sel,
        "extension": ext_sel,
        "carpeta": carpeta_sel,
        "etiquetas": etiquetas_sel,
        "fuzzy": fuzzy,
        "contenido": por_contenido,
        "semantico": semantico,
        "proveedor": proveedor_sel,
        "anio": anio_sel,
        "hospital": hospital_sel,
        "mes": mes_sel,
    }

    criterios = (
        bool(query.strip())
        or tipo_sel != "TODOS"
        or ext_sel != "TODOS"
        or carpeta_sel != "TODOS"
        or bool(etiquetas_sel)
        or proveedor_sel != "TODOS"
        or anio_sel != "TODOS"
        or hospital_sel != "TODOS"
        or mes_sel != "TODOS"
    )
    engine = SearchEngine(registros_filtrados_virtuales)
    engine.indexar_documentos()

    start = time.perf_counter()
    if criterios:
        resultados_busqueda = engine.buscar_avanzado(
            query,
            filtros=filtros_activos,
            usar_nombre=True,
            usar_contenido=por_contenido,
            usar_semantico=semantico,
            modo=modo_busqueda,
            weights=weights_busqueda,
            auditoria=mostrar_auditoria,
            profiling=activar_profiling,
        )
    else:
        resultados_busqueda = [{
            "nombre": str(x.get("nombre_archivo", "")),
            "tipo": str(x.get("categoria", "")),
            "carpeta": str(x.get("carpeta", "")),
            "extension": str(x.get("extension", "")),
            "tamano": int(x.get("tamaño", 0) or 0),
            "fecha": str(x.get("fecha_modificacion", "")),
            "ruta": str(x.get("ruta_completa", "")),
            "relevancia": 1.0,
            "contenido_extraido": str(x.get("contenido_extraido", "")),
        } for x in registros_filtrados_virtuales]
    elapsed = time.perf_counter() - start

    resultados_df = pd.DataFrame(resultados_busqueda)
    if resultados_df.empty:
        st.info("Sin resultados para los filtros seleccionados.")
        return

    if "nombre" not in resultados_df.columns:
        resultados_df["nombre"] = resultados_df.get("nombre_archivo", "")
    if "tipo" not in resultados_df.columns:
        resultados_df["tipo"] = resultados_df.get("categoria", "")
    if "tamano" not in resultados_df.columns:
        resultados_df["tamano"] = resultados_df.get("tamaño", 0)
    if "fecha" not in resultados_df.columns:
        resultados_df["fecha"] = resultados_df.get("fecha_modificacion", "")
    if "ruta" not in resultados_df.columns:
        resultados_df["ruta"] = resultados_df.get("ruta_completa", "")
    if "relevancia" not in resultados_df.columns:
        resultados_df["relevancia"] = 1.0

    ruta_breadcrumb = {
        str(item.get("ruta_completa", "")): breadcrumbs_virtuales(item)
        for item in registros_filtrados_virtuales
    }
    resultados_df["breadcrumb"] = resultados_df["ruta"].astype(str).map(ruta_breadcrumb).fillna("")

    top_tipo = str(resultados_df["tipo"].astype(str).mode().iloc[0]) if not resultados_df["tipo"].empty else ""
    top_carpeta = str(resultados_df["carpeta"].astype(str).mode().iloc[0]) if not resultados_df["carpeta"].empty else ""
    stats_path = docs_dir / "dropbox_search_stats.json"
    hist: list[dict[str, object]] = []
    if stats_path.exists():
        try:
            hist = list(json.loads(stats_path.read_text(encoding="utf-8")).get("historial", []))
        except Exception:
            hist = []
    if criterios and query.strip():
        hist.append({"query": query.strip(), "tipo_top": top_tipo, "carpeta_top": top_carpeta})
        hist = hist[-500:]
        stats = construir_estadisticas_busqueda(hist)
        stats["historial"] = hist
        stats_path.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total resultados", f"{len(resultados_df):,}")
    k2.metric("Tiempo búsqueda", f"{elapsed * 1000:.1f} ms")
    k3.metric("Tipos encontrados", f"{resultados_df['tipo'].nunique():,}")
    k4.metric("Carpetas encontradas", f"{resultados_df['carpeta'].nunique():,}")

    g1, g2, g3 = st.columns(3)
    with g1:
        st.caption("Resultados por tipo")
        st.bar_chart(resultados_df["tipo"].value_counts())
    with g2:
        st.caption("Resultados por carpeta")
        st.bar_chart(resultados_df["carpeta"].value_counts())
    with g3:
        st.caption("Resultados por extensión")
        st.bar_chart(resultados_df["extension"].value_counts())

    if mostrar_auditoria:
        audit_log = engine.get_audit_log(limit=80)
        ultimo_audit = next((x for x in reversed(audit_log) if str(x.get("evento", "")) == "busqueda_auditoria"), {})
        weights_aplicados = dict(ultimo_audit.get("weights", {})) if isinstance(ultimo_audit, dict) else {}
        boost_aplicado = dict(ultimo_audit.get("boost_weights", {})) if isinstance(ultimo_audit, dict) else {}
        _render_search_audit_panel(
            engine=engine,
            resultados_df=resultados_df,
            audit_log=audit_log,
            weights_aplicados=weights_aplicados,
            boost_aplicado=boost_aplicado,
            out_dir=docs_dir / "reportes",
        )

    if activar_profiling:
        _render_search_performance_panel(engine=engine, out_dir=docs_dir / "reportes")

    _render_search_historical_panel(docs_dir)

    resultados_df = resultados_df.sort_values(by="relevancia", ascending=False)
    tabla = resultados_df[["breadcrumb", "nombre", "tipo", "carpeta", "extension", "tamano", "fecha", "relevancia", "ruta"]].copy()
    tabla.rename(
        columns={
            "breadcrumb": "Breadcrumb",
            "nombre": "Nombre",
            "tipo": "Tipo",
            "carpeta": "Carpeta",
            "extension": "Extensión",
            "tamano": "Tamaño",
            "fecha": "Fecha",
            "relevancia": "Relevancia",
            "ruta": "Previsualizar",
        },
        inplace=True,
    )
    st.dataframe(tabla, use_container_width=True, height=280)

    r1, r2 = st.columns(2)
    with r1:
        st.caption("Archivos más recientes")
        recientes_df = resultados_df.sort_values(by="fecha", ascending=False).head(10)
        if not recientes_df.empty:
            st.dataframe(recientes_df[["nombre", "fecha", "carpeta", "tipo"]], use_container_width=True, height=180)
    with r2:
        st.caption("Archivos más pesados")
        pesados_df = resultados_df.sort_values(by="tamano", ascending=False).head(10)
        if not pesados_df.empty:
            st.dataframe(pesados_df[["nombre", "tamano", "carpeta", "tipo"]], use_container_width=True, height=180)

    rutas = [str(x) for x in resultados_df["ruta"].astype(str).tolist() if str(x).strip()]
    if not rutas:
        st.info("No hay rutas disponibles para previsualización.")
        return

    cprev1, cprev2 = st.columns([3, 1])
    with cprev1:
        seleccionado_valor = st.selectbox("Archivo para vista previa", rutas, key="dropbox_resultado_previsualizar")
    with cprev2:
        previsualizar_click = st.button("Previsualizar", use_container_width=True)

    if not previsualizar_click:
        st.caption("Selecciona un archivo y presiona 'Previsualizar'.")
        return

    seleccionado = Path(seleccionado_valor)

    if not seleccionado.exists():
        st.warning("El archivo seleccionado ya no existe en disco.")
        return

    ext = seleccionado.suffix.lower()
    if ext in {".jpg", ".jpeg", ".png"}:
        z1, z2 = st.columns(2)
        with z1:
            zoom_img = st.slider("Zoom imagen", min_value=0.5, max_value=3.0, value=1.0, step=0.1)
        with z2:
            rotacion_img = st.selectbox("Rotación", options=[0, 90, 180, 270], index=0)
        try:
            mostrar_imagen_streamlit(seleccionado, zoom=float(zoom_img), rotacion=int(rotacion_img))
        except Exception as error:
            st.error(f"No se pudo previsualizar imagen: {error}")
    elif ext == ".pdf":
        render_pdf_preview(
            seleccionado,
            state.get("cfg")["zoom_pdf"],
            state.get("cfg")["max_paginas_pdf"],
        )
    elif ext in {".txt", ".md", ".py", ".ps1"}:
        formato = "TEXTO"
        if ext == ".py":
            formato = "PYTHON"
        elif ext == ".ps1":
            formato = "POWERSHELL"
        render_text_code_preview(seleccionado, formato)
    else:
        st.info("Vista previa no disponible para este tipo. Usa descarga controlada.")

    render_download_control(seleccionado)


def _is_safe_subpath(base: Path, candidate: Path) -> bool:
    try:
        base_resolved = base.resolve()
        candidate_resolved = candidate.resolve()
        candidate_resolved.relative_to(base_resolved)
        return True
    except Exception:
        return False


def _scan_explorer_files(base: Path) -> list[dict[str, object]]:
    allowed = {".pdf", ".xml", ".jpg", ".jpeg", ".png", ".txt", ".zip"}
    rows: list[dict[str, object]] = []
    for path in sorted(base.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in allowed:
            continue
        rel = path.relative_to(base)
        rows.append(
            {
                "nombre": path.name,
                "extension": path.suffix.lower(),
                "carpeta": rel.parent.as_posix() if rel.parent != Path(".") else "(raíz)",
                "ruta_relativa": rel.as_posix(),
                "tamaño_kb": round(path.stat().st_size / 1024, 2),
            }
        )
    return rows


def _scan_invoices_for_actions(base: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for pdf in sorted(base.rglob("*.pdf")):
        if not pdf.is_file() or not _is_safe_subpath(base, pdf):
            continue
        contenido = extraer_contenido_archivo(pdf)
        rows.append(
            {
                "nombre_archivo": pdf.name,
                "ruta_completa": str(pdf),
                "extension": ".pdf",
                "contenido_extraido": contenido,
                "proveedor_virtual": "",
            }
        )
    return rows


def _register_explorer_action(
    state: StateManager,
    usuario: str,
    rol: str,
    accion: str,
    ruta_afectada: str,
) -> None:
    payload = {
        "usuario": usuario,
        "rol": rol,
        "accion": accion,
        "ruta_afectada": ruta_afectada,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    }
    register_action(state, "dropbox_explorer_action", json.dumps(payload, ensure_ascii=False))


def render_dropbox_explorer(state: StateManager, carpeta: Path) -> None:
    st.markdown(
        """
        <style>
        .dropbox-explorer-title {color: #0D47A1; font-weight: 700;}
        .dropbox-explorer-accent {color: #1565C0;}
        .dropbox-explorer-soft {color: #1E88E5;}
        .dropbox-explorer-note {color: #42A5F5;}
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("<h3 class='dropbox-explorer-title'>Dropbox Explorer</h3>", unsafe_allow_html=True)
    st.caption("Visualización y operación segura del árbol FACTURACION con control administrativo.")

    base = Path(carpeta)
    if not base.exists() or not base.is_dir():
        st.error("La ruta FACTURACION no existe o no es válida.")
        return

    usuarios = {
        "daniel.andrade.martinez03@gmail.com": "Administrador",
        "auditor@empresa.com": "Auditor",
        "lectura@empresa.com": "Lectura",
    }

    if "dropbox_explorer_auth_ok" not in st.session_state:
        st.session_state.dropbox_explorer_auth_ok = False
    if "dropbox_explorer_auth_user" not in st.session_state:
        st.session_state.dropbox_explorer_auth_user = ""
    if "dropbox_explorer_auth_role" not in st.session_state:
        st.session_state.dropbox_explorer_auth_role = "Lectura"
    if "modo" not in st.session_state:
        st.session_state["modo"] = "admin"
    if "rol" not in st.session_state:
        st.session_state["rol"] = "Lectura"
    if "correo" not in st.session_state:
        st.session_state["correo"] = ""
    if "autenticado" not in st.session_state:
        st.session_state["autenticado"] = False
    if "dropbox_explorer_allow_alt_login" not in st.session_state:
        st.session_state.dropbox_explorer_allow_alt_login = False
    if "dropbox_explorer_login_mode" not in st.session_state:
        st.session_state.dropbox_explorer_login_mode = "admin"

    st.markdown("#### Autenticación")
    admin_email = "daniel.andrade.martinez03@gmail.com"
    admin_email_norm = admin_email.strip().lower()

    _load_env_for_dropbox_auth()
    admin_pass = os.getenv("DROPBOX_ADMIN_PASS", "").strip().strip('"').strip("'")
    auditor_pass = os.getenv("DROPBOX_AUDITOR_PASS", "").strip()
    readonly_pass = os.getenv("DROPBOX_READONLY_PASS", "").strip()
    print("DEBUG admin_pass:", repr(admin_pass))
    if not admin_pass:
        logging.warning("DROPBOX_ADMIN_PASS no está definida o está vacía")

    is_session_active = bool(st.session_state.get("dropbox_explorer_auth_ok", False))
    is_admin_active = (
        is_session_active
        and str(st.session_state.get("dropbox_explorer_auth_role", "")) == "Administrador"
        and str(st.session_state.get("dropbox_explorer_auth_user", "")).strip().lower() == admin_email_norm
    )

    if is_session_active:
        if st.button("Cerrar sesión", use_container_width=True, key="dropbox_explorer_logout_btn"):
            st.session_state.dropbox_explorer_auth_ok = False
            st.session_state.dropbox_explorer_auth_user = ""
            st.session_state.dropbox_explorer_auth_role = "Lectura"
            st.session_state["modo"] = "admin"
            st.session_state["rol"] = "Lectura"
            st.session_state["correo"] = ""
            st.session_state["autenticado"] = False
            st.session_state.dropbox_explorer_allow_alt_login = True
            st.session_state.dropbox_explorer_login_mode = "admin"
            st.rerun()

    show_other_user_btn = (
        not is_admin_active
        and not is_session_active
        and bool(st.session_state.get("dropbox_explorer_allow_alt_login", False))
        and st.session_state.get("dropbox_explorer_login_mode", "admin") == "admin"
    )
    if show_other_user_btn:
        if st.button("Ingresar como otro usuario", use_container_width=True, key="dropbox_explorer_other_user_btn"):
            st.session_state["modo"] = "otro"
            st.session_state.dropbox_explorer_login_mode = "other"
            st.rerun()

    use_other_user = (
        st.session_state.get("modo", "admin") == "otro"
        and
        bool(st.session_state.get("dropbox_explorer_allow_alt_login", False))
        and st.session_state.get("dropbox_explorer_login_mode", "admin") == "other"
        and not is_session_active
    )

    if not is_session_active and not use_other_user:
        correo = admin_email
        rol = "Administrador"
        st.markdown(f"Usuario: {admin_email} (Administrador)")
        password = st.text_input("Contraseña", type="password", key="dropbox_explorer_login_pass_admin")
        password = str(password).strip()
        login_click = st.button("Iniciar sesión", use_container_width=True, key="dropbox_explorer_login_btn_admin")

        if login_click:
            if rol == "Administrador" and password == admin_pass:
                st.session_state.dropbox_explorer_auth_ok = True
                st.session_state.dropbox_explorer_auth_user = admin_email
                st.session_state.dropbox_explorer_auth_role = "Administrador"
                st.session_state["modo"] = "admin"
                st.session_state["rol"] = "Administrador"
                st.session_state["correo"] = admin_email
                st.session_state["autenticado"] = True
                st.session_state.dropbox_explorer_allow_alt_login = False
                st.session_state.dropbox_explorer_login_mode = "admin"
            else:
                st.session_state.dropbox_explorer_auth_ok = False
                st.session_state.dropbox_explorer_auth_user = ""
                st.session_state.dropbox_explorer_auth_role = "Lectura"
                st.session_state["modo"] = "admin"
                st.session_state["rol"] = "Lectura"
                st.session_state["correo"] = ""
                st.session_state["autenticado"] = False

            print("DEBUG LOGIN:", correo, rol, password == admin_pass)
    elif not is_session_active:
        correo_input = st.text_input("Correo electrónico", key="dropbox_explorer_login_email")
        password = st.text_input("Contraseña", type="password", key="dropbox_explorer_login_pass")
        password = str(password).strip()
        login_click = st.button("Iniciar sesión", use_container_width=True, key="dropbox_explorer_login_btn")

        if login_click:
            correo = str(correo_input).strip().lower()
            if correo == admin_email_norm:
                st.session_state["modo"] = "admin"
                st.session_state.dropbox_explorer_login_mode = "admin"
                st.info("Correo administrador detectado. Continúa con el flujo automático de administrador.")
                st.rerun()

            rol = usuarios.get(correo, "")

            modo_edicion = False
            modo_auditor = False
            modo_lectura = False

            if rol == "Administrador" and correo == admin_email_norm and password == admin_pass:
                modo_edicion = True
            elif rol == "Auditor" and password == auditor_pass:
                modo_auditor = True
            elif rol == "Lectura" and password == readonly_pass:
                modo_lectura = True
            else:
                modo_lectura = False

            print("DEBUG LOGIN:", correo, rol, password == admin_pass)
            st.session_state.dropbox_explorer_auth_ok = modo_edicion or modo_auditor or modo_lectura
            st.session_state.dropbox_explorer_auth_user = correo if st.session_state.dropbox_explorer_auth_ok else ""
            st.session_state.dropbox_explorer_auth_role = (
                "Administrador"
                if modo_edicion
                else ("Auditor" if modo_auditor else ("Lectura" if modo_lectura else "Lectura"))
            )
            st.session_state["modo"] = "otro"
            st.session_state["rol"] = st.session_state.dropbox_explorer_auth_role
            st.session_state["correo"] = correo if st.session_state.dropbox_explorer_auth_ok else ""
            st.session_state["autenticado"] = bool(st.session_state.dropbox_explorer_auth_ok)

    auth_ok = bool(st.session_state.get("dropbox_explorer_auth_ok", False))
    current_user = str(st.session_state.get("dropbox_explorer_auth_user", "") or "")
    current_role = str(st.session_state.get("dropbox_explorer_auth_role", "Lectura") or "Lectura")
    current_user_norm = current_user.strip().lower()

    if auth_ok:
        st.success(f"Sesión activa: {current_user} ({current_role})")
    else:
        st.info("Modo lectura habilitado. Login inválido o no autenticado.")

    modo_edicion = auth_ok and current_role == "Administrador" and current_user_norm == admin_email_norm
    modo_auditor = auth_ok and current_role == "Auditor"
    modo_lectura = not modo_edicion and not modo_auditor

    can_edit = modo_edicion
    can_validate = modo_edicion or modo_auditor
    can_view_logs = modo_edicion or modo_auditor

    expected_dirs = [
        "FACTURACION",
        "Aspel",
        "Facturama",
        "Facture",
        "Contpaqi",
        "Imagenes",
        "Pendiente",
        "Otros",
    ]
    protected_roots = {"facturacion", "aspel", "facturama", "facture", "contpaqi", "imagenes", "pendiente", "otros", "."}

    st.markdown("#### Estructura real de carpetas")
    root_rows: list[dict[str, object]] = []
    for rel in expected_dirs:
        path = base if rel == "FACTURACION" else (base / rel)
        root_rows.append(
            {
                "carpeta": rel,
                "estado": "OK" if path.exists() and path.is_dir() else "FALTANTE",
                "ruta": str(path),
            }
        )
    st.dataframe(pd.DataFrame(root_rows), use_container_width=True, height=220)

    files_rows = _scan_explorer_files(base)
    df_files = pd.DataFrame(files_rows)
    st.markdown("#### Archivos detectados (PDF/XML/JPG/PNG/TXT/ZIP)")
    if df_files.empty:
        st.info("No se detectaron archivos del alcance del explorador.")
    else:
        st.dataframe(df_files, use_container_width=True, height=260)

        for folder, group in df_files.groupby("carpeta"):
            with st.expander(f"{folder} ({len(group)})", expanded=False):
                st.dataframe(group[["nombre", "extension", "tamaño_kb", "ruta_relativa"]], use_container_width=True, height=180)

    if not can_edit and not can_validate and not can_view_logs:
        return

    st.markdown("#### Acciones de edición")
    dirs = [p for p in sorted(base.rglob("*")) if p.is_dir() and _is_safe_subpath(base, p)]
    dir_options = [str(p.relative_to(base)).replace("\\", "/") for p in dirs if p != base]
    file_options = [str(p.relative_to(base)).replace("\\", "/") for p in sorted(base.rglob("*")) if p.is_file() and _is_safe_subpath(base, p)]

    if can_edit:
        a1, a2, a3 = st.columns(3)
        with a1:
            st.markdown("**Crear carpeta**")
            new_folder_rel = st.text_input("Nueva carpeta (relativa)", key="dropbox_explorer_new_folder")
            if st.button("Crear carpeta", use_container_width=True, key="dropbox_explorer_create_folder"):
                target = base / str(new_folder_rel).strip().replace("\\", "/")
                if not str(new_folder_rel).strip():
                    st.warning("Especifica una ruta de carpeta.")
                elif not _is_safe_subpath(base, target):
                    st.error("Ruta inválida fuera de FACTURACION.")
                else:
                    target.mkdir(parents=True, exist_ok=True)
                    _register_explorer_action(state, current_user, current_role, "crear_carpeta", str(target))
                    st.success(f"Carpeta creada: {target}")

        with a2:
            st.markdown("**Renombrar carpeta**")
            folder_sel = st.selectbox("Carpeta origen", ["", *dir_options], key="dropbox_explorer_rename_folder_sel")
            folder_new = st.text_input("Nuevo nombre carpeta", key="dropbox_explorer_rename_folder_name")
            if st.button("Renombrar carpeta", use_container_width=True, key="dropbox_explorer_rename_folder"):
                src = base / folder_sel
                if not folder_sel:
                    st.warning("Selecciona una carpeta.")
                elif not _is_safe_subpath(base, src) or not src.exists() or not src.is_dir():
                    st.error("Carpeta inválida.")
                elif src.resolve() == base.resolve() or (src.parent == base and src.name.lower() in protected_roots):
                    st.error("No se permite renombrar carpetas raíz protegidas.")
                elif not folder_new.strip():
                    st.warning("Indica el nuevo nombre.")
                else:
                    dst = src.parent / folder_new.strip()
                    if not _is_safe_subpath(base, dst):
                        st.error("Ruta destino inválida fuera de FACTURACION.")
                    elif dst.exists():
                        st.error("Ya existe una carpeta con ese nombre.")
                    else:
                        src.rename(dst)
                        _register_explorer_action(state, current_user, current_role, "renombrar_carpeta", f"{src} -> {dst}")
                        st.success("Carpeta renombrada correctamente.")

        with a3:
            st.markdown("**Eliminar archivo**")
            file_del_sel = st.selectbox("Archivo a eliminar", ["", *file_options], key="dropbox_explorer_delete_file_sel")
            confirm_del = st.checkbox("Confirmo eliminación", key="dropbox_explorer_delete_confirm")
            if st.button("Eliminar archivo", use_container_width=True, key="dropbox_explorer_delete_file"):
                src = base / file_del_sel
                if not file_del_sel:
                    st.warning("Selecciona un archivo.")
                elif not _is_safe_subpath(base, src) or not src.exists() or not src.is_file():
                    st.error("Archivo inválido.")
                elif not confirm_del:
                    st.warning("Confirma la eliminación para continuar.")
                else:
                    src.unlink()
                    _register_explorer_action(state, current_user, current_role, "eliminar_archivo", str(src))
                    st.success("Archivo eliminado correctamente.")

        b1, b2, b3 = st.columns(3)
        with b1:
            st.markdown("**Renombrar archivo**")
            file_rename_sel = st.selectbox("Archivo origen", ["", *file_options], key="dropbox_explorer_rename_file_sel")
            file_new_name = st.text_input("Nuevo nombre archivo", key="dropbox_explorer_rename_file_name")
            if st.button("Renombrar archivo", use_container_width=True, key="dropbox_explorer_rename_file"):
                src = base / file_rename_sel
                if not file_rename_sel:
                    st.warning("Selecciona un archivo.")
                elif not _is_safe_subpath(base, src) or not src.exists() or not src.is_file():
                    st.error("Archivo inválido.")
                elif not file_new_name.strip():
                    st.warning("Indica nuevo nombre.")
                else:
                    dst = src.parent / file_new_name.strip()
                    if not _is_safe_subpath(base, dst):
                        st.error("Ruta destino inválida fuera de FACTURACION.")
                    elif dst.exists():
                        st.error("Ya existe un archivo con ese nombre.")
                    else:
                        src.rename(dst)
                        _register_explorer_action(state, current_user, current_role, "renombrar_archivo", f"{src} -> {dst}")
                        st.success("Archivo renombrado correctamente.")

        with b2:
            st.markdown("**Mover archivo**")
            file_move_sel = st.selectbox("Archivo origen", ["", *file_options], key="dropbox_explorer_move_file_sel")
            move_dest = st.selectbox("Carpeta destino", ["", *dir_options], key="dropbox_explorer_move_dest")
            if st.button("Mover archivo", use_container_width=True, key="dropbox_explorer_move_file"):
                src = base / file_move_sel
                dst_dir = base / move_dest
                if not file_move_sel or not move_dest:
                    st.warning("Selecciona archivo y carpeta destino.")
                elif not _is_safe_subpath(base, src) or not src.exists() or not src.is_file():
                    st.error("Archivo origen inválido.")
                elif not _is_safe_subpath(base, dst_dir) or not dst_dir.exists() or not dst_dir.is_dir():
                    st.error("Carpeta destino inválida.")
                else:
                    dst = dst_dir / src.name
                    if dst.exists():
                        st.error("Ya existe un archivo con ese nombre en la carpeta destino.")
                    else:
                        shutil.move(str(src), str(dst))
                        _register_explorer_action(state, current_user, current_role, "mover_archivo", f"{src} -> {dst}")
                        st.success("Archivo movido correctamente.")

        with b3:
            st.markdown("**Subir archivos**")
            upload_dest = st.selectbox("Carpeta destino", ["", *dir_options], key="dropbox_explorer_upload_dest")
            uploaded = st.file_uploader(
                "Selecciona PDF/XML/JPG/PNG/TXT",
                type=["pdf", "xml", "jpg", "jpeg", "png", "txt"],
                accept_multiple_files=True,
                key="dropbox_explorer_uploader",
            )
            if st.button("Subir archivos", use_container_width=True, key="dropbox_explorer_upload_btn"):
                allowed_upload = {".pdf", ".xml", ".jpg", ".jpeg", ".png", ".txt"}
                forbidden_exec = {".exe", ".bat", ".sh", ".cmd", ".msi", ".ps1", ".com", ".scr"}
                dst_dir = base / upload_dest
                if not upload_dest:
                    st.warning("Selecciona carpeta destino.")
                elif not uploaded:
                    st.warning("Selecciona al menos un archivo.")
                elif not _is_safe_subpath(base, dst_dir) or not dst_dir.exists() or not dst_dir.is_dir():
                    st.error("Carpeta destino inválida.")
                else:
                    ok_count = 0
                    for f in uploaded:
                        ext = Path(f.name).suffix.lower()
                        if ext in forbidden_exec or ext not in allowed_upload:
                            st.warning(f"Archivo bloqueado por seguridad/extensión: {f.name}")
                            continue
                        target = dst_dir / Path(f.name).name
                        if not _is_safe_subpath(base, target):
                            st.warning(f"Ruta inválida omitida: {f.name}")
                            continue
                        target.write_bytes(f.getbuffer())
                        ok_count += 1
                    _register_explorer_action(state, current_user, current_role, "subir_archivos", f"subidos={ok_count} destino={dst_dir}")
                    st.success(f"Carga finalizada. Archivos subidos: {ok_count}")

        st.markdown("#### Acciones analíticas y de mantenimiento")
        c1, c2, c3, c4 = st.columns(4)

        with c1:
            if st.button("Ejecutar renombrado JPG", use_container_width=True, key="dropbox_explorer_rename_jpg"):
                renames = _rename_images_by_folder(base)
                _register_explorer_action(state, current_user, current_role, "renombrado_jpg", f"movimientos={len(renames)}")
                st.dataframe(pd.DataFrame(renames), use_container_width=True, height=180)

        with c2:
            if st.button("Clasificación por proveedor", use_container_width=True, key="dropbox_explorer_provider"):
                invoices = _scan_invoices_for_actions(base)
                classified: list[dict[str, object]] = []
                for row in invoices:
                    prov = classify_invoice_provider(
                        text=str(row.get("contenido_extraido", "")),
                        file_name=str(row.get("nombre_archivo", "")),
                    )
                    classified.append({"ruta": str(row.get("ruta_completa", "")), "proveedor_detectado": prov})
                moves = move_invoices_to_provider_folders(base, classified)
                _register_explorer_action(state, current_user, current_role, "clasificacion_proveedor", f"clasificados={len(classified)} movidos={len(moves)}")
                st.success(f"Clasificación por proveedor ejecutada. Movidos: {len(moves)}")
                if moves:
                    st.dataframe(pd.DataFrame(moves), use_container_width=True, height=180)

        with c3:
            if st.button("Clasificación por receptor", use_container_width=True, key="dropbox_explorer_receptor"):
                invoices = _scan_invoices_for_actions(base)
                rows = build_invoices_dataset(invoices)
                summary = summarize_by_receptor(rows)
                _register_explorer_action(state, current_user, current_role, "clasificacion_receptor", f"filas={len(rows)}")
                st.json(summary)

        with c4:
            if st.button("Validación estructural Dropbox", use_container_width=True, key="dropbox_explorer_validate"):
                validation = validate_dropbox_structure(base)
                _register_explorer_action(state, current_user, current_role, "validacion_estructural", str(base))
                if validation.get("valid"):
                    st.success("Estructura Dropbox válida.")
                else:
                    st.warning("Se detectaron carpetas faltantes en estructura Dropbox.")
                st.json(validation)

    elif can_validate:
        st.markdown("#### Acciones permitidas para Auditor")
        if st.button("Validación estructural Dropbox", use_container_width=True, key="dropbox_explorer_validate_auditor"):
            validation = validate_dropbox_structure(base)
            _register_explorer_action(state, current_user, current_role, "validacion_estructural", str(base))
            if validation.get("valid"):
                st.success("Estructura Dropbox válida.")
            else:
                st.warning("Se detectaron carpetas faltantes en estructura Dropbox.")
            st.json(validation)

    if can_view_logs:
        st.markdown("#### Log interno de acciones")
        logs = state.get("logs", [])
        if logs:
            st.dataframe(pd.DataFrame(logs).tail(50), use_container_width=True, height=220)
        else:
            st.caption("Sin acciones registradas en la sesión actual.")

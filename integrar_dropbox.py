from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import date
import time
from pathlib import Path
import shutil

from dropbox_integration.ai_classifier import enriquecer_con_ia
from dropbox_integration.analytics_engine import analizar_documentos, construir_resumen_analitico
from dropbox_integration.asignador_modulos import asignar_modulos_app, exportar_asignacion
from dropbox_integration.clasificador_documentos import clasificar_documentos, exportar_mapeo
from dropbox_integration.dashboard_documentos import DashboardDocumentos, cargar_search_stats
from dropbox_integration.dropbox_structure import (
    ensure_dropbox_structure,
    move_invoices_to_provider_folders,
    normalize_images_to_pending,
    validate_dropbox_structure,
)
from dropbox_integration.folder_tree import construir_arbol_virtual, resumen_arbol
from dropbox_integration.invoice_receptor_analytics import build_invoices_dataset, summarize_by_receptor
from dropbox_integration.lector_dropbox import detectar_ruta_dropbox, leer_dropbox_recursivo
from dropbox_integration.report_generator import exportar_json, generar_paquete_reportes
from dropbox_integration.search_engine import SearchEngine
from dropbox_integration.tagging_engine import asignar_etiquetas_automaticas


def log(msg: str, verbose: bool = True) -> None:
    if verbose:
        print(f"[DROPBOX] {msg}")


def _actualizar_markdown_dropbox(registros: list[dict[str, object]], path: Path) -> None:
    total = len(registros)
    por_tipo = Counter(str(r.get("categoria", "Sin clasificar")) for r in registros)
    por_carpeta = Counter(str(r.get("carpeta", "")) for r in registros)

    lines = [
        "# Importación Dropbox",
        "",
        "Este archivo resume la importación recursiva de FACTURACION.",
        "",
        f"- Total de archivos: **{total}**",
        f"- Fecha de ejecución: **{date.today().isoformat()}**",
        "",
        "## Conteo por tipo",
    ]
    lines.extend([f"- {k}: {v}" for k, v in por_tipo.items()])
    lines.extend(["", "## Conteo por carpeta"])
    lines.extend([f"- {k}: {v}" for k, v in por_carpeta.items()])
    lines.extend(
        [
            "",
            "## Archivos de salida",
            "- docs/dropbox_mapeo_documentos.json",
            "- docs/dropbox_mapeo_documentos.md",
            "- docs/dropbox_asignacion_app.json",
        ]
    )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _actualizar_markdown_busqueda(path: Path) -> None:
    contenido = """# Búsqueda Avanzada Dropbox IA

Sistema documental avanzado con indexación, filtros, fuzzy search, búsqueda por contenido y búsqueda semántica TF‑IDF.

## Capacidades

- Búsqueda por nombre (exacta, parcial y difusa con `rapidfuzz`).
- Filtros por extensión, carpeta, tipo documental y etiquetas.
- Búsqueda por contenido en `PDF`, `TXT`, `MD`, `DOCX`.
- Ranking por score de relevancia y combinación de resultados.
- Búsqueda semántica local con `scikit-learn` (`TF-IDF` + coseno).
- Métricas de búsqueda en Streamlit y estadísticas en dashboard.

## Módulos principales

- `dropbox_integration/content_extractor.py`
- `dropbox_integration/search_engine.py`
- `dropbox_integration/lector_dropbox.py`
- `dropbox_integration/ai_classifier.py`
- `ui/layout.py` (pantalla `Dropbox IA`)
- `dropbox_integration/dashboard_documentos.py`

## Pruebas automatizadas

Ubicación: `tests/search/`

- `test_content_extractor.py`
- `test_search_engine_basico.py`
- `test_search_engine_contenido.py`
- `test_search_engine_semantico.py`
- `test_integracion_dropbox.py`
- `test_streamlit_dummy.py`

## Artefactos generados

- `docs/dropbox_search_stats.json`
- `docs/markdown/DROPBOX_SEARCH.md`
- `docs/versions/latest/dropbox/search/dropbox_search_stats.json`
- `docs/versions/latest/dropbox/search/DROPBOX_SEARCH.md`
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(contenido, encoding="utf-8")


def _actualizar_markdown_analytics(path: Path) -> None:
    contenido = """# Analítica Documental Dropbox IA

Sistema analítico de documentos con clasificación técnica por tipo, árbol virtual reconstruido y reportes automáticos.

## Capacidades

- Métricas por tipo de archivo: `PDF`, `EXCEL`, `IMAGEN`, `TEXTO`, `ZIP`.
- Árbol virtual: `PROVEEDOR → AÑO → HOSPITAL → MES → ARCHIVOS`.
- Filtros virtuales en Streamlit por proveedor, año, hospital y mes.
- Reportes automáticos en `PDF`, `Excel`, `TXT`, `ZIP`.
- Snapshot analítico en `docs/versions/latest/dropbox/analytics/`.

## Módulos

- `dropbox_integration/analytics_engine.py`
- `dropbox_integration/folder_tree.py`
- `dropbox_integration/report_generator.py`
- `ui/layout.py` (explorador analítico y árbol virtual)

## Artefactos

- `docs/dropbox_analytics.json`
- `docs/dropbox_folder_tree.json`
- `docs/dropbox_analytics_summary.json`
- `docs/dropbox_file_metrics.json`
- `docs/dropbox_type_metrics.json`
- `docs/dropbox_hospital_metrics.json`
- `docs/dropbox_month_metrics.json`
- `docs/dropbox_analytics_reportes.json`

## Flags del pipeline

- `--audit-search`: activa la auditoría de búsqueda y exporta `*_audit.json` / `*_audit.csv`.
- Comportamiento por defecto: auditoría **desactivada**; se ejecuta solo con `--audit-search`.
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(contenido, encoding="utf-8")


def _actualizar_index_documentacion(index_path: Path) -> None:
    if not index_path.exists():
        return
    content = index_path.read_text(encoding="utf-8")
    bloques = {
        "Documentos importados desde Dropbox": "## 🗃️ 9. Documentos importados desde Dropbox\n\n- Mapeo: [dropbox_mapeo_documentos.json](dropbox_mapeo_documentos.json)\n- Resumen: [dropbox_mapeo_documentos.md](dropbox_mapeo_documentos.md)\n- Asignación app: [dropbox_asignacion_app.json](dropbox_asignacion_app.json)\n- Guía markdown: [markdown/DROPBOX_IMPORT.md](markdown/DROPBOX_IMPORT.md)\n",
        "Dashboard visual": "## 🧭 10. Dashboard visual\n\n- Módulo: `dropbox_integration/dashboard_documentos.py`\n- Permite filtros por tipo/carpeta y apertura de visores.\n",
        "Clasificador IA": "## 🤖 11. Clasificador IA\n\n- Módulo: `dropbox_integration/ai_classifier.py`\n- Sugiere categoría, etiquetas y módulo destino.\n",
        "Visor PDF": "## 📄 12. Visor PDF\n\n- Módulo: `dropbox_integration/pdf_viewer.py`\n- Navegación por página, zoom y exportación de página como imagen.\n",
        "Etiquetas inteligentes": "## 🏷️ 13. Etiquetas inteligentes\n\n- Módulo: `dropbox_integration/tagging_engine.py`\n- Etiquetado automático + edición manual de etiquetas.\n",
        "Búsqueda avanzada Dropbox IA": "## 🔎 14. Búsqueda avanzada Dropbox IA\n\n- Motor: `dropbox_integration/search_engine.py`\n- Extracción de contenido: `dropbox_integration/content_extractor.py`\n- Guía: [markdown/DROPBOX_SEARCH.md](markdown/DROPBOX_SEARCH.md)\n- Estadísticas: [dropbox_search_stats.json](dropbox_search_stats.json)\n",
        "Analítica documental Dropbox IA": "## 📊 15. Analítica documental Dropbox IA\n\n- Motor analítico: `dropbox_integration/analytics_engine.py`\n- Árbol virtual: `dropbox_integration/folder_tree.py`\n- Reportes: `dropbox_integration/report_generator.py`\n- Guía: [markdown/DROPBOX_ANALYTICS.md](markdown/DROPBOX_ANALYTICS.md)\n- Artefactos: [dropbox_analytics.json](dropbox_analytics.json), [dropbox_folder_tree.json](dropbox_folder_tree.json)\n",
        "Auditoría de búsqueda generada": "## 🧪 16. Auditoría de búsqueda generada\n\n- Snapshot: `docs/versions/latest/dropbox/analytics/dropbox_search_audit_snapshot.json`\n- Snapshot CSV: `docs/versions/latest/dropbox/analytics/dropbox_search_audit_snapshot.csv`\n- Reportes incluyen `*_audit.json` y `*_audit.csv` en ZIP/TXT/Excel cuando existe auditoría.\n",
    }

    changed = False
    for key, bloque in bloques.items():
        if key not in content:
            content += "\n\n" + bloque
            changed = True

    if changed:
        index_path.write_text(content, encoding="utf-8")


def _actualizar_changelog(
    changelog_path: Path,
    total: int,
    dry_run: bool,
    audit_info: dict[str, object] | None = None,
) -> None:
    if dry_run:
        return

    entry = (
        f"\n\n## [dropbox-sync-{date.today().isoformat()}] — {date.today().isoformat()}\n"
        "### Added\n"
        "- Integración de lectura recursiva Dropbox (FACTURACION/EXCEL,JPG,PDF,POWERSHELL,PYTHON,TEXTO,ZIPPED).\n"
        "- Generación de mapeo JSON/Markdown y asignación a módulos.\n"
        "- Soporte para flag --audit-search (control de auditoría de búsqueda).\n"
        "\n### Changed\n"
        f"- Registros procesados en última ejecución: {total}.\n"
        + (
            f"- Auditoría de búsqueda generada: json={audit_info.get('snapshot_json', '')}, "
            f"csv={audit_info.get('snapshot_csv', '')}, filas={audit_info.get('result_rows', 0)}.\n"
            if isinstance(audit_info, dict) and audit_info.get("enabled")
            else ""
        )
        +
        "\n### Fixed\n"
        "- Cobertura de carpetas/subcarpetas para lectura recursiva documental.\n"
        "\n### Removed\n"
        "- N/A\n"
    )

    if changelog_path.exists():
        changelog_path.write_text(changelog_path.read_text(encoding="utf-8") + entry, encoding="utf-8")
    else:
        changelog_path.write_text("# Changelog de Documentación\n" + entry, encoding="utf-8")


def _copiar_a_version_activa(docs_dir: Path, dry_run: bool) -> None:
    latest = docs_dir / "versions" / "latest" / "dropbox"
    latest_search = latest / "search"
    latest_analytics = latest / "analytics"
    latest.mkdir(parents=True, exist_ok=True)
    latest_search.mkdir(parents=True, exist_ok=True)
    latest_analytics.mkdir(parents=True, exist_ok=True)
    archivos = [
        docs_dir / "dropbox_mapeo_documentos.json",
        docs_dir / "dropbox_mapeo_documentos.md",
        docs_dir / "dropbox_asignacion_app.json",
        docs_dir / "markdown" / "DROPBOX_IMPORT.md",
        docs_dir / "markdown" / "DROPBOX_SEARCH.md",
        docs_dir / "markdown" / "DROPBOX_ANALYTICS.md",
        docs_dir / "dropbox_search_stats.json",
        docs_dir / "dropbox_analytics.json",
        docs_dir / "dropbox_analytics_summary.json",
        docs_dir / "dropbox_folder_tree.json",
        docs_dir / "dropbox_file_metrics.json",
        docs_dir / "dropbox_type_metrics.json",
        docs_dir / "dropbox_hospital_metrics.json",
        docs_dir / "dropbox_month_metrics.json",
        docs_dir / "dropbox_invoices_by_receptor.json",
        docs_dir / "dropbox_analytics_reportes.json",
    ]
    for archivo in archivos:
        if archivo.exists() and not dry_run:
            shutil.copy2(archivo, latest / archivo.name)

    search_archivos = [
        docs_dir / "markdown" / "DROPBOX_SEARCH.md",
        docs_dir / "dropbox_search_stats.json",
    ]
    for archivo in search_archivos:
        if archivo.exists() and not dry_run:
            shutil.copy2(archivo, latest_search / archivo.name)

    analytics_archivos = [
        docs_dir / "markdown" / "DROPBOX_ANALYTICS.md",
        docs_dir / "dropbox_analytics.json",
        docs_dir / "dropbox_analytics_summary.json",
        docs_dir / "dropbox_folder_tree.json",
        docs_dir / "dropbox_file_metrics.json",
        docs_dir / "dropbox_type_metrics.json",
        docs_dir / "dropbox_hospital_metrics.json",
        docs_dir / "dropbox_month_metrics.json",
        docs_dir / "dropbox_invoices_by_receptor.json",
        docs_dir / "dropbox_analytics_reportes.json",
    ]
    for archivo in analytics_archivos:
        if archivo.exists() and not dry_run:
            shutil.copy2(archivo, latest_analytics / archivo.name)

    reportes_dir = docs_dir / "reportes"
    if reportes_dir.exists() and not dry_run:
        for archivo in reportes_dir.glob("dropbox_analytics_*.*"):
            shutil.copy2(archivo, latest_analytics / archivo.name)
        for archivo in reportes_dir.glob("dropbox_search_audit*.*"):
            shutil.copy2(archivo, latest_analytics / archivo.name)
        for archivo in reportes_dir.glob("dropbox_search_performance*.*"):
            shutil.copy2(archivo, latest_analytics / archivo.name)


def _queries_auditoria_canonicas() -> list[str]:
    """Retorna consultas canónicas para auditoría representativa del ranking."""
    return ["factura", "hospital", "proveedor", ""]


def _ejecutar_auditoria_busqueda(
    registros: list[dict[str, object]],
    snapshot_dir: Path,
    reportes_dir: Path,
    verbose: bool,
    profiling: bool = False,
) -> dict[str, object]:
    """Ejecuta auditoría de búsqueda, exporta JSON/CSV y retorna metadata útil para reportes/changelog."""
    audit_info: dict[str, object] = {
        "enabled": False,
        "snapshot_json": "",
        "snapshot_csv": "",
        "snapshot_performance_json": "",
        "snapshot_performance_csv": "",
        "report_json": "",
        "report_csv": "",
        "report_performance_json": "",
        "report_performance_csv": "",
        "result_rows": 0,
        "resultados_mejor_query": 0,
        "mejor_query": "",
        "auditoria_data": {},
    }
    if not registros:
        return audit_info

    try:
        log("Inicio auditoría de búsqueda en pipeline", verbose=verbose)
        engine = SearchEngine(registros)
        engine.indexar_documentos()

        filtros = {
            "tipo": "TODOS",
            "extension": "TODOS",
            "carpeta": "TODOS",
            "etiquetas": [],
            "fuzzy": True,
        }

        mejor_query = ""
        mejor_count = -1
        for query in _queries_auditoria_canonicas():
            resultados = engine.buscar_avanzado(
                query,
                filtros=filtros,
                usar_nombre=True,
                usar_contenido=True,
                usar_semantico=True,
                modo="flexible",
                auditoria=True,
                profiling=profiling,
            )
            if len(resultados) > mejor_count:
                mejor_count = len(resultados)
                mejor_query = query

        _ = engine.buscar_avanzado(
            mejor_query,
            filtros=filtros,
            usar_nombre=True,
            usar_contenido=True,
            usar_semantico=True,
            modo="flexible",
            auditoria=True,
            profiling=profiling,
        )

        snapshot_dir.mkdir(parents=True, exist_ok=True)
        reportes_dir.mkdir(parents=True, exist_ok=True)

        snapshot_json = engine.export_auditoria_json(str(snapshot_dir / "dropbox_search_audit_snapshot.json"))
        snapshot_csv = engine.export_auditoria_csv(str(snapshot_dir / "dropbox_search_audit_snapshot.csv"))
        report_json = engine.export_auditoria_json(str(reportes_dir / "dropbox_search_audit.json"))
        report_csv = engine.export_auditoria_csv(str(reportes_dir / "dropbox_search_audit.csv"))

        snapshot_perf_json = Path()
        snapshot_perf_csv = Path()
        report_perf_json = Path()
        report_perf_csv = Path()
        if profiling:
            snapshot_perf_json = engine.export_performance_json(str(snapshot_dir / "dropbox_search_performance_snapshot.json"))
            snapshot_perf_csv = engine.export_performance_csv(str(snapshot_dir / "dropbox_search_performance_snapshot.csv"))
            report_perf_json = engine.export_performance_json(str(reportes_dir / "dropbox_search_performance.json"))
            report_perf_csv = engine.export_performance_csv(str(reportes_dir / "dropbox_search_performance.csv"))

        auditoria_data = json.loads(snapshot_json.read_text(encoding="utf-8"))
        result_rows = int(auditoria_data.get("metadata", {}).get("result_rows", 0))
        size_json = int(snapshot_json.stat().st_size) if snapshot_json.exists() else 0
        size_csv = int(snapshot_csv.stat().st_size) if snapshot_csv.exists() else 0

        log(
            (
                "Fin auditoría de búsqueda | "
                f"query='{mejor_query}' | rows={result_rows} | "
                f"json={snapshot_json} ({size_json} bytes) | "
                f"csv={snapshot_csv} ({size_csv} bytes)"
            ),
            verbose=verbose,
        )

        audit_info.update(
            {
                "enabled": True,
                "snapshot_json": str(snapshot_json),
                "snapshot_csv": str(snapshot_csv),
                "snapshot_performance_json": str(snapshot_perf_json) if profiling else "",
                "snapshot_performance_csv": str(snapshot_perf_csv) if profiling else "",
                "report_json": str(report_json),
                "report_csv": str(report_csv),
                "report_performance_json": str(report_perf_json) if profiling else "",
                "report_performance_csv": str(report_perf_csv) if profiling else "",
                "result_rows": result_rows,
                "resultados_mejor_query": int(mejor_count),
                "mejor_query": mejor_query,
                "auditoria_data": auditoria_data,
            }
        )
    except Exception as error:
        log(f"Auditoría de búsqueda falló: {error}", verbose=True)

    return audit_info


def _validate_outputs(docs_dir: Path) -> tuple[bool, list[str]]:
    requeridos = [
        docs_dir / "dropbox_mapeo_documentos.json",
        docs_dir / "dropbox_mapeo_documentos.md",
        docs_dir / "dropbox_asignacion_app.json",
        docs_dir / "markdown" / "DROPBOX_IMPORT.md",
        docs_dir / "markdown" / "DROPBOX_SEARCH.md",
        docs_dir / "markdown" / "DROPBOX_ANALYTICS.md",
        docs_dir / "dropbox_search_stats.json",
        docs_dir / "dropbox_analytics.json",
        docs_dir / "dropbox_analytics_summary.json",
        docs_dir / "dropbox_folder_tree.json",
        docs_dir / "dropbox_file_metrics.json",
        docs_dir / "dropbox_type_metrics.json",
        docs_dir / "dropbox_hospital_metrics.json",
        docs_dir / "dropbox_month_metrics.json",
        docs_dir / "dropbox_analytics_reportes.json",
    ]
    faltantes = [str(p) for p in requeridos if not p.exists()]
    return len(faltantes) == 0, faltantes


def _generar_metricas_adicionales(enriquecidos: list[dict[str, object]], analitica_detallada: list[dict[str, object]]) -> dict[str, object]:
    file_metrics = []
    type_counter: Counter[str] = Counter()
    type_bytes: Counter[str] = Counter()
    hospital_counter: Counter[str] = Counter()
    month_counter: Counter[str] = Counter()

    ruta_to_virtual = {
        str(item.get("ruta_completa", "")): {
            "proveedor": str(item.get("proveedor_virtual", "SIN_PROVEEDOR")),
            "hospital": str(item.get("hospital_virtual", "SIN_HOSPITAL")),
            "mes": str(item.get("mes_virtual", "SIN_MES")),
            "anio": str(item.get("anio_virtual", "SIN_AÑO")),
        }
        for item in enriquecidos
    }

    for metrica in analitica_detallada:
        ruta = str(metrica.get("ruta", ""))
        tipo = str(metrica.get("tipo", "OTRO"))
        tamano = int(metrica.get("tamano_bytes", 0) or 0)
        virtual = ruta_to_virtual.get(ruta, {"proveedor": "SIN_PROVEEDOR", "hospital": "SIN_HOSPITAL", "mes": "SIN_MES", "anio": "SIN_AÑO"})

        file_metrics.append(
            {
                "ruta": ruta,
                "nombre": str(metrica.get("nombre", "")),
                "tipo": tipo,
                "extension": str(metrica.get("extension", "")),
                "tamano_bytes": tamano,
                "fecha_modificacion": str(metrica.get("fecha_modificacion", "")),
                "proveedor": virtual["proveedor"],
                "anio": virtual["anio"],
                "hospital": virtual["hospital"],
                "mes": virtual["mes"],
            }
        )

        type_counter[tipo] += 1
        type_bytes[tipo] += tamano
        hospital_counter[str(virtual["hospital"])] += 1
        month_counter[str(virtual["mes"])] += 1

    type_metrics = [
        {"tipo": tipo, "archivos": count, "tamano_bytes": int(type_bytes.get(tipo, 0))}
        for tipo, count in type_counter.most_common()
    ]
    hospital_metrics = [{"hospital": hospital, "archivos": count} for hospital, count in hospital_counter.most_common()]
    month_metrics = [{"mes": mes, "archivos": count} for mes, count in month_counter.most_common()]

    return {
        "file_metrics": file_metrics,
        "type_metrics": type_metrics,
        "hospital_metrics": hospital_metrics,
        "month_metrics": month_metrics,
    }


def _comparar_hashes(prev: list[dict[str, object]], curr: list[dict[str, object]]) -> dict[str, int]:
    prev_map = {str(r.get("ruta_completa", "")): str(r.get("sha256", "")) for r in prev}
    curr_map = {str(r.get("ruta_completa", "")): str(r.get("sha256", "")) for r in curr}

    rutas_prev = set(prev_map.keys())
    rutas_curr = set(curr_map.keys())

    nuevos = rutas_curr - rutas_prev
    eliminados = rutas_prev - rutas_curr
    modificados = {r for r in rutas_curr & rutas_prev if prev_map.get(r) != curr_map.get(r)}

    return {
        "nuevos": len(nuevos),
        "eliminados": len(eliminados),
        "modificados": len(modificados),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Integra lectura recursiva de Dropbox y clasificación documental.")
    parser.add_argument("--ruta", type=str, default="", help="Ruta FACTURACION a procesar.")
    parser.add_argument("--validate", action="store_true", help="Valida existencia de artefactos generados.")
    parser.add_argument("--dry-run", action="store_true", help="No escribe archivos; solo simula y muestra resultados.")
    parser.add_argument("--verbose", action="store_true", help="Activa logging detallado.")
    parser.add_argument("--dashboard", action="store_true", help="Abre dashboard visual al finalizar.")
    parser.add_argument("--analytics", action="store_true", help="Activa generación explícita de analítica documental.")
    parser.add_argument("--generate-reports", action="store_true", help="Activa generación explícita de reportes analíticos.")
    parser.add_argument("--snapshot", action="store_true", help="Activa snapshot explícito en docs/versions/latest/dropbox/analytics.")
    parser.add_argument(
        "--audit-search",
        action="store_true",
        help="Activa auditoría de búsqueda (por defecto desactivada).",
    )
    parser.add_argument(
        "--profiling",
        action="store_true",
        help="Activa perfilado de performance durante la auditoría de búsqueda.",
    )
    parser.add_argument(
        "--enforce-structure",
        action="store_true",
        help="Aplica reglas de estructura Dropbox (crea carpetas faltantes y normaliza ubicación de archivos).",
    )
    return parser.parse_args()


def main() -> int:
    start_ts = time.perf_counter()
    args = parse_args()
    root = Path(__file__).resolve().parent
    docs_dir = root / "docs"

    ruta = Path(args.ruta) if args.ruta else detectar_ruta_dropbox()
    ensure_info = ensure_dropbox_structure(ruta)
    estructura_validacion = validate_dropbox_structure(ruta)
    log(
        f"Estructura Dropbox validada | valid={estructura_validacion.get('valid')} | creadas={ensure_info.get('total_created', 0)}",
        verbose=True,
    )

    log(f"Ruta FACTURACION objetivo: {ruta}", verbose=True)
    try:
        registros = leer_dropbox_recursivo(ruta, logger=(lambda m: log(m, args.verbose)))
    except FileNotFoundError as error:
        print(f"Error: {error}")
        print("Tip: usa --ruta para indicar la carpeta FACTURACION correcta.")
        return 1
    clasificados = clasificar_documentos(registros)
    asignados = asignar_modulos_app(clasificados)
    etiquetados = asignar_etiquetas_automaticas(asignados)
    enriquecidos = enriquecer_con_ia(etiquetados)

    mapeo_json = docs_dir / "dropbox_mapeo_documentos.json"
    mapeo_md = docs_dir / "dropbox_mapeo_documentos.md"
    asignacion_json = docs_dir / "dropbox_asignacion_app.json"
    import_md = docs_dir / "markdown" / "DROPBOX_IMPORT.md"
    search_md = docs_dir / "markdown" / "DROPBOX_SEARCH.md"
    analytics_md = docs_dir / "markdown" / "DROPBOX_ANALYTICS.md"
    stats_json = docs_dir / "dropbox_search_stats.json"
    analytics_json = docs_dir / "dropbox_analytics.json"
    analytics_summary_json = docs_dir / "dropbox_analytics_summary.json"
    folder_tree_json = docs_dir / "dropbox_folder_tree.json"
    file_metrics_json = docs_dir / "dropbox_file_metrics.json"
    type_metrics_json = docs_dir / "dropbox_type_metrics.json"
    hospital_metrics_json = docs_dir / "dropbox_hospital_metrics.json"
    month_metrics_json = docs_dir / "dropbox_month_metrics.json"
    analytics_reportes_json = docs_dir / "dropbox_analytics_reportes.json"
    invoices_receptor_json = docs_dir / "dropbox_invoices_by_receptor.json"
    snapshot_analytics_dir = docs_dir / "versions" / "latest" / "dropbox" / "analytics"
    reportes_dir = docs_dir / "reportes"
    audit_search_enabled = bool(args.audit_search)
    profiling_enabled = bool(args.profiling)
    enforce_structure = bool(args.enforce_structure)

    arbol_virtual = construir_arbol_virtual(enriquecidos)
    analitica_detallada = analizar_documentos(enriquecidos)
    resumen_analitico = construir_resumen_analitico(analitica_detallada)
    resumen_arbol_virtual = resumen_arbol(arbol_virtual)
    metricas_adicionales = _generar_metricas_adicionales(enriquecidos, analitica_detallada)
    invoices_dataset = build_invoices_dataset(enriquecidos)

    if enforce_structure and not args.dry_run:
        pending_moves = normalize_images_to_pending(ruta)
        provider_moves = move_invoices_to_provider_folders(ruta, invoices_dataset)
        if pending_moves or provider_moves:
            log(
                f"Estructura aplicada | pending_moves={len(pending_moves)} | provider_moves={len(provider_moves)}",
                verbose=True,
            )
            registros = leer_dropbox_recursivo(ruta, logger=(lambda m: log(m, args.verbose)))
            clasificados = clasificar_documentos(registros)
            asignados = asignar_modulos_app(clasificados)
            etiquetados = asignar_etiquetas_automaticas(asignados)
            enriquecidos = enriquecer_con_ia(etiquetados)
            arbol_virtual = construir_arbol_virtual(enriquecidos)
            analitica_detallada = analizar_documentos(enriquecidos)
            resumen_analitico = construir_resumen_analitico(analitica_detallada)
            resumen_arbol_virtual = resumen_arbol(arbol_virtual)
            metricas_adicionales = _generar_metricas_adicionales(enriquecidos, analitica_detallada)
            invoices_dataset = build_invoices_dataset(enriquecidos)

    previo: list[dict[str, object]] = []
    if mapeo_json.exists():
        try:
            previo = json.loads(mapeo_json.read_text(encoding="utf-8"))
        except Exception:
            previo = []
    cambios_hash = _comparar_hashes(previo, enriquecidos)

    audit_info: dict[str, object] = {
        "enabled": False,
        "snapshot_json": "",
        "snapshot_csv": "",
        "snapshot_performance_json": "",
        "snapshot_performance_csv": "",
        "report_json": "",
        "report_csv": "",
        "report_performance_json": "",
        "report_performance_csv": "",
        "result_rows": 0,
    }

    if args.dry_run:
        log(f"Dry-run: {len(enriquecidos)} archivos procesados", verbose=True)
    else:
        if audit_search_enabled:
            log("Auditoría de búsqueda activada (flag --audit-search)", verbose=True)
            audit_info = _ejecutar_auditoria_busqueda(
                registros=enriquecidos,
                snapshot_dir=snapshot_analytics_dir,
                reportes_dir=reportes_dir,
                verbose=True,
                profiling=profiling_enabled,
            )
        else:
            log("Auditoría de búsqueda desactivada para esta corrida", verbose=True)
        exportar_mapeo(enriquecidos, mapeo_json, mapeo_md)
        exportar_asignacion(enriquecidos, asignacion_json)
        _actualizar_markdown_dropbox(enriquecidos, import_md)
        _actualizar_markdown_busqueda(search_md)
        _actualizar_markdown_analytics(analytics_md)
        exportar_json({"registros": analitica_detallada}, analytics_json)
        exportar_json(resumen_analitico | {"arbol_virtual": resumen_arbol_virtual}, analytics_summary_json)
        exportar_json(arbol_virtual, folder_tree_json)
        exportar_json({"registros": metricas_adicionales["file_metrics"]}, file_metrics_json)
        exportar_json({"tipos": metricas_adicionales["type_metrics"]}, type_metrics_json)
        exportar_json({"hospitales": metricas_adicionales["hospital_metrics"]}, hospital_metrics_json)
        exportar_json({"meses": metricas_adicionales["month_metrics"]}, month_metrics_json)
        exportar_json(
            {
                "facturas": invoices_dataset,
                "resumen": summarize_by_receptor(invoices_dataset),
            },
            invoices_receptor_json,
        )
        reportes = generar_paquete_reportes(
            resumen=resumen_analitico,
            analitica_detallada=analitica_detallada,
            tree_summary=resumen_arbol_virtual,
            out_dir=reportes_dir,
            auditoria_data=(
                audit_info.get("auditoria_data")
                if audit_search_enabled and isinstance(audit_info, dict)
                else None
            ),
        )
        payload_reportes: dict[str, object] = {"reportes": reportes}
        if audit_search_enabled:
            payload_reportes["auditoria"] = audit_info
        payload_reportes["facturas_receptor"] = {
            "artifact": str(invoices_receptor_json),
            "total_facturas": len(invoices_dataset),
        }
        payload_reportes["estructura_dropbox"] = {
            "valid": bool(estructura_validacion.get("valid", False)),
            "missing": list(estructura_validacion.get("missing", [])),
            "created": int(ensure_info.get("total_created", 0)),
            "enforced": enforce_structure,
        }
        exportar_json(payload_reportes, analytics_reportes_json)
        if not stats_json.exists():
            stats_json.write_text(
                json.dumps(
                    {
                        "terminos_mas_buscados": {},
                        "tipos_mas_encontrados": {},
                        "carpetas_mas_relevantes": {},
                        "historial": [],
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
        _actualizar_index_documentacion(docs_dir / "INDEX_DOCUMENTACION.md")
        _copiar_a_version_activa(docs_dir, dry_run=False)

    log(
        (
            "Cambios por hash -> "
            f"nuevos={cambios_hash['nuevos']}, "
            f"modificados={cambios_hash['modificados']}, "
            f"eliminados={cambios_hash['eliminados']}"
        ),
        verbose=True,
    )

    _actualizar_changelog(docs_dir / "CHANGELOG_DOCUMENTACION.md", len(enriquecidos), args.dry_run, audit_info=audit_info)

    if args.validate:
        ok, faltantes = _validate_outputs(docs_dir)
        if not ok:
            print("Validación fallida. Faltan artefactos:")
            for item in faltantes:
                print(f"- {item}")
            return 1

    if args.dashboard and enriquecidos:
        DashboardDocumentos(enriquecidos, search_stats=cargar_search_stats(docs_dir / "dropbox_search_stats.json")).run()

    elapsed = time.perf_counter() - start_ts
    log(f"Proceso completado. Archivos procesados: {len(enriquecidos)} | tiempo={elapsed:.2f}s", verbose=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

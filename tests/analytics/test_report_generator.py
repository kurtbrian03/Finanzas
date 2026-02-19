import csv
import json
from pathlib import Path
import zipfile

from dropbox_integration.report_generator import generar_paquete_reportes


def test_generar_paquete_reportes(tmp_path: Path) -> None:
    resumen = {
        "total_archivos": 3,
        "total_bytes": 300,
        "pdf_paginas": 5,
        "excel_hojas": 2,
        "imagenes_logo_probable": 1,
        "texto_palabras": 50,
        "zip_entradas": 2,
        "tipos": {"PDF": 1, "EXCEL": 1, "TEXTO": 1},
    }
    detalle = [
        {"nombre": "a.pdf", "tipo": "PDF", "metricas": {"paginas": 5}},
        {"nombre": "b.xlsx", "tipo": "EXCEL", "metricas": {"hojas": 2}},
    ]
    tree = {"proveedores_top": {"ProveedorUno": 2}, "hospitales_top": {"Hospital Central": 2}, "meses_top": {"01-Enero": 1}}

    reportes = generar_paquete_reportes(resumen, detalle, tree, tmp_path)

    assert Path(reportes["txt"]).exists()
    assert Path(reportes["excel"]).exists()
    assert Path(reportes["pdf"]).exists()
    assert Path(reportes["zip"]).exists()


def test_export_integration_zip(tmp_path: Path) -> None:
    resumen = {
        "total_archivos": 2,
        "total_bytes": 200,
        "tipos": {"PDF": 1, "TEXTO": 1},
    }
    detalle = [
        {"nombre": "factura.pdf", "tipo": "PDF", "metricas": {"paginas": 2}},
        {"nombre": "nota.txt", "tipo": "Texto", "metricas": {"palabras": 12}},
    ]
    tree = {"proveedores_top": {"ACME": 2}, "hospitales_top": {"Hospital Central": 2}, "meses_top": {"01-Enero": 1}}
    auditoria_data = {
        "metadata": {
            "engine_version": "2.0.0",
            "generated_at": "2026-02-17T10:00:00+00:00",
            "indexed_documents": 2,
            "audit_events": 3,
            "result_rows": 2,
        },
        "query_context": {"modo": "flexible", "query_raw": "factura acme"},
        "resumen_scores": {"score_final_avg": 0.8, "score_boosting_avg": 0.2},
        "resultados_scores": [
            {
                "ruta": "C:/tmp/factura.pdf",
                "score_exacto": 0.8,
                "score_fuzzy": 0.7,
                "score_semantico": 0.6,
                "score_tokens": 0.7,
                "score_temporal": 0.1,
                "score_estructural": 0.2,
                "score_boosting": 0.2,
                "score_final": 0.95,
            }
        ],
        "performance_metrics": {
            "timestamp": "2026-02-17T10:00:01+00:00",
            "version_motor": "2.0.0",
            "total_time_ms": 42.1,
            "components": {
                "prepare_corpus_ms": 4.3,
                "fuzzy_ms": 6.2,
                "tfidf_ms": 5.8,
                "semantic_ms": 7.1,
                "tokens_ms": 4.9,
                "temporal_ms": 2.1,
                "structural_ms": 2.5,
                "boosting_ms": 3.0,
                "ranking_ms": 5.7,
                "audit_ms": 0.5,
            },
        },
    }

    reportes = generar_paquete_reportes(
        resumen,
        detalle,
        tree,
        tmp_path,
        auditoria_data=auditoria_data,
    )

    assert Path(reportes["audit_json"]).exists()
    assert Path(reportes["audit_csv"]).exists()
    assert Path(reportes["performance_json"]).exists()
    assert Path(reportes["performance_csv"]).exists()

    payload = json.loads(Path(reportes["audit_json"]).read_text(encoding="utf-8"))
    assert payload["metadata"]["engine_version"] == "2.0.0"

    with Path(reportes["audit_csv"]).open("r", encoding="utf-8", newline="") as handler:
        rows = list(csv.DictReader(handler))
    assert rows
    assert "score_final" in rows[0]

    with Path(reportes["performance_csv"]).open("r", encoding="utf-8", newline="") as handler:
        perf_rows = list(csv.DictReader(handler))
    assert perf_rows
    assert "component" in perf_rows[0]
    assert "time_ms" in perf_rows[0]

    txt_content = Path(reportes["txt"]).read_text(encoding="utf-8")
    assert "Performance del motor (profiling):" in txt_content
    assert "prepare_corpus_ms" in txt_content

    with zipfile.ZipFile(reportes["zip"], "r") as archive:
        names = archive.namelist()
    assert any(name.endswith("_audit.json") for name in names)
    assert any(name.endswith("_audit.csv") for name in names)
    assert any(name.endswith("_performance.json") for name in names)
    assert any(name.endswith("_performance.csv") for name in names)

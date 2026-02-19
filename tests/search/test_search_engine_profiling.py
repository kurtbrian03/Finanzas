import csv
import json
from pathlib import Path

from dropbox_integration.search_engine import SearchEngine


def _docs() -> list[dict[str, object]]:
    return [
        {
            "nombre_archivo": "factura_hospital_central_enero_2026.pdf",
            "ruta_completa": "C:/tmp/factura_hospital_central_enero_2026.pdf",
            "extension": ".pdf",
            "carpeta": "PDF",
            "categoria": "PDF",
            "etiquetas": ["factura", "enero", "hospital"],
            "tamaño": 180,
            "fecha_modificacion": "2026-01-15T10:00:00",
            "hash": "a1",
            "contenido_extraido": "factura proveedor acme hospital central enero 2026",
            "proveedor_virtual": "ACME",
            "hospital_virtual": "Hospital Central",
            "mes_virtual": "01-Enero",
            "anio_virtual": "2026",
            "carpeta_virtual": "ACME/2026/Hospital Central/01-Enero",
        },
        {
            "nombre_archivo": "factura_hospital_norte_enero_2026.pdf",
            "ruta_completa": "C:/tmp/factura_hospital_norte_enero_2026.pdf",
            "extension": ".pdf",
            "carpeta": "PDF",
            "categoria": "PDF",
            "etiquetas": ["factura", "enero"],
            "tamaño": 165,
            "fecha_modificacion": "2026-01-12T10:00:00",
            "hash": "a2",
            "contenido_extraido": "factura proveedor acme hospital norte enero 2026",
            "proveedor_virtual": "ACME",
            "hospital_virtual": "Hospital Norte",
            "mes_virtual": "01-Enero",
            "anio_virtual": "2026",
            "carpeta_virtual": "ACME/2026/Hospital Norte/01-Enero",
        },
    ]


def _filtros() -> dict[str, object]:
    return {
        "tipo": "TODOS",
        "extension": "TODOS",
        "carpeta": "TODOS",
        "etiquetas": [],
        "fuzzy": True,
    }


def test_profiling_generates_performance_metrics_and_context(tmp_path: Path) -> None:
    engine = SearchEngine(_docs())
    engine.indexar_documentos()

    resultados = engine.buscar_avanzado(
        "factura hospital central",
        filtros=_filtros(),
        usar_nombre=True,
        usar_contenido=True,
        usar_semantico=True,
        modo="flexible",
        auditoria=True,
        profiling=True,
    )

    assert resultados
    perf = engine.get_last_performance_metrics()
    assert perf
    assert float(perf.get("total_time_ms", 0.0)) >= 0.0

    components = perf.get("components", {})
    assert isinstance(components, dict)
    expected = {
        "prepare_corpus_ms",
        "fuzzy_ms",
        "tfidf_ms",
        "semantic_ms",
        "tokens_ms",
        "temporal_ms",
        "structural_ms",
        "boosting_ms",
        "ranking_ms",
        "audit_ms",
    }
    assert expected.issubset(set(components.keys()))

    audit_payload_path = engine.export_auditoria_json(str(tmp_path / "auditoria_perfilada.json"))
    payload = json.loads(audit_payload_path.read_text(encoding="utf-8"))
    assert bool(payload.get("query_context", {}).get("profiling")) is True
    assert "performance_metrics" in payload


def test_profiling_exports_json_and_csv(tmp_path: Path) -> None:
    engine = SearchEngine(_docs())
    engine.indexar_documentos()

    _ = engine.buscar_avanzado(
        "factura acme",
        filtros=_filtros(),
        usar_nombre=True,
        usar_contenido=True,
        usar_semantico=True,
        modo="flexible",
        profiling=True,
    )

    json_path = engine.export_performance_json(str(tmp_path / "performance.json"))
    csv_path = engine.export_performance_csv(str(tmp_path / "performance.csv"))

    assert json_path.exists()
    assert csv_path.exists()

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert "components" in payload
    assert "total_time_ms" in payload

    with csv_path.open("r", encoding="utf-8", newline="") as handler:
        rows = list(csv.DictReader(handler))
    assert rows
    assert "component" in rows[0]
    assert "time_ms" in rows[0]


def test_profiling_disabled_clears_last_metrics() -> None:
    engine = SearchEngine(_docs())
    engine.indexar_documentos()

    _ = engine.buscar_avanzado("factura", filtros=_filtros(), modo="flexible", profiling=True)
    assert engine.get_last_performance_metrics()

    _ = engine.buscar_avanzado("factura", filtros=_filtros(), modo="flexible", profiling=False)
    assert engine.get_last_performance_metrics() == {}

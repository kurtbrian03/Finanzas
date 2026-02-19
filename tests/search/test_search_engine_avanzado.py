import csv
import json
from pathlib import Path

from dropbox_integration.search_engine import SearchEngine, benchmark_busquedas


def _docs_avanzados() -> list[dict[str, object]]:
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
        {
            "nombre_archivo": "factura_hospital_central_enero_2024.pdf",
            "ruta_completa": "C:/tmp/factura_hospital_central_enero_2024.pdf",
            "extension": ".pdf",
            "carpeta": "PDF",
            "categoria": "PDF",
            "etiquetas": ["factura", "enero"],
            "tamaño": 150,
            "fecha_modificacion": "2024-01-10T10:00:00",
            "hash": "a3",
            "contenido_extraido": "factura proveedor acme hospital central enero 2024",
            "proveedor_virtual": "ACME",
            "hospital_virtual": "Hospital Central",
            "mes_virtual": "01-Enero",
            "anio_virtual": "2024",
            "carpeta_virtual": "ACME/2024/Hospital Central/01-Enero",
        },
        {
            "nombre_archivo": "nota_credito_betha_hospital_sur.txt",
            "ruta_completa": "C:/tmp/nota_credito_betha_hospital_sur.txt",
            "extension": ".txt",
            "carpeta": "TEXTO",
            "categoria": "Texto",
            "etiquetas": ["nota", "credito"],
            "tamaño": 35,
            "fecha_modificacion": "2026-01-16T10:00:00",
            "hash": "a4",
            "contenido_extraido": "nota de credito proveedor betha hospital sur",
            "proveedor_virtual": "BETHA",
            "hospital_virtual": "Hospital Sur",
            "mes_virtual": "01-Enero",
            "anio_virtual": "2026",
            "carpeta_virtual": "BETHA/2026/Hospital Sur/01-Enero",
        },
    ]


def _filtros_base() -> dict[str, object]:
    return {
        "tipo": "TODOS",
        "extension": "TODOS",
        "carpeta": "TODOS",
        "etiquetas": [],
        "fuzzy": True,
    }


def test_ranking_hibrido_con_boosting_contextual() -> None:
    engine = SearchEngine(_docs_avanzados())
    engine.indexar_documentos()

    filtros = {
        **_filtros_base(),
        "proveedor": "ACME",
        "hospital": "Hospital Central",
    }
    resultados = engine.buscar_avanzado(
        "factura hospital central enero 2026",
        filtros=filtros,
        usar_nombre=True,
        usar_contenido=True,
        usar_semantico=True,
        modo="flexible",
    )

    assert resultados
    assert resultados[0]["hash"] == "a1"


def test_modo_estricto_vs_flexible() -> None:
    engine = SearchEngine(_docs_avanzados())
    engine.indexar_documentos()

    filtros = _filtros_base()
    estricto = engine.buscar_avanzado(
        "factura hospital central",
        filtros=filtros,
        usar_nombre=True,
        usar_contenido=True,
        usar_semantico=True,
        modo="estricta",
    )
    flexible = engine.buscar_avanzado(
        "factura hospital central",
        filtros=filtros,
        usar_nombre=True,
        usar_contenido=True,
        usar_semantico=True,
        modo="flexible",
    )

    assert estricto
    assert flexible
    assert len(flexible) >= len(estricto)


def test_prioridad_temporal_en_consulta_general() -> None:
    engine = SearchEngine(_docs_avanzados())
    engine.indexar_documentos()

    resultados = engine.buscar_avanzado(
        "factura hospital central",
        filtros={**_filtros_base(), "hospital": "Hospital Central"},
        usar_nombre=True,
        usar_contenido=True,
        usar_semantico=True,
        modo="flexible",
    )

    hashes = [str(r.get("hash")) for r in resultados]
    assert "a1" in hashes and "a3" in hashes
    assert hashes.index("a1") < hashes.index("a3")


def test_similitud_estructural_por_carpeta_virtual() -> None:
    engine = SearchEngine(_docs_avanzados())
    engine.indexar_documentos()

    resultados = engine.buscar_avanzado(
        "acme hospital norte 2026 enero",
        filtros={**_filtros_base(), "carpeta_virtual": "ACME/2026/Hospital Norte/01-Enero"},
        usar_nombre=True,
        usar_contenido=True,
        usar_semantico=False,
        modo="flexible",
    )

    assert resultados
    assert resultados[0]["hash"] == "a2"


def test_regresion_consistencia_ordenamiento() -> None:
    engine = SearchEngine(_docs_avanzados())
    engine.indexar_documentos()

    filtros = _filtros_base()
    r1 = engine.buscar_avanzado("factura acme", filtros=filtros, usar_semantico=True, modo="flexible")
    r2 = engine.buscar_avanzado("factura acme", filtros=filtros, usar_semantico=True, modo="flexible")

    assert [x["hash"] for x in r1] == [x["hash"] for x in r2]


def test_benchmark_busquedas_retorna_metricas() -> None:
    engine = SearchEngine(_docs_avanzados())
    engine.indexar_documentos()

    metricas = benchmark_busquedas(
        engine,
        consultas=["factura acme", "hospital central", "nota credito"],
        filtros=_filtros_base(),
        repeticiones=2,
        modo="flexible",
    )

    assert metricas["consultas"] == 6
    assert float(metricas["media_ms"]) >= 0
    assert float(metricas["p95_ms"]) >= 0
    assert int(metricas["resultados"]) >= 1


def test_audit_log_genera_eventos() -> None:
    engine = SearchEngine(_docs_avanzados())
    engine.indexar_documentos()

    _ = engine.buscar_avanzado("factura", filtros=_filtros_base(), modo="flexible")
    auditoria = engine.get_audit_log(limit=10)

    assert auditoria
    assert any(str(x.get("evento")) == "indexacion" for x in auditoria)
    assert any(str(x.get("evento")) == "busqueda_avanzada" for x in auditoria)


def test_busqueda_avanzada_admite_weights_y_auditoria() -> None:
    engine = SearchEngine(_docs_avanzados())
    engine.indexar_documentos()

    resultados = engine.buscar_avanzado(
        "factura acme hospital",
        filtros=_filtros_base(),
        usar_nombre=True,
        usar_contenido=True,
        usar_semantico=True,
        modo="flexible",
        weights={
            "boost_proveedor": 1.5,
            "boost_hospital": 1.4,
            "boost_temporal": 1.2,
            "score_exacto": 1.3,
            "score_semantico": 1.5,
            "score_tokens": 1.1,
        },
        auditoria=True,
    )

    assert resultados
    assert "score_final" in resultados[0]
    assert "score_boosting" in resultados[0]
    assert any(str(x.get("evento")) == "busqueda_auditoria" for x in engine.get_audit_log(limit=20))


def test_export_auditoria_json(tmp_path: Path) -> None:
    engine = SearchEngine(_docs_avanzados())
    engine.indexar_documentos()
    engine.buscar_avanzado("factura acme", filtros=_filtros_base(), auditoria=True, modo="flexible")

    out_file = tmp_path / "auditoria.json"
    exported = engine.export_auditoria_json(str(out_file))

    assert exported.exists()
    payload = json.loads(exported.read_text(encoding="utf-8"))
    assert "metadata" in payload
    assert "resultados_scores" in payload
    assert int(payload["metadata"]["result_rows"]) >= 1


def test_export_auditoria_csv(tmp_path: Path) -> None:
    engine = SearchEngine(_docs_avanzados())
    engine.indexar_documentos()
    engine.buscar_avanzado("factura", filtros=_filtros_base(), auditoria=True, modo="flexible")

    out_file = tmp_path / "auditoria.csv"
    exported = engine.export_auditoria_csv(str(out_file))

    assert exported.exists()
    with exported.open("r", encoding="utf-8", newline="") as handler:
        rows = list(csv.DictReader(handler))
    assert rows
    assert "score_final" in rows[0]


def test_export_auditoria_empty(tmp_path: Path) -> None:
    engine = SearchEngine([])
    engine.indexar_documentos()

    json_path = engine.export_auditoria_json(str(tmp_path / "empty.json"))
    csv_path = engine.export_auditoria_csv(str(tmp_path / "empty.csv"))

    assert json_path.exists()
    assert csv_path.exists()

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["resultados_scores"] == []
    assert int(payload["metadata"]["result_rows"]) == 0

    with csv_path.open("r", encoding="utf-8", newline="") as handler:
        rows = list(csv.DictReader(handler))
    assert rows == []


def test_export_auditoria_full(tmp_path: Path) -> None:
    engine = SearchEngine(_docs_avanzados())
    engine.indexar_documentos()
    engine.buscar_avanzado(
        "factura hospital central enero 2026",
        filtros={**_filtros_base(), "hospital": "Hospital Central", "proveedor": "ACME"},
        usar_nombre=True,
        usar_contenido=True,
        usar_semantico=True,
        auditoria=True,
        modo="flexible",
    )

    json_path = engine.export_auditoria_json(str(tmp_path / "full.json"))
    csv_path = engine.export_auditoria_csv(str(tmp_path / "full.csv"))

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["query_context"]["modo"] == "flexible"
    assert payload["resumen_scores"]["score_final_max"] >= payload["resumen_scores"]["score_final_min"]
    assert payload["resultados_scores"]

    with csv_path.open("r", encoding="utf-8", newline="") as handler:
        rows = list(csv.DictReader(handler))
    assert rows
    assert all("ruta" in row for row in rows)

from pathlib import Path
import sys
import zipfile

import pytest

import integrar_dropbox
from dropbox_integration.report_generator import generar_paquete_reportes
from dropbox_integration.lector_dropbox import leer_dropbox_recursivo
from dropbox_integration.search_engine import SearchEngine


def test_pipeline_integrado_dropbox(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    base = tmp_path / "FACTURACION"
    carpeta = base / "PDF"
    carpeta.mkdir(parents=True)
    archivo = carpeta / "factura_demo.txt"
    archivo.write_text("Factura demo cliente ACME", encoding="utf-8")

    from dropbox_integration import lector_dropbox

    monkeypatch.setattr(lector_dropbox, "CARPETAS_FACTURACION", ["PDF"])
    registros = leer_dropbox_recursivo(base, logger=lambda _m: None)

    assert registros
    assert "contenido_extraido" in registros[0]
    assert registros[0].get("hash")

    engine = SearchEngine(registros)
    engine.indexar_documentos()
    resultados = engine.buscar_avanzado(
        "factura",
        filtros={"tipo": "TODOS", "extension": "TODOS", "carpeta": "TODOS", "etiquetas": [], "fuzzy": True},
        usar_nombre=True,
        usar_contenido=True,
        usar_semantico=True,
    )
    assert resultados


def test_pipeline_auditoria_search_exporta_y_entra_en_zip(tmp_path: Path) -> None:
    registros = [
        {
            "nombre_archivo": "factura_demo_acme.pdf",
            "ruta_completa": str(tmp_path / "factura_demo_acme.pdf"),
            "extension": ".pdf",
            "carpeta": "PDF",
            "categoria": "PDF",
            "etiquetas": ["factura", "acme"],
            "tamaño": 120,
            "fecha_modificacion": "2026-02-18T10:00:00",
            "hash": "a1",
            "contenido_extraido": "factura proveedor acme hospital central enero 2026",
            "proveedor_virtual": "ACME",
            "hospital_virtual": "Hospital Central",
            "mes_virtual": "01-Enero",
            "anio_virtual": "2026",
            "carpeta_virtual": "ACME/2026/Hospital Central/01-Enero",
        }
    ]

    snapshot_dir = tmp_path / "docs" / "versions" / "latest" / "dropbox" / "analytics"
    reportes_dir = tmp_path / "docs" / "reportes"
    audit_info = integrar_dropbox._ejecutar_auditoria_busqueda(
        registros=registros,
        snapshot_dir=snapshot_dir,
        reportes_dir=reportes_dir,
        verbose=False,
    )

    assert bool(audit_info.get("enabled"))
    snapshot_json = Path(str(audit_info.get("snapshot_json", "")))
    snapshot_csv = Path(str(audit_info.get("snapshot_csv", "")))
    assert snapshot_json.exists()
    assert snapshot_csv.exists()

    resumen = {"total_archivos": 1, "total_bytes": 120, "tipos": {"PDF": 1}}
    detalle = [
        {
            "ruta": str(tmp_path / "factura_demo_acme.pdf"),
            "nombre": "factura_demo_acme.pdf",
            "tipo": "PDF",
            "extension": ".pdf",
            "tamano_bytes": 120,
            "fecha_modificacion": "2026-02-18T10:00:00",
        }
    ]
    tree = {"proveedores_top": {"ACME": 1}, "hospitales_top": {"Hospital Central": 1}, "meses_top": {"01-Enero": 1}}

    reportes = generar_paquete_reportes(
        resumen=resumen,
        analitica_detallada=detalle,
        tree_summary=tree,
        out_dir=reportes_dir,
        auditoria_data=audit_info.get("auditoria_data") if isinstance(audit_info, dict) else None,
    )

    assert Path(reportes["audit_json"]).exists()
    assert Path(reportes["audit_csv"]).exists()

    with zipfile.ZipFile(reportes["zip"], "r") as archive:
        names = archive.namelist()
    assert any(name.endswith("_audit.json") for name in names)
    assert any(name.endswith("_audit.csv") for name in names)

    txt_content = Path(reportes["txt"]).read_text(encoding="utf-8")
    assert "Auditoría de búsqueda" in txt_content


def test_pipeline_auditoria_search_con_profiling_exporta_performance(tmp_path: Path) -> None:
    registros = [
        {
            "nombre_archivo": "factura_demo_acme.pdf",
            "ruta_completa": str(tmp_path / "factura_demo_acme.pdf"),
            "extension": ".pdf",
            "carpeta": "PDF",
            "categoria": "PDF",
            "etiquetas": ["factura", "acme"],
            "tamaño": 120,
            "fecha_modificacion": "2026-02-18T10:00:00",
            "hash": "a1",
            "contenido_extraido": "factura proveedor acme hospital central enero 2026",
            "proveedor_virtual": "ACME",
            "hospital_virtual": "Hospital Central",
            "mes_virtual": "01-Enero",
            "anio_virtual": "2026",
            "carpeta_virtual": "ACME/2026/Hospital Central/01-Enero",
        }
    ]

    snapshot_dir = tmp_path / "docs" / "versions" / "latest" / "dropbox" / "analytics"
    reportes_dir = tmp_path / "docs" / "reportes"
    audit_info = integrar_dropbox._ejecutar_auditoria_busqueda(
        registros=registros,
        snapshot_dir=snapshot_dir,
        reportes_dir=reportes_dir,
        verbose=False,
        profiling=True,
    )

    assert bool(audit_info.get("enabled"))
    assert Path(str(audit_info.get("snapshot_performance_json", ""))).exists()
    assert Path(str(audit_info.get("snapshot_performance_csv", ""))).exists()
    assert Path(str(audit_info.get("report_performance_json", ""))).exists()
    assert Path(str(audit_info.get("report_performance_csv", ""))).exists()


def test_pipeline_sin_auditoria_no_genera_artifacts_en_zip(tmp_path: Path) -> None:
    resumen = {"total_archivos": 1, "total_bytes": 120, "tipos": {"PDF": 1}}
    detalle = [
        {
            "ruta": str(tmp_path / "factura_demo_acme.pdf"),
            "nombre": "factura_demo_acme.pdf",
            "tipo": "PDF",
            "extension": ".pdf",
            "tamano_bytes": 120,
            "fecha_modificacion": "2026-02-18T10:00:00",
        }
    ]
    tree = {"proveedores_top": {"ACME": 1}, "hospitales_top": {"Hospital Central": 1}, "meses_top": {"01-Enero": 1}}
    reportes_dir = tmp_path / "docs" / "reportes"

    reportes = generar_paquete_reportes(
        resumen=resumen,
        analitica_detallada=detalle,
        tree_summary=tree,
        out_dir=reportes_dir,
        auditoria_data=None,
    )

    assert "audit_json" not in reportes
    assert "audit_csv" not in reportes

    with zipfile.ZipFile(reportes["zip"], "r") as archive:
        names = archive.namelist()
    assert not any(name.endswith("_audit.json") for name in names)
    assert not any(name.endswith("_audit.csv") for name in names)

    txt_content = Path(reportes["txt"]).read_text(encoding="utf-8")
    assert "Auditoría de búsqueda" not in txt_content


def test_parse_args_audit_search_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["integrar_dropbox.py", "--audit-search"])
    args = integrar_dropbox.parse_args()
    assert bool(args.audit_search)


def test_parse_args_audit_search_default_off(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["integrar_dropbox.py"])
    args = integrar_dropbox.parse_args()
    assert not bool(args.audit_search)


def test_parse_args_profiling_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["integrar_dropbox.py", "--profiling"])
    args = integrar_dropbox.parse_args()
    assert bool(args.profiling)

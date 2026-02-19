import json
from pathlib import Path

from ui.dashboard_facturas_receptor import _find_audit_snapshots, _load_registros_default


def test_load_registros_default_reads_valid_list(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir(parents=True)
    payload = [{"nombre_archivo": "a.pdf"}, {"nombre_archivo": "b.pdf"}, "invalid"]
    (docs / "dropbox_asignacion_app.json").write_text(json.dumps(payload), encoding="utf-8")

    out = _load_registros_default(tmp_path)
    assert len(out) == 2
    assert all(isinstance(item, dict) for item in out)


def test_find_audit_snapshots_returns_sorted_matches(tmp_path: Path) -> None:
    versions = tmp_path / "docs" / "versions" / "2026-02"
    versions.mkdir(parents=True)

    f1 = versions / "x_search_audit_old.json"
    f2 = versions / "x_search_audit_new.json"
    f1.write_text("{}", encoding="utf-8")
    f2.write_text("{}", encoding="utf-8")

    f1.touch()
    f2.touch()

    out = _find_audit_snapshots(tmp_path)
    assert len(out) == 2
    assert all("search_audit" in p.name for p in out)

import csv
import json
from pathlib import Path

from dropbox_integration.audit_diff import (
    compare_auditoria_snapshots,
    export_auditoria_diff_csv,
    export_auditoria_diff_json,
    export_auditoria_diff_txt,
)


def _snapshot_payload(resultados: list[dict[str, object]]) -> dict[str, object]:
    return {
        "metadata": {"engine_version": "2.0.0", "result_rows": len(resultados)},
        "query_context": {"query_raw": "factura", "modo": "flexible"},
        "resultados_scores": resultados,
    }


def test_compare_auditoria_snapshots_calcula_deltas(tmp_path: Path) -> None:
    snap_a = _snapshot_payload(
        [
            {"ruta": "A", "score_final": 0.90, "score_exacto": 0.6, "score_fuzzy": 0.5},
            {"ruta": "B", "score_final": 0.80, "score_exacto": 0.5, "score_fuzzy": 0.4},
            {"ruta": "C", "score_final": 0.70, "score_exacto": 0.4, "score_fuzzy": 0.3},
        ]
    )
    snap_b = _snapshot_payload(
        [
            {"ruta": "B", "score_final": 0.92, "score_exacto": 0.7, "score_fuzzy": 0.6},
            {"ruta": "A", "score_final": 0.85, "score_exacto": 0.6, "score_fuzzy": 0.5},
            {"ruta": "D", "score_final": 0.60, "score_exacto": 0.3, "score_fuzzy": 0.2},
        ]
    )

    p_a = tmp_path / "a.json"
    p_b = tmp_path / "b.json"
    p_a.write_text(json.dumps(snap_a, ensure_ascii=False), encoding="utf-8")
    p_b.write_text(json.dumps(snap_b, ensure_ascii=False), encoding="utf-8")

    diff = compare_auditoria_snapshots(p_a, p_b, snapshot_name_a="A", snapshot_name_b="B", top_n=5)

    metadata = diff["metadata"]
    assert metadata["snapshot_a"] == "A"
    assert metadata["snapshot_b"] == "B"
    assert int(metadata["common_docs"]) == 2
    assert int(metadata["new_docs"]) == 1
    assert int(metadata["removed_docs"]) == 1

    ranking = diff["summary"]["ranking"]
    assert int(ranking["up_count"]) == 1
    assert int(ranking["down_count"]) == 1
    assert int(ranking["same_count"]) == 0

    docs = [x for x in diff["documents"] if x.get("status") == "common"]
    doc_b = next(x for x in docs if x["ruta"] == "B")
    assert int(doc_b["pos_a"]) == 2
    assert int(doc_b["pos_b"]) == 1
    assert int(doc_b["delta_pos"]) == 1


def test_export_auditoria_diff_archivos(tmp_path: Path) -> None:
    snap_a = _snapshot_payload([{"ruta": "A", "score_final": 0.9}])
    snap_b = _snapshot_payload([{"ruta": "A", "score_final": 1.0}])

    p_a = tmp_path / "a.json"
    p_b = tmp_path / "b.json"
    p_a.write_text(json.dumps(snap_a, ensure_ascii=False), encoding="utf-8")
    p_b.write_text(json.dumps(snap_b, ensure_ascii=False), encoding="utf-8")

    diff = compare_auditoria_snapshots(p_a, p_b, snapshot_name_a="A", snapshot_name_b="B")

    out_json = export_auditoria_diff_json(diff, tmp_path / "diff.json")
    out_csv = export_auditoria_diff_csv(diff, tmp_path / "diff.csv")
    out_txt = export_auditoria_diff_txt(diff, tmp_path / "diff.txt")

    assert out_json.exists()
    assert out_csv.exists()
    assert out_txt.exists()

    payload = json.loads(out_json.read_text(encoding="utf-8"))
    assert "summary" in payload
    assert "documents" in payload

    with out_csv.open("r", encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    assert rows
    assert "delta_score_final" in rows[0]

    txt = out_txt.read_text(encoding="utf-8")
    assert "AUDITORIA DIFF SNAPSHOTS" in txt
    assert "Top cambios de ranking" in txt
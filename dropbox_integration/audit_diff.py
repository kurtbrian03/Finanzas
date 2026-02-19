from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path


COMPONENTES_SCORE = [
    "score_exacto",
    "score_fuzzy",
    "score_semantico",
    "score_tokens",
    "score_temporal",
    "score_estructural",
    "score_boosting",
]


def _to_float(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _safe_dict(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _safe_list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _load_snapshot(path: str | Path) -> dict[str, object]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Snapshot no encontrado: {p}")
    payload = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Snapshot inválido (no es objeto JSON): {p}")
    return payload


def _indexar_resultados(snapshot: dict[str, object]) -> tuple[list[dict[str, object]], dict[str, dict[str, object]]]:
    resultados = [x for x in _safe_list(snapshot.get("resultados_scores", [])) if isinstance(x, dict)]
    index: dict[str, dict[str, object]] = {}
    for pos, row in enumerate(resultados, start=1):
        ruta = str(row.get("ruta", "")).strip()
        if not ruta:
            continue
        index[ruta] = {"pos": pos, **row}
    return resultados, index


def _mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return round(sum(values) / len(values), 6)


def compare_auditoria_snapshots(
    snapshot_a_path: str | Path,
    snapshot_b_path: str | Path,
    snapshot_name_a: str = "snapshot_a",
    snapshot_name_b: str = "snapshot_b",
    top_n: int = 20,
) -> dict[str, object]:
    """Compara dos snapshots de auditoría y retorna diff completo reutilizable para CLI/UI/CI."""
    snap_a = _load_snapshot(snapshot_a_path)
    snap_b = _load_snapshot(snapshot_b_path)

    resultados_a, idx_a = _indexar_resultados(snap_a)
    resultados_b, idx_b = _indexar_resultados(snap_b)

    rutas_a = set(idx_a.keys())
    rutas_b = set(idx_b.keys())
    comunes = sorted(rutas_a & rutas_b)
    nuevas = sorted(rutas_b - rutas_a)
    removidas = sorted(rutas_a - rutas_b)

    docs_diff: list[dict[str, object]] = []
    up_count = 0
    down_count = 0
    same_count = 0

    delta_final_vals: list[float] = []
    delta_por_componente: dict[str, list[float]] = {k: [] for k in COMPONENTES_SCORE}

    for ruta in comunes:
        row_a = _safe_dict(idx_a.get(ruta, {}))
        row_b = _safe_dict(idx_b.get(ruta, {}))
        pos_a = int(row_a.get("pos", 0) or 0)
        pos_b = int(row_b.get("pos", 0) or 0)
        delta_pos = pos_a - pos_b

        if delta_pos > 0:
            up_count += 1
        elif delta_pos < 0:
            down_count += 1
        else:
            same_count += 1

        score_a = _to_float(row_a.get("score_final", row_a.get("relevancia", 0.0)))
        score_b = _to_float(row_b.get("score_final", row_b.get("relevancia", 0.0)))
        delta_score = round(score_b - score_a, 6)
        delta_final_vals.append(delta_score)

        row_diff: dict[str, object] = {
            "ruta": ruta,
            "status": "common",
            "pos_a": pos_a,
            "pos_b": pos_b,
            "delta_pos": delta_pos,
            "score_final_a": score_a,
            "score_final_b": score_b,
            "delta_score_final": delta_score,
        }

        for comp in COMPONENTES_SCORE:
            comp_a = _to_float(row_a.get(comp, 0.0))
            comp_b = _to_float(row_b.get(comp, 0.0))
            comp_delta = round(comp_b - comp_a, 6)
            row_diff[f"{comp}_a"] = comp_a
            row_diff[f"{comp}_b"] = comp_b
            row_diff[f"delta_{comp}"] = comp_delta
            delta_por_componente[comp].append(comp_delta)

        docs_diff.append(row_diff)

    for ruta in nuevas:
        row_b = _safe_dict(idx_b.get(ruta, {}))
        docs_diff.append(
            {
                "ruta": ruta,
                "status": "new",
                "pos_a": None,
                "pos_b": int(row_b.get("pos", 0) or 0),
                "delta_pos": None,
                "score_final_a": 0.0,
                "score_final_b": _to_float(row_b.get("score_final", row_b.get("relevancia", 0.0))),
                "delta_score_final": None,
            }
        )

    for ruta in removidas:
        row_a = _safe_dict(idx_a.get(ruta, {}))
        docs_diff.append(
            {
                "ruta": ruta,
                "status": "removed",
                "pos_a": int(row_a.get("pos", 0) or 0),
                "pos_b": None,
                "delta_pos": None,
                "score_final_a": _to_float(row_a.get("score_final", row_a.get("relevancia", 0.0))),
                "score_final_b": 0.0,
                "delta_score_final": None,
            }
        )

    total_common = len(comunes)
    up_pct = round((up_count / total_common) * 100.0, 4) if total_common else 0.0
    down_pct = round((down_count / total_common) * 100.0, 4) if total_common else 0.0
    same_pct = round((same_count / total_common) * 100.0, 4) if total_common else 0.0

    top_rank_changes = sorted(
        [d for d in docs_diff if d.get("status") == "common" and isinstance(d.get("delta_pos"), int)],
        key=lambda x: abs(int(x.get("delta_pos", 0))),
        reverse=True,
    )[: max(1, top_n)]

    summary = {
        "ranking": {
            "up_count": up_count,
            "down_count": down_count,
            "same_count": same_count,
            "up_pct": up_pct,
            "down_pct": down_pct,
            "same_pct": same_pct,
        },
        "score": {
            "avg_delta_score_final": _mean(delta_final_vals),
            **{f"avg_delta_{comp}": _mean(vals) for comp, vals in delta_por_componente.items()},
        },
    }

    return {
        "metadata": {
            "compared_at": datetime.now(timezone.utc).isoformat(),
            "snapshot_a": snapshot_name_a,
            "snapshot_b": snapshot_name_b,
            "rows_a": len(resultados_a),
            "rows_b": len(resultados_b),
            "common_docs": len(comunes),
            "new_docs": len(nuevas),
            "removed_docs": len(removidas),
        },
        "summary": summary,
        "documents": docs_diff,
        "top_rank_changes": top_rank_changes,
    }


def export_auditoria_diff_json(diff_payload: dict[str, object], out_path: str | Path) -> Path:
    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(diff_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def export_auditoria_diff_csv(diff_payload: dict[str, object], out_path: str | Path) -> Path:
    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    docs = [x for x in _safe_list(diff_payload.get("documents", [])) if isinstance(x, dict)]

    base_cols = [
        "ruta",
        "status",
        "pos_a",
        "pos_b",
        "delta_pos",
        "score_final_a",
        "score_final_b",
        "delta_score_final",
    ]
    score_cols = []
    for comp in COMPONENTES_SCORE:
        score_cols.extend([f"{comp}_a", f"{comp}_b", f"delta_{comp}"])
    cols = base_cols + score_cols

    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=cols)
        writer.writeheader()
        for doc in docs:
            writer.writerow({k: doc.get(k) for k in cols})
    return path


def export_auditoria_diff_txt(diff_payload: dict[str, object], out_path: str | Path) -> Path:
    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    metadata = _safe_dict(diff_payload.get("metadata", {}))
    summary = _safe_dict(diff_payload.get("summary", {}))
    ranking = _safe_dict(summary.get("ranking", {}))
    score = _safe_dict(summary.get("score", {}))
    top = [x for x in _safe_list(diff_payload.get("top_rank_changes", [])) if isinstance(x, dict)]

    lines = [
        "AUDITORIA DIFF SNAPSHOTS",
        f"Snapshot A: {metadata.get('snapshot_a', '')}",
        f"Snapshot B: {metadata.get('snapshot_b', '')}",
        f"Compared at: {metadata.get('compared_at', '')}",
        "",
        f"Common docs: {metadata.get('common_docs', 0)}",
        f"New docs: {metadata.get('new_docs', 0)}",
        f"Removed docs: {metadata.get('removed_docs', 0)}",
        "",
        f"Up: {ranking.get('up_count', 0)} ({ranking.get('up_pct', 0)}%)",
        f"Down: {ranking.get('down_count', 0)} ({ranking.get('down_pct', 0)}%)",
        f"Same: {ranking.get('same_count', 0)} ({ranking.get('same_pct', 0)}%)",
        f"Avg Δ score final: {score.get('avg_delta_score_final', 0.0)}",
        "",
        "Top cambios de ranking:",
    ]
    for row in top:
        lines.append(
            f"- {row.get('ruta', '')} | pos_A={row.get('pos_a')} | "
            f"pos_B={row.get('pos_b')} | delta_pos={row.get('delta_pos')}"
        )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
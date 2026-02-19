from __future__ import annotations

import argparse
from pathlib import Path

from dropbox_integration.audit_diff import (
    compare_auditoria_snapshots,
    export_auditoria_diff_csv,
    export_auditoria_diff_json,
    export_auditoria_diff_txt,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Auditoría CI/CD para snapshots de búsqueda")
    parser.add_argument("--snapshot-a", required=True, help="Ruta snapshot A (anterior)")
    parser.add_argument("--snapshot-b", required=True, help="Ruta snapshot B (actual)")
    parser.add_argument("--name-a", default="snapshot_a", help="Nombre lógico snapshot A")
    parser.add_argument("--name-b", default="snapshot_b", help="Nombre lógico snapshot B")
    parser.add_argument("--out-dir", default="docs/reportes", help="Directorio de salida de diff")
    parser.add_argument("--top-n", type=int, default=25, help="Top cambios de ranking")
    parser.add_argument("--max-down-pct", type=float, default=35.0, help="Umbral máximo permitido de caída (%)")
    parser.add_argument(
        "--max-negative-delta-score",
        type=float,
        default=0.02,
        help="Máxima degradación permitida en avg_delta_score_final (valor absoluto)",
    )
    return parser.parse_args()


def evaluate_ci_policy(diff: dict[str, object], max_down_pct: float, max_negative_delta_score: float) -> tuple[bool, str]:
    summary = diff.get("summary", {}) if isinstance(diff, dict) else {}
    ranking = summary.get("ranking", {}) if isinstance(summary, dict) else {}
    score = summary.get("score", {}) if isinstance(summary, dict) else {}

    down_pct = float(ranking.get("down_pct", ranking.get("pct_down", 0.0)) or 0.0)
    avg_delta = float(score.get("avg_delta_score_final", 0.0) or 0.0)

    if down_pct > max_down_pct:
        return False, f"Fallo CI: down_pct={down_pct:.4f}% excede umbral {max_down_pct:.4f}%"
    if avg_delta < -(abs(max_negative_delta_score)):
        return False, (
            "Fallo CI: avg_delta_score_final="
            f"{avg_delta:.6f} es menor al umbral permitido -{abs(max_negative_delta_score):.6f}"
        )

    return True, (
        "OK CI: "
        f"down_pct={down_pct:.4f}% | avg_delta_score_final={avg_delta:.6f}"
    )


def main() -> int:
    args = parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    diff = compare_auditoria_snapshots(
        snapshot_a_path=args.snapshot_a,
        snapshot_b_path=args.snapshot_b,
        snapshot_name_a=args.name_a,
        snapshot_name_b=args.name_b,
        top_n=max(1, int(args.top_n)),
    )

    export_auditoria_diff_json(diff, out_dir / "ci_audit_diff.json")
    export_auditoria_diff_csv(diff, out_dir / "ci_audit_diff.csv")
    export_auditoria_diff_txt(diff, out_dir / "ci_audit_diff.txt")

    ok, message = evaluate_ci_policy(
        diff,
        max_down_pct=float(args.max_down_pct),
        max_negative_delta_score=float(args.max_negative_delta_score),
    )
    print(message)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

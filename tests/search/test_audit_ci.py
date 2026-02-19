from pathlib import Path

from dropbox_integration.audit_ci import evaluate_ci_policy


def test_evaluate_ci_policy_ok() -> None:
    diff = {
        "summary": {
            "ranking": {"down_pct": 10.0},
            "score": {"avg_delta_score_final": 0.01},
        }
    }
    ok, _ = evaluate_ci_policy(diff, max_down_pct=35.0, max_negative_delta_score=0.02)
    assert ok


def test_evaluate_ci_policy_fail() -> None:
    diff = {
        "summary": {
            "ranking": {"down_pct": 50.0},
            "score": {"avg_delta_score_final": -0.10},
        }
    }
    ok, msg = evaluate_ci_policy(diff, max_down_pct=35.0, max_negative_delta_score=0.02)
    assert not ok
    assert "Fallo CI" in msg

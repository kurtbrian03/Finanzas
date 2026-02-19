from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_validate_scripts_exist() -> None:
    expected = {
        "validate_all.ps1",
        "validate_python.ps1",
        "validate_gmail_api.ps1",
        "validate_credentials.ps1",
        "validate_smtp.ps1",
        "validate_gmail_pinpon.ps1",
        "validate_folders.ps1",
        "validate_config.ps1",
    }

    found = {p.name for p in PROJECT_ROOT.glob("validate_*.ps1")}
    missing = expected - found

    assert not missing, f"Faltan validadores: {sorted(missing)}"

from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_setup_scripts_exist() -> None:
    expected = {
        "setup_pinpon.ps1",
        "build_requirements.ps1",
        "rebuild_venv.ps1",
        "validate_python.ps1",
        "validate_folders.ps1",
        "validate_config.ps1",
        "reset_pinpon.ps1",
        "init_project_structure.ps1",
        "check_venv.ps1",
        "check_pip.ps1",
        "check_python_version.ps1",
    }

    missing = [name for name in expected if not (PROJECT_ROOT / name).exists()]
    assert not missing, f"Faltan scripts setup/check: {sorted(missing)}"

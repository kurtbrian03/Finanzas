from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_workflows_exist() -> None:
    ci = PROJECT_ROOT / ".github/workflows/ci.yml"
    cd = PROJECT_ROOT / ".github/workflows/cd.yml"
    publish = PROJECT_ROOT / ".github/workflows/publish_pip.yml"
    create_remote = PROJECT_ROOT / ".github/workflows/create_remote_repo.yml"
    sync_submodules = PROJECT_ROOT / ".github/workflows/sync_submodules.yml"

    assert ci.exists(), "No existe ci.yml"
    assert cd.exists(), "No existe cd.yml"
    assert publish.exists(), "No existe publish_pip.yml"
    assert create_remote.exists(), "No existe create_remote_repo.yml"
    assert sync_submodules.exists(), "No existe sync_submodules.yml"


def test_ci_contains_required_stages() -> None:
    ci_text = (PROJECT_ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")

    required_fragments = [
        "validate-and-test:",
        "security:",
        "--import-mode=importlib",
        "Validar marketplace",
        "Validar loader dinámico",
        "scripts/run_tests.ps1",
    ]

    for fragment in required_fragments:
        assert fragment in ci_text, f"No se encontró fragmento requerido en ci.yml: {fragment}"


def test_cd_contains_deploy_and_rollback() -> None:
    cd_text = (PROJECT_ROOT / ".github/workflows/cd.yml").read_text(encoding="utf-8")

    required_fragments = [
        "workflow_run:",
        "Deploy placeholder",
        "Rollback básico",
        "scripts/deploy.ps1",
        "-Rollback",
    ]

    for fragment in required_fragments:
        assert fragment in cd_text, f"No se encontró fragmento requerido en cd.yml: {fragment}"

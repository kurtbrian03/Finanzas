import re

def simulate_auto_keep(pr_body: str, changed_files: list, rules: dict):
    """
    Simula el comportamiento del script auto_keep_checklist.ps1.
    No ejecuta PowerShell; solo aplica reglas de mapeo tarea→archivo.
    """
    updated = pr_body.splitlines()

    for i, line in enumerate(updated):
        # Detectar casillas del checklist
        match = re.match(r"\s*-\s*\[( |x)\]\s*(.+)", line)
        if not match:
            continue

        checked, task = match.groups()
        task = task.strip()

        # Si ya está marcada, no tocar
        if checked == "x":
            continue

        # Si la tarea tiene reglas asociadas
        if task in rules:
            # Si alguno de los archivos modificados coincide
            if any(f in changed_files for f in rules[task]):
                updated[i] = f"- [x] {task}"

    return "\n".join(updated).strip()


def test_auto_keep_basic_mapping():
    pr_body = """
### Checklist
- [ ] Reforzar GitHub workflows
- [ ] Ajustar Azure y GitLab
- [ ] Completar ci_local y validaciones
- [ ] Ejecutar pruebas de integridad
"""

    changed_files = [
        ".github/workflows/ci.yml",
        "scripts/ci_local.ps1",
        "tests/test_ci_cd.py"
    ]

    rules = {
        "Reforzar GitHub workflows": [".github/workflows/ci.yml"],
        "Ajustar Azure y GitLab": ["azure-pipelines.yml", ".gitlab-ci.yml"],
        "Completar ci_local y validaciones": ["scripts/ci_local.ps1"],
        "Ejecutar pruebas de integridad": ["tests/test_ci_cd.py"]
    }

    result = simulate_auto_keep(pr_body, changed_files, rules)

    assert "- [x] Reforzar GitHub workflows" in result
    assert "- [ ] Ajustar Azure y GitLab" in result
    assert "- [x] Completar ci_local y validaciones" in result
    assert "- [x] Ejecutar pruebas de integridad" in result


def test_auto_keep_idempotent():
    pr_body = """
### Checklist
- [x] Reforzar GitHub workflows
- [ ] Ajustar Azure y GitLab
"""

    changed_files = [".github/workflows/ci.yml"]

    rules = {
        "Reforzar GitHub workflows": [".github/workflows/ci.yml"],
        "Ajustar Azure y GitLab": ["azure-pipelines.yml"]
    }

    result = simulate_auto_keep(pr_body, changed_files, rules)

    # No debe desmarcar nada
    assert "- [x] Reforzar GitHub workflows" in result
    # No debe marcar Azure porque no hubo cambios
    assert "- [ ] Ajustar Azure y GitLab" in result


def test_auto_keep_noop_when_no_rules_match():
    pr_body = """
### Checklist
- [ ] Reforzar GitHub workflows
- [ ] Ajustar Azure y GitLab
"""

    changed_files = ["README.md"]

    rules = {
        "Reforzar GitHub workflows": [".github/workflows/ci.yml"],
        "Ajustar Azure y GitLab": ["azure-pipelines.yml"]
    }

    result = simulate_auto_keep(pr_body, changed_files, rules)

    assert result == pr_body.strip()

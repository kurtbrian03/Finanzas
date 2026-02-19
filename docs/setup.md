# Setup de PINPON

## Scripts principales

- `init_project_structure.ps1`: crea estructura base y JSON de configuración mínimos.
- `setup_pinpon.ps1`: ejecuta setup integral.
- `rebuild_venv.ps1`: reconstruye `.venv`.
- `build_requirements.ps1`: regenera `requirements.txt`.

## Checks de entorno

- `check_python_version.ps1`
- `check_pip.ps1`
- `check_venv.ps1`

## Flujo recomendado

1. `pwsh ./init_project_structure.ps1`
2. `pwsh ./setup_pinpon.ps1 -Yes`
3. `pwsh ./validate_all.ps1`
4. `pwsh ./scripts/run_tests.ps1`

## Notas

- Todos los scripts usan `Set-StrictMode -Version Latest`.
- Todos retornan `exit 0`/`exit 1`.

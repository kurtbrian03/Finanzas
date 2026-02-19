# Estructura del Proyecto PINPON

## Carpetas núcleo

- `analysis/`: motores de análisis documental.
- `config/`: archivos JSON y parámetros de ejecución.
- `core/`: componentes centrales de flujo y estado.
- `downloads/`: descargas y empaquetado.
- `history/`: historial operativo.
- `ui/`: interfaz de usuario.
- `utils/`: utilidades Python.
- `validation/`: lógica de validación Python.

## Carpetas operativas

- `pinpon_modules/`: módulos ERP y extensiones.
- `scripts/`: scripts de mantenimiento CI/CD.
- `tests/`: pruebas automáticas.
- `docs/`: documentación técnica y funcional.
- `dist/`: artefactos de build.

## Archivos de automatización

- Workflows: `.github/workflows/ci.yml`, `.github/workflows/cd.yml`.
- Setup: `setup_pinpon.ps1`, `init_project_structure.ps1`.
- Validación: `validate_*.ps1`.
- Mantenimiento: `scripts/*.ps1`.

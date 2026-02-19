# PINPON · Plataforma Financiera Modular

PINPON es un proyecto financiero modular integrado en el repositorio Finanzas, con automatización completa de validación, pruebas, build y despliegue mediante CI/CD.

## Objetivos del proyecto

- Mantener la rama principal siempre en estado verde.
- Estandarizar setup, validación y mantenimiento.
- Garantizar trazabilidad operativa y reproducibilidad.
- Preparar despliegues controlados con rollback básico.

## Estructura principal

- `analysis/` análisis de documentos.
- `config/` configuración y credenciales.
- `core/` núcleo de ejecución.
- `docs/` documentación técnica.
- `pinpon_modules/` módulos funcionales.
- `scripts/` scripts de mantenimiento CI/CD.
- `tests/` pruebas automatizadas.

## Setup rápido

1. Inicializar estructura:
   - `pwsh ./init_project_structure.ps1`
2. Setup completo:
   - `pwsh ./setup_pinpon.ps1 -Yes`
3. Validación global:
   - `pwsh ./validate_all.ps1`
4. Pruebas:
   - `pwsh ./scripts/run_tests.ps1`

## Validadores soportados

- `validate_python.ps1`
- `validate_gmail_api.ps1`
- `validate_credentials.ps1`
- `validate_smtp.ps1`
- `validate_gmail_pinpon.ps1`
- `validate_folders.ps1`
- `validate_config.ps1`
- `validate_all.ps1`

### Claves de configuración requeridas

- `efirma_cer_path`
- `efirma_key_path`
- `efirma_password`
- `gmail_address`
- `gmail_app_password`
- `sat_password`
- `sat_rfc`

## CI/CD en PINPON

### CI (`.github/workflows/ci.yml`)

Se ejecuta en:

- `push` a cualquier rama.
- `pull_request` a `main`.

Etapas:

1. `build`
2. `validate`
3. `test`
4. `security`

### CD (`.github/workflows/cd.yml`)

Se ejecuta cuando CI finaliza exitosamente para `main`.

Etapas:

1. Build previo a release.
2. Publicación de artefacto.
3. Deploy placeholder.
4. Rollback básico en caso de fallo.

## Scripts de mantenimiento

- `scripts/build.ps1`
- `scripts/run_all_validators.ps1`
- `scripts/run_tests.ps1`
- `scripts/deploy.ps1`

## Generador de proyecto

`pinpon_new_project.ps1` permite crear desde cero una estructura PINPON completa con configuración base, scripts, documentación, pruebas y workflows.

## Pruebas automatizadas

- `tests/test_validadores.py`
- `tests/test_setup.py`
- `tests/test_ci_cd.py`

Ejecución:

- `python -m pytest -q tests`

## Documentación técnica

- `docs/estructura.md`
- `docs/validadores.md`
- `docs/setup.md`
- `docs/mantenimiento.md`
- `docs/arquitectura.md`
- `docs/ci_cd.md`

## Flujo recomendado de contribución

1. Crear rama de trabajo.
2. Ejecutar `validate_all.ps1` y pruebas.
3. Abrir PR hacia `main`.
4. Esperar CI en verde.
5. Merge.

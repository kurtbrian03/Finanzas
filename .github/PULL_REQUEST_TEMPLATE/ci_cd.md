## Tipo de cambio

Actualización de CI/CD (workflows, pipelines, scripts de runner o validaciones automáticas).

## Riesgos asociados

- Riesgo de romper pipelines en plataformas múltiples.
- Riesgo de falsos negativos/positivos en validaciones.
- Riesgo de degradación en tiempos de ejecución.

## Checklist específico

- [ ] Se validó sintaxis YAML de workflows/pipelines
- [ ] Se mantiene comportamiento no bloqueante en validaciones opcionales
- [ ] Se verificó matriz Windows/Linux
- [ ] No se removieron triggers críticos

## Validaciones obligatorias

- [ ] `tests/test_ci_cd.py` pasa
- [ ] `scripts/ci_local.ps1` pasa
- [ ] `pytest --import-mode=importlib -q` pasa

## Validaciones opcionales

- [ ] Validación manual de artefactos subidos en CI
- [ ] Revisión de logs para warnings nuevos

## Antes de solicitar revisión

- [ ] Se adjuntaron resultados relevantes de CI
- [ ] Se describió el impacto en PR

## Después de mergear

- [ ] Monitorear primeras ejecuciones de CI en `main`
- [ ] Confirmar que no aumentó tasa de fallos

# Mantenimiento PINPON

## Scripts operativos

- `scripts/build.ps1`: genera artefacto en `dist/`.
- `scripts/run_all_validators.ps1`: orquesta todos los validadores.
- `scripts/run_tests.ps1`: ejecuta suite de pruebas.
- `scripts/deploy.ps1`: deploy placeholder + rollback básico.

## Limpieza y recuperación

- `reset_pinpon.ps1 -Mode dry-run`: simula limpieza.
- `reset_pinpon.ps1 -Mode clean -Yes`: limpia salidas temporales.

## Recomendaciones

- Ejecutar validadores antes de cada push.
- No desplegar con validadores o pruebas en rojo.
- Conservar artefactos de build para trazabilidad.

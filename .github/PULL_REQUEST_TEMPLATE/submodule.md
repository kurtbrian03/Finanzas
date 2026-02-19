## Tipo de cambio

Cambios relacionados con submódulos Git (`.gitmodules`, sincronización, conversión y workflows asociados).

## Riesgos asociados

- Submódulos desalineados con referencias remotas.
- Árbol Git sucio o divergencias sin detectar.
- Fallos en sincronización diaria/manual.

## Checklist específico

- [ ] `.gitmodules` válido
- [ ] `git submodule status` limpio
- [ ] `convert_compras_to_submodule.ps1` funciona
- [ ] `sync_submodules.yml` no falla

## Validaciones obligatorias

- [ ] Paso de submódulos en CI pasa
- [ ] `scripts/ci_local.ps1` reporta validación de submódulos OK

## Validaciones opcionales

- [ ] Verificación manual `git submodule sync --recursive`
- [ ] Revisión de ahead/behind de submódulos

## Antes de solicitar revisión

- [ ] Se describió impacto en onboarding/repos clonados
- [ ] Se adjuntó evidencia de estado limpio

## Después de mergear

- [ ] Monitorear ejecución programada de sync
- [ ] Confirmar que no aparecen submódulos desincronizados

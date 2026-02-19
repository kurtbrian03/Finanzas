## Tipo de cambio

Cambios en el loader dinámico de módulos (`pinpon_modules/__init__.py` y estrategias de descubrimiento/carga).

## Riesgos asociados

- Fallos al cargar módulos por import path.
- Incompatibilidad con módulos pip o submódulos Git.
- Errores por módulos ausentes.

## Checklist específico

- [ ] Detecta módulos locales
- [ ] Detecta módulos pip
- [ ] Detecta submódulos Git
- [ ] Tolera módulos no existentes
- [ ] Tolera marketplace vacío

## Validaciones obligatorias

- [ ] Validación de loader en CI pasa
- [ ] `scripts/ci_local.ps1` pasa en sección loader
- [ ] No se rompen imports dinámicos existentes

## Validaciones opcionales

- [ ] Pruebas manuales con módulos instalados y no instalados
- [ ] Revisión de mensajes de error para claridad

## Antes de solicitar revisión

- [ ] Se documentó la estrategia de fallback
- [ ] Se incluyeron casos límite validados

## Después de mergear

- [ ] Monitorear carga de módulos en próximas PRs
- [ ] Ajustar reglas de descubrimiento si aparecen nuevos formatos

## Tipo de cambio

Cambios funcionales en módulos ERP (Compras/Ventas/Inventarios u otros futuros).

## Riesgos asociados

- Regresiones de lógica de negocio.
- Inconsistencias de persistencia/validación.
- Ruptura de integración con marketplace/loader.

## Checklist específico

- [ ] Se validó flujo principal del módulo
- [ ] Se validaron validadores y casos error
- [ ] Se validó persistencia local/JSON
- [ ] No se rompe integración con marketplace
- [ ] No se rompe carga dinámica del módulo

## Validaciones obligatorias

- [ ] Tests del módulo pasan
- [ ] `scripts/run_tests.ps1` pasa
- [ ] CI general de PR pasa

## Validaciones opcionales

- [ ] Prueba manual en Streamlit
- [ ] Validación de datos de ejemplo

## Antes de solicitar revisión

- [ ] Se documentó impacto funcional
- [ ] Se indicaron riesgos y mitigaciones

## Después de mergear

- [ ] Monitorear errores funcionales reportados
- [ ] Ajustar tests de regresión si aplica

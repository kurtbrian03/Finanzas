## Tipo de cambio

Cambios en marketplace ERP (`registry.json`, `installer.py`, `ui.py`, lógica de instalación/desinstalación/actualización).

## Riesgos asociados

- Inconsistencia de registro de módulos.
- Detección incorrecta de modos `none/local/pip/submodule`.
- Errores en flujo UI del marketplace.

## Checklist específico

- [ ] `registry.json` conserva estructura válida
- [ ] No hay IDs de módulos duplicados
- [ ] `installer.py` mantiene detección de modos
- [ ] `ui.py` renderiza sin excepciones

## Validaciones obligatorias

- [ ] `tests/test_marketplace.py` pasa
- [ ] Validación de marketplace en CI pasa
- [ ] Loader dinámico no falla en módulos instalados

## Validaciones opcionales

- [ ] Prueba manual de instalar/actualizar/desinstalar módulo
- [ ] Verificación de mensajes de estado en UI

## Antes de solicitar revisión

- [ ] Se listaron módulos impactados
- [ ] Se documentaron cambios de compatibilidad

## Después de mergear

- [ ] Verificar marketplace en entorno de integración
- [ ] Confirmar integridad de `registry.json`

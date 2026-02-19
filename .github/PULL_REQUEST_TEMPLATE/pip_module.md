## Tipo de cambio

Cambios de empaquetado/publicación pip (`pyproject.toml`, `setup.cfg`, build y publish scripts/workflows).

## Riesgos asociados

- Publicación fallida por metadatos inválidos.
- Ruptura por imports o estructura de paquete.
- Falta de idempotencia en publicación.

## Checklist específico

- [ ] `pyproject.toml` válido
- [ ] `setup.cfg` válido
- [ ] build local funciona
- [ ] `publish_pip_compras.ps1` idempotente
- [ ] No falla si versión ya existe

## Validaciones obligatorias

- [ ] Workflow de publish ejecuta sin errores estructurales
- [ ] Validación marketplace post-publish pasa

## Validaciones opcionales

- [ ] Prueba de instalación local de wheel
- [ ] Revisión de metadatos del paquete generado

## Antes de solicitar revisión

- [ ] Se indicó versión objetivo
- [ ] Se describió estrategia ante versión existente

## Después de mergear

- [ ] Verificar paquete en índice objetivo
- [ ] Confirmar instalación en entorno limpio

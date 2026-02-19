# Versiones de documentación

Este directorio mantiene snapshots de la documentación por versión.

## Estructura

- `v1/`, `v2/`, `v3/`: contenedores de snapshots documentales
- `latest/`: referencia documental activa
- `LATEST_VERSION.txt`: versión activa declarada

## Reglas

- Cambios mayores: crear nueva versión (`vN`)
- Cambios menores: registrar subversión en changelog (`vN.x`)
- Cambios de formato sin impacto estructural: no requieren versión mayor
- Cambios estructurales: actualizar `INDEX_DOCUMENTACION.md`

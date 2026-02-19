# Scripts de documentación

Este directorio contiene utilidades para regenerar y validar artefactos documentales.

## Script principal

- `regenerar_documentacion.py`

## Uso

```powershell
# Desde la raíz del repo
& "./.venv/Scripts/python.exe" docs/scripts/regenerar_documentacion.py --target all --validate

# Regenerar solo markdown
& "./.venv/Scripts/python.exe" docs/scripts/regenerar_documentacion.py --target markdown

# Registrar entrada en changelog
& "./.venv/Scripts/python.exe" docs/scripts/regenerar_documentacion.py --target html --log "Regeneración HTML"
```

## Objetivos

- Ejecución idempotente
- Regeneración por formato o global
- Validación de integridad de archivos mínimos
- Extensibilidad para nuevos formatos

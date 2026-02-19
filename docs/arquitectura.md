# Arquitectura Técnica PINPON

## Capas

1. **Presentación**: `ui/` y componentes Streamlit.
2. **Core**: `core/` para routing, estado y eventos.
3. **Dominio**: `pinpon_modules/` por módulo funcional.
4. **Análisis**: `analysis/` y extracción documental.
5. **Infra de scripts**: PowerShell para setup/validación/deploy.

## Diseño CI/CD

- CI: build → validate → test → security.
- CD: build release → deploy placeholder → rollback básico.

## Principios

- Rama principal siempre verde.
- Scripts autocontenidos, seguros y repetibles.
- Validación temprana de configuración.
- Trazabilidad por logs y artefactos.

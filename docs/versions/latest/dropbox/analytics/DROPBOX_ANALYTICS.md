# Analítica Documental Dropbox IA

Sistema analítico de documentos con clasificación técnica por tipo, árbol virtual reconstruido y reportes automáticos.

## Capacidades

- Métricas por tipo de archivo: `PDF`, `EXCEL`, `IMAGEN`, `TEXTO`, `ZIP`.
- Árbol virtual: `PROVEEDOR → AÑO → HOSPITAL → MES → ARCHIVOS`.
- Filtros virtuales en Streamlit por proveedor, año, hospital y mes.
- Reportes automáticos en `PDF`, `Excel`, `TXT`, `ZIP`.
- Snapshot analítico en `docs/versions/latest/dropbox/analytics/`.

## Módulos

- `dropbox_integration/analytics_engine.py`
- `dropbox_integration/folder_tree.py`
- `dropbox_integration/report_generator.py`
- `ui/layout.py` (explorador analítico y árbol virtual)

## Artefactos

- `docs/dropbox_analytics.json`
- `docs/dropbox_folder_tree.json`
- `docs/dropbox_analytics_summary.json`
- `docs/dropbox_file_metrics.json`
- `docs/dropbox_type_metrics.json`
- `docs/dropbox_hospital_metrics.json`
- `docs/dropbox_month_metrics.json`
- `docs/dropbox_analytics_reportes.json`

## Flags del pipeline

- `--audit-search`: activa la auditoría de búsqueda y exporta `*_audit.json` / `*_audit.csv`.
- Comportamiento por defecto: auditoría **desactivada**; se ejecuta solo con `--audit-search`.

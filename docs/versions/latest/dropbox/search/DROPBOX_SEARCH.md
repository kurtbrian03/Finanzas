# Búsqueda Avanzada Dropbox IA

Sistema documental avanzado con indexación, filtros, fuzzy search, búsqueda por contenido y búsqueda semántica TF‑IDF.

## Capacidades

- Búsqueda por nombre (exacta, parcial y difusa con `rapidfuzz`).
- Filtros por extensión, carpeta, tipo documental y etiquetas.
- Búsqueda por contenido en `PDF`, `TXT`, `MD`, `DOCX`.
- Ranking por score de relevancia y combinación de resultados.
- Búsqueda semántica local con `scikit-learn` (`TF-IDF` + coseno).
- Métricas de búsqueda en Streamlit y estadísticas en dashboard.

## Módulos principales

- `dropbox_integration/content_extractor.py`
- `dropbox_integration/search_engine.py`
- `dropbox_integration/lector_dropbox.py`
- `dropbox_integration/ai_classifier.py`
- `ui/layout.py` (pantalla `Dropbox IA`)
- `dropbox_integration/dashboard_documentos.py`

## Pruebas automatizadas

Ubicación: `tests/search/`

- `test_content_extractor.py`
- `test_search_engine_basico.py`
- `test_search_engine_contenido.py`
- `test_search_engine_semantico.py`
- `test_integracion_dropbox.py`
- `test_streamlit_dummy.py`

## Artefactos generados

- `docs/dropbox_search_stats.json`
- `docs/markdown/DROPBOX_SEARCH.md`
- `docs/versions/latest/dropbox/search/dropbox_search_stats.json`
- `docs/versions/latest/dropbox/search/DROPBOX_SEARCH.md`

# Manual Técnico para Desarrolladores

## 1. Descripción general del sistema

La aplicación es un sistema modular para visualización, análisis, validación fiscal y descarga controlada de documentos.

Principios de diseño:
- Arquitectura por responsabilidades.
- Flujo controlado por router.
- Estado centralizado con `StateManager`.
- Vistas previas en solo lectura.
- Descargas exclusivamente por acción manual.

## 2. Estructura del proyecto

- `app.py`: entrypoint mínimo.
- `core/`: estado, ciclo de vida, eventos y enrutamiento.
- `ui/`: navegación, layout y componentes visuales.
- `analysis/`: análisis PDF/Excel y extracción complementaria.
- `validation/`: validación RFC/Folio y reglas SAT.
- `downloads/`: indexación, filtros y empaquetado de descargas.
- `history/`: auditoría e historial.
- `config/`: constantes, settings y entorno.
- `utils/`: utilidades compartidas.
- `docs/`: arquitectura, roadmap y documentación técnica.

## 3. Cómo iniciar el proyecto

1) Activar entorno virtual:
- Windows PowerShell: `& .\.venv\Scripts\Activate.ps1`

2) Ejecutar la app:
- `python -m streamlit run .\app.py --server.port 8501`

3) Abrir en navegador:
- `http://localhost:8501`

## 4. Cómo agregar nuevas funcionalidades

### Regla de oro
Agregar en el módulo correcto, sin mezclar responsabilidades:
- UI en `ui/*`
- Lógica de negocio en `analysis|validation|downloads|history`
- Estado y navegación en `core/*`

### Pasos recomendados
1. Crear función en módulo de dominio.
2. Exponerla desde `ui/layout.py` en la pantalla correspondiente.
3. Registrar acción en historial con `history.history_manager.register_action`.
4. Validar ejecución y errores.

## 5. Extender análisis PDF/Excel

### PDF
- Agregar detectores en `analysis/entity_detector.py` o `analysis/tone_analyzer.py`.
- Integrar resultado en `analysis/pdf_analyzer.py`.
- Mostrar salida en `ui/components.py` (panel análisis PDF).

### Excel
- Agregar métricas en `analysis/excel_analyzer.py`.
- Mantener salida en estructura de diccionario estable.
- Renderizar en `ui/components.py` (panel análisis Excel).

## 6. Agregar nuevos métodos de descarga

1. Incorporar indexado/filtro en `downloads/download_filters.py`.
2. Ajustar empaquetado en `downloads/file_packager.py` si aplica.
3. Mantener botón manual con `downloads/downloader.py`.
4. Exponer flujo en `ui/layout.py` dentro de `render_downloads_page`.

## 7. Consistencia con StateManager y Router

- Toda pantalla se renderiza vía `core.router.dispatch`.
- No acceder a `st.session_state` directamente desde múltiples lugares si ya existe wrapper en `StateManager`.
- Mantener rutas en `config/constants.py` (`RUTAS_APP`).
- Registrar eventos relevantes con `core.event_bus.publish_event` cuando aplique.

## 8. Cómo evitar romper la arquitectura

- No introducir lógica de negocio en `app.py`.
- No acoplar módulos de análisis con componentes visuales.
- No duplicar validaciones entre `validation/*` y `analysis/*`.
- Evitar imports circulares (dependencias unidireccionales).

## 9. Depuración de errores

Checklist:
1. Revisar panel de errores de Streamlit y stacktrace.
2. Ejecutar `get_errors` en el workspace.
3. Confirmar imports y rutas de módulo.
4. Verificar que `StateManager.initialize()` se ejecute al inicio.
5. Aislar el módulo con fallo y validar con datos mínimos.

## 10. Pruebas unitarias (recomendación operativa)

Estrategia:
- Tests por módulo de dominio (`analysis`, `validation`, `downloads`).
- Smoke tests de router y layout principal.
- Fixtures con PDFs/Excels pequeños de prueba.

Sugerencia inicial:
- Framework: `pytest`.
- Estructura: `tests/analysis`, `tests/validation`, `tests/downloads`, `tests/core`.

## 11. Notas de compatibilidad

- La migración preserva comportamiento funcional previo.
- La interfaz y flujo principal se mantienen.
- Descargas continúan siendo manuales y controladas por botón.

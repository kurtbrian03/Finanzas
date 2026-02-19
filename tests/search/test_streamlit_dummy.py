import inspect

import ui.layout as layout


def test_layout_carga_sin_error() -> None:
    assert hasattr(layout, "render_dropbox_page")


def test_componentes_busqueda_en_layout() -> None:
    source = inspect.getsource(layout.render_dropbox_page)
    assert "Búsqueda avanzada" in source
    assert "Modo estricto (exacto + filtros)" in source
    assert "Modo flexible (híbrido avanzado)" in source
    assert "Búsqueda difusa" in source
    assert "Búsqueda por contenido" in source
    assert "Búsqueda semántica" in source
    assert "Ajustes de boosting contextual" in source
    assert "Mostrar auditoría avanzada" in source
    assert "Activar modo profiling" in source
    assert "Menú inteligente de facturas Aspel" in source
    assert "Validar Folio (SAT)" in source
    assert "Renombrado automático de imágenes" in source
    assert "Renombrar imágenes ahora" in source


def test_panel_auditoria_historica_en_layout() -> None:
    assert hasattr(layout, "_render_search_historical_panel")
    source = inspect.getsource(layout._render_search_historical_panel)
    assert "Auditoría histórica del motor de búsqueda" in source
    assert "Exportar diff JSON" in source
    assert "Exportar diff CSV" in source
    assert "Exportar diff TXT" in source


def test_panel_performance_en_layout() -> None:
    assert hasattr(layout, "_render_search_performance_panel")
    source = inspect.getsource(layout._render_search_performance_panel)
    assert "Perfil de performance del motor" in source
    assert "Exportar performance (JSON)" in source
    assert "Exportar performance (CSV)" in source

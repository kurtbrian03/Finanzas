"""Punto de entrada de la aplicación.

Responsabilidad:
- Inicializar ciclo de vida.
- Construir navegación.
- Delegar renderizado al router central.
"""

from pathlib import Path

from config.settings import APP_INFO
from core.lifecycle import bootstrap_app
from core.router import dispatch
from core.state_manager import StateManager
from ui.components import render_footer, render_top_bar
from ui.layout import (
    render_dropbox_explorer,
    render_dropbox_page,
    render_document_viewer,
    render_downloads_page,
    render_history_page,
    render_settings_page,
    render_validation_page,
)
from ui.dashboard_facturas_receptor import render_dashboard_facturas_receptor
from ui.messages import show_global_notice
from ui.navigation import render_sidebar
from ui.theme import apply_theme


def main() -> None:
    """Arranque principal del sistema."""
    state = StateManager()
    bootstrap_app(state)
    apply_theme()

    usuario, ruta, selected = render_sidebar()
    carpeta = Path(ruta)

    render_top_bar(usuario)
    show_global_notice()

    if not carpeta.exists() or not carpeta.is_dir():
        import streamlit as st

        st.error("La ruta FACTURACION no existe o no es válida.")
        render_footer(len(state.get("logs", [])), APP_INFO["version"])
        return

    handlers = {
        "viewer": lambda: render_document_viewer(state, carpeta),
        "dropbox": lambda: render_dropbox_page(state, carpeta),
        "dropbox_explorer": lambda: render_dropbox_explorer(state, carpeta),
        "receptor_dashboard": lambda: render_dashboard_facturas_receptor(carpeta_facturacion=carpeta, repo_root=Path(__file__).resolve().parent),
        "validation": lambda: render_validation_page(state),
        "downloads": lambda: render_downloads_page(state, carpeta),
        "history": lambda: render_history_page(state),
        "settings": lambda: render_settings_page(state),
    }

    dispatch(state, selected, handlers)
    render_footer(len(state.get("logs", [])), APP_INFO["version"])


if __name__ == "__main__":
    main()

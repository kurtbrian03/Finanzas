"""Funciones de ciclo de vida de aplicación.

Responsabilidad:
- Inicializar estado y configuración visual en el arranque.
"""

import streamlit as st

from config.settings import APP_INFO
from .state_manager import StateManager


def bootstrap_app(state: StateManager) -> None:
    """Configura página e inicializa estado base."""
    st.set_page_config(
        page_title=APP_INFO["page_title"],
        page_icon=APP_INFO["page_icon"],
        layout=APP_INFO["layout"],
    )
    state.initialize()

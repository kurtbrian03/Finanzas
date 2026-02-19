"""Router central de pantallas.

Responsabilidad:
- Mapear rutas de UI y despachar el módulo correspondiente.
"""

from __future__ import annotations

from typing import Callable

import streamlit as st

from config.constants import RUTAS_APP
from .event_bus import publish_event
from .state_manager import StateManager


def build_routes() -> dict[str, str]:
    """Retorna tabla de rutas canónica."""
    return RUTAS_APP.copy()


def dispatch(
    state: StateManager,
    selected_label: str,
    handlers: dict[str, Callable[[], None]],
) -> None:
    """Despacha navegación hacia handler registrado.

    Args:
        state: Gestor de estado.
        selected_label: Opción seleccionada en sidebar.
        handlers: Diccionario ruta->función render.
    """
    routes = build_routes()
    route_key = routes.get(selected_label)
    if route_key is None:
        st.error(f"Ruta no válida: {selected_label}")
        publish_event(state, "router_error", {"selected": selected_label})
        return

    handler = handlers.get(route_key)
    if handler is None:
        st.error(f"No existe handler para ruta: {route_key}")
        publish_event(state, "router_missing_handler", {"route": route_key})
        return

    publish_event(state, "route_change", {"route": route_key})
    handler()

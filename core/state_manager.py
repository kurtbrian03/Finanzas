"""Gestor centralizado de estado para Streamlit.

Responsabilidad:
- Inicializar y encapsular acceso a `st.session_state`.
- Proveer operaciones get/set y estructuras de logs/historial.
"""

from __future__ import annotations

from typing import Any

import streamlit as st

from config.settings import DEFAULT_CONFIG


class StateManager:
    """Encapsula operaciones sobre session_state para mantener consistencia."""

    def initialize(self) -> None:
        if "logs" not in st.session_state:
            st.session_state.logs = []
        if "historial" not in st.session_state:
            st.session_state.historial = []
        if "cfg" not in st.session_state:
            st.session_state.cfg = DEFAULT_CONFIG.copy()
        if "events" not in st.session_state:
            st.session_state.events = []
        if "flags" not in st.session_state:
            st.session_state.flags = {}
        if "errors" not in st.session_state:
            st.session_state.errors = []

    def get(self, key: str, default: Any = None) -> Any:
        return st.session_state.get(key, default)

    def set(self, key: str, value: Any) -> None:
        st.session_state[key] = value

    def append_log(self, item: dict[str, Any]) -> None:
        st.session_state.logs.append(item)
        st.session_state.historial.insert(0, item)

    def append_event(self, event: dict[str, Any]) -> None:
        st.session_state.events.append(event)

    def append_error(self, error: dict[str, Any]) -> None:
        st.session_state.errors.append(error)

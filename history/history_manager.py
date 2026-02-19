"""Gestor de historial y logs.

Responsabilidad:
- Registrar acciones del usuario de manera uniforme.
"""

from __future__ import annotations

from core.state_manager import StateManager
from .audit_log import build_record


def register_action(state: StateManager, accion: str, detalle: str) -> None:
    """Registra una acción en logs e historial."""
    state.append_log(build_record(accion, detalle))

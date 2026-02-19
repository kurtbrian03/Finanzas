"""Bus de eventos interno.

Responsabilidad:
- Registrar eventos de usuario y sistema sin acoplar módulos.
"""

from __future__ import annotations

from datetime import datetime

from .state_manager import StateManager


def publish_event(state: StateManager, event_type: str, payload: dict | None = None) -> None:
    """Publica un evento en el estado central.

    Args:
        state: Gestor de estado.
        event_type: Tipo de evento.
        payload: Datos adicionales.
    """
    state.append_event(
        {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "type": event_type,
            "payload": payload or {},
        }
    )

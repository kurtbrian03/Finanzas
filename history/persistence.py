"""Persistencia opcional de historial.

Responsabilidad:
- Guardar y cargar historial en JSON local cuando se requiera.
"""

from __future__ import annotations

import json
from pathlib import Path


def save_history(path: Path, items: list[dict]) -> None:
    """Guarda historial en disco en formato JSON."""
    path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")


def load_history(path: Path) -> list[dict]:
    """Carga historial desde disco; retorna lista vacía si no existe."""
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []

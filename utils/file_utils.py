"""Utilidades de archivo.

Responsabilidad:
- Operaciones de lectura segura y listado de archivos.
"""

from __future__ import annotations

from pathlib import Path


def read_text_safe(path: Path) -> str:
    """Lee texto con fallback de codificación."""
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="latin-1", errors="replace")
    except Exception:
        return ""


def file_size_kb(path: Path) -> float:
    """Retorna tamaño en KB."""
    return round(path.stat().st_size / 1024, 2)

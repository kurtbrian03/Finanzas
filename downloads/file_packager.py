"""Empaquetado de archivos para descargas masivas.

Responsabilidad:
- Construir ZIP en memoria sin modificar archivos fuente.
"""

from __future__ import annotations

import io
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


def construir_zip_memoria(paths: list[Path]) -> bytes:
    """Construye archivo ZIP en memoria con los paths indicados."""
    buffer = io.BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as zf:
        for path in paths:
            zf.writestr(path.name, path.read_bytes())
    return buffer.getvalue()

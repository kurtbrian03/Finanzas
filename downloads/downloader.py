"""Descarga controlada de archivos.

Responsabilidad:
- Exponer botones de descarga explícitos y mapear mime types.
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st


MIME_MAP = {
    ".pdf": "application/pdf",
    ".xml": "application/xml",
    ".zip": "application/zip",
    ".json": "application/json",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".xls": "application/vnd.ms-excel",
    ".txt": "text/plain",
    ".csv": "text/csv",
    ".py": "text/plain",
    ".ps1": "text/plain",
}


def mime_for(path: Path) -> str:
    """Retorna mime type en base a extensión."""
    return MIME_MAP.get(path.suffix.lower(), "application/octet-stream")


def descargar_archivo(path: Path, mime: str | None = None) -> None:
    """Renderiza botón de descarga controlada por usuario."""
    try:
        data = path.read_bytes()
    except Exception as error:
        st.error(f"No se pudo preparar la descarga: {error}")
        return
    st.download_button(
        label=f"Descargar {path.name}",
        data=data,
        file_name=path.name,
        mime=mime or mime_for(path),
        use_container_width=True,
    )

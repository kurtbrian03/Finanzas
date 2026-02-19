"""Utilidades de entorno y descubrimiento de rutas.

Responsabilidad:
- Detectar la ubicación probable de FACTURACION en entornos Windows comunes.
"""

from pathlib import Path


def detectar_carpeta_facturacion() -> Path:
    """Detecta la carpeta FACTURACION en rutas conocidas.

    Returns:
        Path: Ruta encontrada o primer candidato como fallback.
    """
    home = Path.home()
    candidatos = [
        home / "Dropbox" / "FACTURACION",
        home / "Documents" / "Dropbox" / "FACTURACION",
        home / "OneDrive" / "Dropbox" / "FACTURACION",
    ]
    for carpeta in candidatos:
        if carpeta.exists() and carpeta.is_dir():
            return carpeta
    return candidatos[0]

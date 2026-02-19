from __future__ import annotations

from datetime import datetime
import hashlib
from mimetypes import guess_type
from pathlib import Path
from typing import Callable
import os
import platform

from .content_extractor import extraer_texto_archivo

try:
    from PIL import Image
except Exception:
    Image = None

CARPETAS_FACTURACION = ["EXCEL", "JPG", "PDF", "POWERSHELL", "PYTHON", "TEXTO", "ZIPPED"]


def _calcular_sha256(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            sha.update(chunk)
    return sha.hexdigest()


def _metadatos_imagen(path: Path) -> dict[str, object]:
    if Image is None or path.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
        return {"image_width": None, "image_height": None, "image_mode": None, "image_format": None}
    try:
        with Image.open(path) as img:
            return {
                "image_width": int(img.width),
                "image_height": int(img.height),
                "image_mode": str(img.mode),
                "image_format": str(img.format or ""),
            }
    except Exception:
        return {"image_width": None, "image_height": None, "image_mode": None, "image_format": None}


def detectar_ruta_dropbox() -> Path:
    """Detecta ruta Dropbox local por sistema operativo."""
    home = Path.home()
    if platform.system().lower().startswith("win"):
        return Path("C:/Pinpon/Dropbox/DocumentacionApp/FACTURACION")
    return home / "Dropbox" / "DocumentacionApp" / "FACTURACION"


def _log(msg: str, logger: Callable[[str], None] | None) -> None:
    if logger:
        logger(msg)


def leer_dropbox_recursivo(
    carpeta_facturacion: Path | str,
    logger: Callable[[str], None] | None = print,
) -> list[dict[str, object]]:
    """Lee recursivamente FACTURACION y retorna metadatos por archivo."""
    base = Path(carpeta_facturacion)
    if not base.exists() or not base.is_dir():
        raise FileNotFoundError(f"Ruta FACTURACION inválida: {base}")

    resultados: list[dict[str, object]] = []
    errores = 0

    for carpeta in CARPETAS_FACTURACION:
        carpeta_path = base / carpeta
        _log(f"Leyendo carpeta: {carpeta_path}", logger)
        if not carpeta_path.exists() or not carpeta_path.is_dir():
            continue

        for path in carpeta_path.rglob("*"):
            if not path.is_file():
                continue

            try:
                _log(f"Leyendo archivo: {path}", logger)
                stat = path.stat()
                mime = guess_type(path.name)[0] or "application/octet-stream"
                file_hash = _calcular_sha256(path)
                _log(f"Hash generado: {path.name}", logger)
                contenido = extraer_texto_archivo(path)
                if contenido:
                    _log(f"Contenido extraído: {path.name}", logger)
                registro = {
                    "nombre_archivo": path.name,
                    "ruta_completa": str(path.resolve()),
                    "extension": path.suffix.lower(),
                    "carpeta": carpeta,
                    "tamaño": stat.st_size,
                    "fecha_modificacion": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
                    "mime": mime,
                    "sha256": file_hash,
                    "hash": file_hash,
                    "contenido_extraido": contenido,
                    "etiquetas": [],
                }
                registro.update(_metadatos_imagen(path))
                resultados.append(registro)
                _log(f"Archivo detectado: {path.name}", logger)
            except PermissionError:
                errores += 1
                _log(f"Error permisos: {path}", logger)
            except OSError as error:
                errores += 1
                _log(f"Error archivo corrupto/inaccesible: {path} ({error})", logger)
            except Exception as error:
                errores += 1
                _log(f"Error inesperado en archivo: {path} ({error})", logger)

    _log(f"Total de archivos encontrados: {len(resultados)}", logger)
    if errores:
        _log(f"Total de archivos con error: {errores}", logger)
    return resultados


def leer_dropbox_desde_entorno(logger: Callable[[str], None] | None = print) -> list[dict[str, object]]:
    """Lee FACTURACION usando ruta detectada o variable DROPBOX_FACTURACION_PATH."""
    ruta_env = os.getenv("DROPBOX_FACTURACION_PATH", "").strip()
    ruta = Path(ruta_env) if ruta_env else detectar_ruta_dropbox()
    return leer_dropbox_recursivo(ruta, logger=logger)

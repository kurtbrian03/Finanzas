from __future__ import annotations

import logging
import re
from pathlib import Path

try:
    import pymupdf as fitz  # type: ignore
except Exception:
    fitz = None

try:
    from docx import Document  # type: ignore
except Exception:
    Document = None

logger = logging.getLogger(__name__)
_EXT_PERMITIDAS = {".pdf", ".txt", ".md", ".docx"}
_MAX_CHARS = 60000


def _leer_pdf(path: Path) -> str:
    if fitz is None:
        return ""
    try:
        logger.info("Extrayendo contenido de PDF: %s", path)
        doc = fitz.open(path)
        texto = "\n".join(str(page.get_text("text")) for page in doc)
        doc.close()
        return texto
    except Exception as error:
        logger.warning("No se pudo extraer PDF %s: %s", path, error)
        return ""


def _leer_txt_md(path: Path) -> str:
    try:
        logger.info("Extrayendo contenido de TXT/MD: %s", path)
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception as error:
        logger.warning("No se pudo leer TXT/MD %s: %s", path, error)
        return ""


def _leer_docx(path: Path) -> str:
    if Document is None:
        return ""
    try:
        logger.info("Extrayendo contenido de DOCX: %s", path)
        doc = Document(str(path))
        return "\n".join(p.text for p in doc.paragraphs)
    except Exception as error:
        logger.warning("No se pudo extraer DOCX %s: %s", path, error)
        return ""


def limpiar_texto(texto: str) -> str:
    base = texto.replace("\r", "\n").lower()
    base = "".join(ch if ch.isprintable() or ch in "\n\t" else " " for ch in base)
    base = re.sub(r"\n+", "\n", base)
    base = re.sub(r"\s+", " ", base)
    return base.strip()


def extraer_texto_archivo(ruta: str | Path) -> str:
    """API principal solicitada para extraer contenido textual de un archivo."""
    try:
        contenido = extraer_contenido_archivo(ruta)
        if not contenido:
            logger.info("Archivo sin contenido: %s", ruta)
        return contenido
    except Exception as error:
        logger.error("Error extrayendo contenido: %s", error)
        return ""


def extraer_contenido_archivo(ruta: Path | str, max_chars: int = _MAX_CHARS) -> str:
    path = Path(ruta)
    if not path.exists() or not path.is_file():
        logger.warning("Archivo inexistente o inválido: %s", path)
        return ""
    ext = path.suffix.lower()
    if ext not in _EXT_PERMITIDAS:
        return ""

    if ext == ".pdf":
        contenido = _leer_pdf(path)
    elif ext in {".txt", ".md"}:
        contenido = _leer_txt_md(path)
    elif ext == ".docx":
        contenido = _leer_docx(path)
    else:
        contenido = ""

    limpio = limpiar_texto(contenido)
    if not limpio:
        logger.info("Archivo sin contenido: %s", path)
    return limpio[: max(0, int(max_chars))]

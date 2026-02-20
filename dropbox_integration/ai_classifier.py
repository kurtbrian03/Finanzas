from __future__ import annotations

from pathlib import Path
from typing import Any
import re

try:
    import pymupdf as fitz  # type: ignore
except Exception:
    fitz = None

import numpy as np


def _leer_texto_txt_md(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def _leer_texto_pdf(path: Path) -> str:
    if fitz is None:
        return ""
    try:
        doc = fitz.open(path)
        texto = "\n".join(str(page.get_text("text")) for page in doc)
        doc.close()
        return texto
    except Exception:
        return ""


def _leer_texto_docx(path: Path) -> str:
    try:
        import zipfile
        import re

        with zipfile.ZipFile(path, "r") as docx:
            xml = docx.read("word/document.xml").decode("utf-8", errors="ignore")
        return re.sub(r"<[^>]+>", " ", xml)
    except Exception:
        return ""


def extraer_texto(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in {".txt", ".md"}:
        return _leer_texto_txt_md(path)
    if ext == ".pdf":
        return _leer_texto_pdf(path)
    if ext == ".docx":
        return _leer_texto_docx(path)
    return ""


def sugerir_con_ia(registro: dict[str, Any]) -> dict[str, str]:
    """Clasificador IA placeholder basado en heurísticas de contenido."""
    nombre = str(registro.get("nombre_archivo", "")).lower()
    texto = str(registro.get("texto_extraido", "")).lower()
    base = f"{nombre} {texto}"[:20000]

    if any(k in base for k in ["contrato", "legal", "juridico"]):
        return {"categoria_sugerida": "Legal", "etiqueta_sugerida": "legal", "modulo_sugerido": "validation/legal/"}
    if any(k in base for k in ["manual", "guia", "instrucciones"]):
        return {
            "categoria_sugerida": "Manual de Usuario",
            "etiqueta_sugerida": "manual",
            "modulo_sugerido": "docs/manuales/",
        }
    if any(k in base for k in ["arquitectura", "diseño", "diagrama"]):
        return {
            "categoria_sugerida": "Arquitectura",
            "etiqueta_sugerida": "arquitectura",
            "modulo_sugerido": "analysis/",
        }
    return {
        "categoria_sugerida": "Documento Técnico",
        "etiqueta_sugerida": "tecnico",
        "modulo_sugerido": "analysis/",
    }


def enriquecer_con_ia(registros: list[dict[str, Any]]) -> list[dict[str, Any]]:
    salida: list[dict[str, Any]] = []
    for item in registros:
        path = Path(str(item.get("ruta_completa", "")))
        texto = extraer_texto(path) if path.exists() else ""
        sugerencia = sugerir_con_ia({**item, "texto_extraido": texto})
        nuevo = dict(item)
        nuevo["texto_extraido_preview"] = texto[:600]
        nuevo.update(sugerencia)
        salida.append(nuevo)
    return salida


def _tokenizar(texto: str) -> list[str]:
    return [t for t in re.split(r"\W+", texto.lower()) if t]


def generar_embeddings(texto: str) -> np.ndarray:
    """Genera embedding local de un texto usando hashing de tokens."""
    dim = 512
    vec = np.zeros(dim, dtype=float)
    tokens = _tokenizar(texto)
    if not tokens:
        return vec
    for tok in tokens:
        vec[hash(tok) % dim] += 1.0
    norm = float(np.linalg.norm(vec))
    if norm > 0:
        vec = vec / norm
    return vec


def generar_embeddings_lote(textos: list[str]) -> dict[str, np.ndarray]:
    """Compatibilidad: genera embeddings por lote indexados por posición."""
    return {str(i): generar_embeddings(texto) for i, texto in enumerate(textos)}


def _embedding_query(query: str, dim: int) -> np.ndarray:
    tokens = _tokenizar(query)
    vec = np.zeros(dim, dtype=float)
    if not tokens:
        return vec
    for tok in tokens:
        slot = hash(tok) % dim
        vec[slot] += 1.0
    norm = float(np.linalg.norm(vec))
    if norm > 0:
        vec = vec / norm
    return vec


def buscar_similares(query: str, documentos: list[dict[str, Any]], top_k: int = 20) -> list[dict[str, Any]]:
    """Busca documentos similares por coseno contra embeddings disponibles."""
    if not documentos:
        return []

    primer_vector = documentos[0].get("embedding")
    if not isinstance(primer_vector, np.ndarray) or primer_vector.size == 0:
        primer_vector = documentos[0].get("vector")
    if not isinstance(primer_vector, np.ndarray) or primer_vector.size == 0:
        primer_vector = generar_embeddings(query)

    q_vec = _embedding_query(query, int(primer_vector.size)) if isinstance(primer_vector, np.ndarray) else generar_embeddings(query)
    if float(np.linalg.norm(q_vec)) == 0.0:
        return []

    resultados: list[dict[str, Any]] = []
    for item in documentos:
        vec = item.get("embedding")
        if not isinstance(vec, np.ndarray) or vec.size != q_vec.size:
            vec = item.get("vector")
        if not isinstance(vec, np.ndarray) or vec.size != q_vec.size:
            continue
        score = float(np.dot(q_vec, vec))
        if score > 0:
            resultados.append({"id": item.get("id"), "doc": item.get("doc"), "score": score})

    return sorted(resultados, key=lambda x: float(x.get("score", 0.0)), reverse=True)[: max(1, int(top_k))]

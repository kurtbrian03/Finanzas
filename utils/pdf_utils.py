"""Utilidades específicas de PDF.

Responsabilidad:
- Tokenización y extracción base de expresiones en texto PDF.
"""

from __future__ import annotations

import re


def limpiar_tokens(texto: str) -> list[str]:
    """Limpia tokens para análisis estadístico básico."""
    tokens = [re.sub(r"[^a-zA-ZáéíóúÁÉÍÓÚñÑ0-9]", "", t).lower() for t in texto.split()]
    stop = {
        "de", "la", "el", "y", "en", "a", "que", "los", "las", "por", "con", "para",
        "del", "al", "se", "es", "un", "una", "o", "su", "sus", "como", "más", "menos",
    }
    return [t for t in tokens if len(t) > 3 and t not in stop and not t.isnumeric()]

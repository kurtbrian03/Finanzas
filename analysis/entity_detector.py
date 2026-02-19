"""Detección heurística de entidades.

Responsabilidad:
- Extraer personas, organizaciones, fechas, ubicaciones, montos e identificadores.
"""

from __future__ import annotations

import re


def extraer_entidades(texto: str) -> dict[str, list[str]]:
    """Extrae entidades relevantes de texto libre."""
    fechas = re.findall(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", texto)
    montos = re.findall(r"\$?\s?\d{1,3}(?:[,.]\d{3})*(?:[.,]\d{2})", texto)
    uuids = re.findall(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b", texto)
    rfcs = re.findall(r"\b[A-ZÑ&]{3,4}\d{6}[A-Z0-9]{3}\b", texto.upper())
    organizaciones = re.findall(r"\b[A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\s]{3,}(?:S\.A\.?\sDE\sC\.V\.?|SA\sDE\sCV|S\.?\sDE\sR\.L\.?)\b", texto.upper())
    personas = re.findall(r"\b[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\s[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)?\b", texto)
    ubicaciones = re.findall(r"\b(Ciudad de\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+|[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+,\s*[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)\b", texto)
    return {
        "Personas": sorted(list(set(personas)))[:15],
        "Organizaciones": sorted(list(set(organizaciones)))[:15],
        "Fechas": sorted(list(set(fechas)))[:20],
        "Ubicaciones": sorted(list(set(ubicaciones)))[:20],
        "Montos": sorted(list(set(montos)))[:20],
        "Identificadores": sorted(list(set(uuids + rfcs)))[:25],
    }

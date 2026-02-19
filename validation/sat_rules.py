"""Reglas SAT para RFC.

Responsabilidad:
- Definir patrones y validaciones básicas del estándar RFC.
"""

from __future__ import annotations

import re
from datetime import date, datetime


RFC_PATTERN = re.compile(r"^[A-ZÑ&]{3,4}\d{6}[A-Z0-9]{3}$")
HOMOCLAVE_PATTERN = re.compile(r"^[A-Z0-9]{3}$")


def validar_estructura_rfc(rfc: str) -> bool:
    """Valida patrón estructural RFC."""
    return bool(RFC_PATTERN.match(rfc))


def extraer_fecha_rfc(rfc: str) -> date | None:
    """Extrae y valida fecha interna del RFC."""
    fecha_txt = rfc[4:10] if len(rfc) == 13 else rfc[3:9]
    yy = int(fecha_txt[:2])
    mm = int(fecha_txt[2:4])
    dd = int(fecha_txt[4:6])
    anio_actual = datetime.now().year % 100
    anio = 2000 + yy if yy <= anio_actual else 1900 + yy
    try:
        return date(anio, mm, dd)
    except ValueError:
        return None


def validar_homoclave_sat(homoclave: str) -> bool:
    """Valida homoclave por regla SAT simplificada."""
    return bool(HOMOCLAVE_PATTERN.match(homoclave))

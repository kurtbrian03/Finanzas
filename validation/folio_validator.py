"""Validación de folio fiscal (UUID)."""

from __future__ import annotations

import re


def validar_folio(folio: str) -> tuple[bool, str]:
    """Valida estructura UUID de folio fiscal."""
    patron_uuid = r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
    if re.match(patron_uuid, folio.strip()):
        return True, "Folio fiscal válido por estructura UUID."
    return False, "Folio fiscal inválido. Debe cumplir estructura UUID estándar."

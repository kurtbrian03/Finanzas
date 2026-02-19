"""Motor de validación de homoclave.

Responsabilidad:
- Encapsular validación de homoclave para RFC.
"""

from .sat_rules import validar_homoclave_sat


def validar_homoclave(rfc: str) -> bool:
    """Valida últimos 3 caracteres del RFC."""
    return validar_homoclave_sat(rfc[-3:])

"""Validador integral RFC.

Responsabilidad:
- Realizar validación estructural SAT con salida detallada y reglas especiales.
"""

from __future__ import annotations

from config.constants import RFC_AUTORIZADOS
from .homoclave_engine import validar_homoclave
from .sat_rules import extraer_fecha_rfc, validar_estructura_rfc


def validar_rfc(rfc: str) -> dict[str, object]:
    """Valida RFC y retorna diagnóstico detallado."""
    rfc = rfc.strip().upper()
    detalles: list[str] = []
    sugerencias: list[str] = []

    if rfc in RFC_AUTORIZADOS:
        return {
            "valido": True,
            "rfc": rfc,
            "detalles": ["RFC autorizado especial: válido por política interna."],
            "observaciones": ["Se omiten bloqueos adicionales por excepción autorizada."],
            "motivos": [],
            "sugerencias": [],
        }

    if len(rfc) not in (12, 13):
        return {
            "valido": False,
            "rfc": rfc,
            "motivos": ["Longitud inválida: debe tener 12 (moral) o 13 (física)."],
            "sugerencias": ["Ejemplo válido persona física: GODE561231GR8", "Ejemplo válido persona moral: ABC9901011A0"],
            "detalles": [],
            "observaciones": [],
        }

    if not validar_estructura_rfc(rfc):
        return {
            "valido": False,
            "rfc": rfc,
            "motivos": ["Estructura inválida conforme al patrón SAT (prefijo+fecha+homoclave)."],
            "sugerencias": ["Usa solo letras válidas, fecha YYMMDD y homoclave alfanumérica."],
            "detalles": [],
            "observaciones": [],
        }

    fecha = extraer_fecha_rfc(rfc)
    if fecha is None:
        return {
            "valido": False,
            "rfc": rfc,
            "motivos": ["La fecha dentro del RFC no es válida."],
            "sugerencias": ["Verifica mes, día y año en el bloque YYMMDD."],
            "detalles": [],
            "observaciones": [],
        }
    detalles.append(f"Fecha interna válida: {fecha.isoformat()}.")

    if not validar_homoclave(rfc):
        return {
            "valido": False,
            "rfc": rfc,
            "motivos": ["Homoclave inválida: requiere 3 caracteres alfanuméricos."],
            "sugerencias": ["Asegura que los últimos 3 caracteres sean letras o números."],
            "detalles": detalles,
            "observaciones": [],
        }

    detalles.extend([
        "Longitud correcta.",
        "Estructura general SAT válida.",
        "Caracteres permitidos válidos.",
    ])

    observaciones = [
        "Validación contra lista autorizada: no listado especial; validación estructural aprobada.",
        "Resultado apto para uso operativo con revisión documental complementaria.",
    ]

    return {
        "valido": True,
        "rfc": rfc,
        "motivos": [],
        "sugerencias": sugerencias,
        "detalles": detalles,
        "observaciones": observaciones,
    }

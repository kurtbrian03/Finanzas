"""Análisis de tono y propósito documental.

Responsabilidad:
- Inferir enfoque (legal/financiero/técnico/informativo) y formalidad.
"""


def analizar_tono_y_proposito(texto: str, cantidad_encabezados: int) -> tuple[str, str]:
    """Retorna enfoque principal y propósito estimado."""
    lower = texto.lower()
    legal = sum(k in lower for k in ["contrato", "cláusula", "legal", "firma"])
    financiero = sum(k in lower for k in ["factura", "importe", "saldo", "pago", "iva", "cfdi"])
    tecnico = sum(k in lower for k in ["sistema", "versión", "proceso", "técnico", "archivo"])
    informativo = sum(k in lower for k in ["informe", "resumen", "nota", "comunicado"])
    mapa = {
        "legal": legal,
        "financiero": financiero,
        "técnico": tecnico,
        "informativo": informativo,
    }
    enfoque = max(mapa, key=mapa.get) if any(mapa.values()) else "informativo"
    formalidad = "alta" if cantidad_encabezados > 5 else "media"
    proposito = f"Documento con enfoque {enfoque} y nivel de formalidad {formalidad}."
    return enfoque, proposito

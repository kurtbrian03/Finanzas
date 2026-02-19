from __future__ import annotations

import re


def _contains(text: str, *tokens: str) -> bool:
    lower = text.lower()
    return any(token.lower() in lower for token in tokens)


def classify_invoice_provider(
    text: str,
    xml_payload: dict[str, object] | None = None,
    file_name: str = "",
) -> str:
    """Clasifica proveedor de factura: Aspel/Facturama/Facture/Contpaqi/Otros."""
    source_text = f"{file_name}\n{text}".lower()
    xml_payload = xml_payload or {}
    xml_text = str(xml_payload).lower()

    if _contains(source_text, "aspel", "cfdi") or _contains(xml_text, "aspel"):
        return "Aspel"

    if _contains(source_text, "facturama") or _contains(xml_text, "facturama"):
        return "Facturama"

    if _contains(source_text, "facture") or _contains(xml_text, "facture"):
        return "Facture"

    if _contains(source_text, "contpaqi", "contpaqi") or _contains(xml_text, "contpaqi", "www.sat.gob.mx/cfd"):
        if _contains(source_text, "contpaqi") or _contains(xml_text, "contpaqi"):
            return "Contpaqi"

    if _contains(source_text, "cfdi", "factura"):
        return "Otros"

    return "Otros"


def classify_receptor_bucket(
    rfc_receptor: str,
    text: str,
) -> str:
    """Clasifica receptor para tablero ejecutivo."""
    base = f"{rfc_receptor} {text}".lower()
    if "ag distribuidora" in base or "ag_distribuidora" in base:
        return "AG DISTRIBUIDORA"
    if "medbright" in base:
        return "MEDBRIGHT"
    return "OTROS"

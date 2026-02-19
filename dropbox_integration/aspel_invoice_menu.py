from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from analysis.cfdi_xml_extractor import extract_cfdi_from_pdf
from dropbox_integration.content_extractor import extraer_contenido_archivo
from dropbox_integration.invoice_provider_classifier import classify_invoice_provider

_ASPEL_HINTS = ("aspel", "cfdi", "factura")
_RFC_RE = re.compile(r"\b[A-ZÑ&]{3,4}\d{6}[A-Z0-9]{3}\b", re.IGNORECASE)
_UUID_RE = re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b")
_TOTAL_RE = re.compile(r"\btotal\s*[:=]?\s*\$?\s*([0-9][0-9,]*(?:\.\d{1,2})?)\b", re.IGNORECASE)
_FECHA_RE = re.compile(r"\b(\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}|\d{2}/\d{2}/\d{4})\b")


def _to_total_str(value: object) -> str:
    try:
        return f"{float(str(value).replace(',', '').strip()):.2f}"
    except Exception:
        return ""


def _is_aspel_invoice(pdf: str | Path | dict[str, object]) -> bool:
    if isinstance(pdf, dict):
        name = str(pdf.get("nombre_archivo", "")).lower()
        contenido = str(pdf.get("contenido_extraido", "")).lower()
        ext = str(pdf.get("extension", "")).lower()
        if ext != ".pdf":
            return False
        hay_hint = any(hint in name or hint in contenido for hint in _ASPEL_HINTS)
        return hay_hint

    path = Path(pdf)
    if path.suffix.lower() != ".pdf":
        return False
    text = extraer_contenido_archivo(path).lower()
    return any(hint in path.name.lower() or hint in text for hint in _ASPEL_HINTS)


def _extract_invoice_metadata(pdf: str | Path | dict[str, object]) -> dict[str, object]:
    if isinstance(pdf, dict):
        path = Path(str(pdf.get("ruta_completa", "")))
        contenido = str(pdf.get("contenido_extraido", ""))
        proveedor = str(pdf.get("proveedor_virtual", ""))
    else:
        path = Path(pdf)
        contenido = extraer_contenido_archivo(path)
        proveedor = ""

    xml_data = extract_cfdi_from_pdf(path)

    rfcs = _RFC_RE.findall(contenido)
    uuid_regex = _UUID_RE.search(contenido)
    total_regex = _TOTAL_RE.search(contenido)
    fecha_regex = _FECHA_RE.search(contenido)

    uuid = str(xml_data.get("uuid", "") or (uuid_regex.group(0) if uuid_regex else "")).strip()
    rfc_emisor = str(xml_data.get("rfc_emisor", "") or (rfcs[0] if len(rfcs) >= 1 else "")).upper()
    rfc_receptor = str(xml_data.get("rfc_receptor", "") or (rfcs[1] if len(rfcs) >= 2 else "")).upper()
    total = _to_total_str(xml_data.get("total", "") or (total_regex.group(1) if total_regex else ""))
    fecha = str(xml_data.get("fecha", "") or (fecha_regex.group(1) if fecha_regex else ""))
    proveedor_detectado = classify_invoice_provider(
        text=contenido,
        xml_payload=xml_data,
        file_name=path.name,
    )

    return {
        "nombre_archivo": path.name,
        "ruta": str(path),
        "proveedor": proveedor,
        "proveedor_detectado": proveedor_detectado,
        "fecha": fecha,
        "total": total,
        "uuid": uuid,
        "rfc_emisor": rfc_emisor,
        "rfc_receptor": rfc_receptor,
        "xml_source": str(xml_data.get("source", "none")),
    }


def _find_pdf_invoices(root: str | Path | list[dict[str, object]]) -> list[dict[str, object]]:
    if isinstance(root, list):
        rows = [r for r in root if isinstance(r, dict) and _is_aspel_invoice(r)]
        out: list[dict[str, object]] = []
        for row in rows:
            out.append(_extract_invoice_metadata(row))
        return out

    path = Path(root)
    if not path.exists():
        return []

    out: list[dict[str, object]] = []
    for pdf in sorted(path.rglob("*.pdf")):
        if _is_aspel_invoice(pdf):
            out.append(_extract_invoice_metadata(pdf))
    return out

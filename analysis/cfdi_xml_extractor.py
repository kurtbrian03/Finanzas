from __future__ import annotations

import re
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

from dropbox_integration.content_extractor import extraer_contenido_archivo

try:
    import fitz  # type: ignore
except Exception:
    fitz = None

_UUID_RE = re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b")
_RFC_RE = re.compile(r"\b[A-ZÑ&]{3,4}\d{6}[A-Z0-9]{3}\b", re.IGNORECASE)
_TOTAL_RE = re.compile(r"\btotal\s*[:=]?\s*\$?\s*([0-9][0-9,]*(?:\.\d{1,2})?)\b", re.IGNORECASE)
_FECHA_RE = re.compile(r"\b(\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}|\d{2}/\d{2}/\d{4})\b")


def _local_name(tag: str) -> str:
    if "}" in tag:
        return tag.split("}", 1)[1]
    if ":" in tag:
        return tag.split(":", 1)[1]
    return tag


def _attr_by_local(attrib: dict[str, str], key: str) -> str:
    for raw_key, value in attrib.items():
        if _local_name(str(raw_key)).lower() == key.lower():
            return str(value)
    return ""


def _parse_cfdi_xml_text(xml_text: str) -> dict[str, object]:
    try:
        root = ET.fromstring(xml_text)
    except Exception:
        return {}

    comprobante = root
    if _local_name(root.tag).lower() != "comprobante":
        for node in root.iter():
            if _local_name(node.tag).lower() == "comprobante":
                comprobante = node
                break

    timbre_node = None
    for node in root.iter():
        if _local_name(node.tag).lower() == "timbrefiscaldigital":
            timbre_node = node
            break

    uuid = ""
    if timbre_node is not None:
        uuid = _attr_by_local(dict(timbre_node.attrib), "UUID")

    emisor_rfc = ""
    receptor_rfc = ""
    for node in root.iter():
        local = _local_name(node.tag).lower()
        if local == "emisor" and not emisor_rfc:
            emisor_rfc = _attr_by_local(dict(node.attrib), "Rfc")
        elif local == "receptor" and not receptor_rfc:
            receptor_rfc = _attr_by_local(dict(node.attrib), "Rfc")

    total = _attr_by_local(dict(comprobante.attrib), "Total")
    fecha = _attr_by_local(dict(comprobante.attrib), "Fecha")

    version = _attr_by_local(dict(comprobante.attrib), "Version") or _attr_by_local(dict(comprobante.attrib), "version")

    return {
        "uuid": uuid,
        "rfc_emisor": emisor_rfc,
        "rfc_receptor": receptor_rfc,
        "total": total,
        "fecha": fecha,
        "timbre_fiscal": uuid,
        "cfdi_version": version,
        "source": "xml",
    }


def _xml_candidates_from_pdf(path: Path) -> list[str]:
    if fitz is None:
        return []
    candidates: list[str] = []
    try:
        doc = fitz.open(path)
        if hasattr(doc, "xref_xml_metadata"):
            try:
                xref = int(doc.xref_xml_metadata())
                if xref > 0:
                    xmp = doc.xref_stream(xref)
                    if isinstance(xmp, (bytes, bytearray)):
                        candidates.append(bytes(xmp).decode("utf-8", errors="ignore"))
            except Exception:
                pass

        for xref in range(1, int(doc.xref_length())):
            try:
                stream = doc.xref_stream(xref)
            except Exception:
                continue
            if not isinstance(stream, (bytes, bytearray)):
                continue
            text = bytes(stream).decode("utf-8", errors="ignore")
            if "<?xml" in text or "<cfdi:Comprobante" in text or "<Comprobante" in text:
                candidates.append(text)
        doc.close()
    except Exception:
        return []

    return candidates


def _normalize_total(text: str) -> str:
    cleaned = str(text or "").replace(",", "").strip()
    try:
        return f"{float(cleaned):.2f}"
    except Exception:
        return ""


def extract_cfdi_from_pdf(pdf_path: str | Path) -> dict[str, object]:
    """Extrae CFDI incrustado desde PDF Aspel con fallback a regex sobre texto."""
    path = Path(pdf_path)
    base: dict[str, object] = {
        "uuid": "",
        "rfc_emisor": "",
        "rfc_receptor": "",
        "total": "",
        "fecha": "",
        "timbre_fiscal": "",
        "cfdi_version": "",
        "source": "none",
    }

    candidates = _xml_candidates_from_pdf(path)
    for candidate in candidates:
        start = candidate.find("<?xml")
        xml_text = candidate[start:] if start >= 0 else candidate
        parsed = _parse_cfdi_xml_text(xml_text)
        if parsed and parsed.get("uuid"):
            parsed["total"] = _normalize_total(str(parsed.get("total", "")))
            return {**base, **parsed}

    texto = extraer_contenido_archivo(path)
    if not texto:
        return base

    uuid_match = _UUID_RE.search(texto)
    rfcs = _RFC_RE.findall(texto)
    total_match = _TOTAL_RE.search(texto)
    fecha_match = _FECHA_RE.search(texto)

    return {
        **base,
        "uuid": uuid_match.group(0) if uuid_match else "",
        "rfc_emisor": rfcs[0].upper() if len(rfcs) >= 1 else "",
        "rfc_receptor": rfcs[1].upper() if len(rfcs) >= 2 else "",
        "total": _normalize_total(total_match.group(1) if total_match else ""),
        "fecha": fecha_match.group(1) if fecha_match else "",
        "timbre_fiscal": uuid_match.group(0) if uuid_match else "",
        "source": "text_regex",
    }

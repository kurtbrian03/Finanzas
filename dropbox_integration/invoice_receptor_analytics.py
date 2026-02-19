from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from pathlib import Path

from dropbox_integration.aspel_invoice_menu import _extract_invoice_metadata
from dropbox_integration.invoice_provider_classifier import classify_receptor_bucket


def _month_key(fecha: str) -> str:
    raw = str(fecha or "").strip()
    if not raw:
        return "Sin fecha"
    for fmt in ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y", "%Y-%m-%d"]:
        try:
            dt = datetime.strptime(raw, fmt)
            return dt.strftime("%Y-%m")
        except Exception:
            continue
    return raw[:7]


def build_invoices_dataset(registros: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for reg in registros:
        if str(reg.get("extension", "")).lower() != ".pdf":
            continue
        contenido = str(reg.get("contenido_extraido", ""))
        if "factura" not in contenido.lower() and "cfdi" not in contenido.lower():
            continue
        meta = _extract_invoice_metadata(reg)
        bucket = classify_receptor_bucket(str(meta.get("rfc_receptor", "")), contenido)
        meta["receptor_bucket"] = bucket
        meta["proveedor_detectado"] = str(meta.get("proveedor_detectado", "Otros"))
        rows.append(meta)
    return rows


def summarize_by_receptor(rows: list[dict[str, object]]) -> dict[str, object]:
    totals = defaultdict(float)
    counts = defaultdict(int)
    monthly = defaultdict(lambda: defaultdict(float))

    for row in rows:
        receptor = str(row.get("receptor_bucket", "OTROS"))
        try:
            total = float(str(row.get("total", "0") or "0"))
        except Exception:
            total = 0.0
        month = _month_key(str(row.get("fecha", "")))

        totals[receptor] += total
        counts[receptor] += 1
        monthly[receptor][month] += total

    return {
        "totals": {k: round(v, 2) for k, v in totals.items()},
        "counts": dict(counts),
        "monthly": {k: {m: round(v, 2) for m, v in months.items()} for k, months in monthly.items()},
    }

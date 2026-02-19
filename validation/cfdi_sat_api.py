from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from hashlib import sha1
from typing import Any
from urllib.parse import urlencode
from urllib.request import urlopen


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _estado_mock(uuid: str, rfc_emisor: str, rfc_receptor: str, total: str) -> tuple[str, str]:
    if not uuid or not rfc_emisor or not rfc_receptor:
        return "no_encontrado", "Parámetros incompletos para validación CFDI."

    key = f"{uuid}|{rfc_emisor}|{rfc_receptor}|{total}".encode("utf-8", errors="ignore")
    bucket = int(sha1(key).hexdigest(), 16) % 10
    if bucket <= 6:
        return "vigente", "CFDI localizado con estatus vigente."
    if bucket <= 8:
        return "cancelado", "CFDI localizado con estatus cancelado."
    return "no_encontrado", "CFDI no localizado en consulta simulada."


def _normalize_total(total: object) -> str:
    try:
        return f"{float(str(total).replace(',', '').strip()):.2f}"
    except Exception:
        return "0.00"


def _validate_cfdi_sat(
    uuid: str,
    rfc_emisor: str,
    rfc_receptor: str,
    total: object,
    timeout: float = 10.0,
) -> dict[str, object]:
    """Valida CFDI en SAT (modo mock por defecto, modo http opcional por entorno)."""
    uuid_clean = str(uuid or "").strip()
    emisor_clean = str(rfc_emisor or "").strip().upper()
    receptor_clean = str(rfc_receptor or "").strip().upper()
    total_clean = _normalize_total(total)

    mode = str(os.getenv("CFDI_SAT_MODE", "mock")).strip().lower()
    endpoint = str(os.getenv("CFDI_SAT_ENDPOINT", "")).strip()

    base_payload: dict[str, object] = {
        "uuid": uuid_clean,
        "rfc_emisor": emisor_clean,
        "rfc_receptor": receptor_clean,
        "total": total_clean,
        "fecha_consulta": _now_iso(),
        "provider": mode,
    }

    if mode != "http":
        estado, mensaje = _estado_mock(uuid_clean, emisor_clean, receptor_clean, total_clean)
        return {**base_payload, "estado": estado, "mensaje": mensaje, "raw": {}}

    if not endpoint:
        return {
            **base_payload,
            "estado": "no_encontrado",
            "mensaje": "CFDI_SAT_ENDPOINT no configurado para modo http.",
            "raw": {},
        }

    try:
        query = urlencode(
            {
                "uuid": uuid_clean,
                "rfc_emisor": emisor_clean,
                "rfc_receptor": receptor_clean,
                "total": total_clean,
            }
        )
        with urlopen(f"{endpoint}?{query}", timeout=timeout) as response:
            raw_text = response.read().decode("utf-8", errors="ignore")
        raw_json = json.loads(raw_text) if raw_text else {}
        if not isinstance(raw_json, dict):
            raw_json = {}

        estado = str(raw_json.get("estado", raw_json.get("status", "no_encontrado"))).strip().lower() or "no_encontrado"
        mensaje = str(raw_json.get("mensaje", raw_json.get("message", "Sin mensaje"))).strip()

        return {
            **base_payload,
            "estado": estado,
            "mensaje": mensaje,
            "raw": raw_json,
        }
    except Exception as error:
        return {
            **base_payload,
            "estado": "no_encontrado",
            "mensaje": f"Error consultando API SAT: {error}",
            "raw": {},
        }


def validate_cfdi_sat(
    uuid: str,
    rfc_emisor: str,
    rfc_receptor: str,
    total: object,
    timeout: float = 10.0,
) -> dict[str, object]:
    """Alias público para validación CFDI SAT."""
    return _validate_cfdi_sat(uuid, rfc_emisor, rfc_receptor, total, timeout=timeout)

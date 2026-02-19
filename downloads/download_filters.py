"""Indexación y filtros para descargas fiscales.

Responsabilidad:
- Indexar documentos descargables.
- Aplicar filtros por fecha, RFC, UUID, monto, tipo y extensión.
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from config.constants import TIPOS_DESCARGA


@st.cache_data(show_spinner=False)
def indexar_documentos(carpeta_base: str) -> list[dict[str, object]]:
    """Indexa documentos en carpeta base según extensiones permitidas."""
    base = Path(carpeta_base)
    if not base.exists() or not base.is_dir():
        return []

    docs: list[dict[str, object]] = []
    uuid_pat = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")
    rfc_pat = re.compile(r"[A-ZÑ&]{3,4}\d{6}[A-Z0-9]{3}")
    monto_pat = re.compile(r"\d{1,3}(?:[,.]\d{3})*(?:[.,]\d{2})")

    for path in base.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TIPOS_DESCARGA:
            continue
        name_upper = path.name.upper()
        uuids = uuid_pat.findall(name_upper)
        rfcs = rfc_pat.findall(name_upper)
        montos = monto_pat.findall(path.name)
        tipo = "OTRO"
        for marker in ["I", "E", "T", "N", "P"]:
            if f"_{marker}_" in name_upper or name_upper.startswith(f"{marker}_"):
                tipo = marker
                break

        docs.append(
            {
                "path": str(path),
                "archivo": path.name,
                "extension": path.suffix.lower(),
                "tamano_kb": round(path.stat().st_size / 1024, 2),
                "fecha_mod": datetime.fromtimestamp(path.stat().st_mtime).date().isoformat(),
                "rfc_emisor": rfcs[0] if len(rfcs) > 0 else "",
                "rfc_receptor": rfcs[1] if len(rfcs) > 1 else "",
                "uuid": uuids[0] if uuids else "",
                "monto": montos[0] if montos else "",
                "tipo_comprobante": tipo,
            }
        )
    return docs


def aplicar_filtros(
    df: pd.DataFrame,
    rango: tuple,
    rfc_emisor: str,
    rfc_receptor: str,
    uuid: str,
    folio: str,
    monto: str,
    tipo: str,
    ext: list[str],
) -> pd.DataFrame:
    """Aplica filtros acumulativos al dataframe indexado."""
    filtrado = df.copy()
    if isinstance(rango, tuple) and len(rango) == 2:
        ini, fin = rango
        fechas = pd.to_datetime(filtrado["fecha_mod"]).dt.date
        filtrado = filtrado[(fechas >= ini) & (fechas <= fin)]

    if rfc_emisor:
        filtrado = filtrado[filtrado["rfc_emisor"].str.contains(rfc_emisor.upper(), na=False)]
    if rfc_receptor:
        filtrado = filtrado[filtrado["rfc_receptor"].str.contains(rfc_receptor.upper(), na=False)]
    if uuid:
        filtrado = filtrado[filtrado["uuid"].str.contains(uuid, case=False, na=False)]
    if folio:
        filtrado = filtrado[filtrado["uuid"].str.contains(folio, case=False, na=False)]
    if monto:
        filtrado = filtrado[filtrado["monto"].str.contains(monto, na=False)]
    if tipo != "TODOS":
        filtrado = filtrado[filtrado["tipo_comprobante"] == tipo]
    if ext:
        filtrado = filtrado[filtrado["extension"].isin(ext)]
    return filtrado

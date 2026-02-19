from __future__ import annotations

from collections import Counter
from pathlib import Path
import re
from typing import Any, cast

MESES = {
    "enero": "01",
    "febrero": "02",
    "marzo": "03",
    "abril": "04",
    "mayo": "05",
    "junio": "06",
    "julio": "07",
    "agosto": "08",
    "septiembre": "09",
    "setiembre": "09",
    "octubre": "10",
    "noviembre": "11",
    "diciembre": "12",
}

_GENERICOS = {
    "facturacion",
    "pdf",
    "excel",
    "texto",
    "python",
    "powershell",
    "zipped",
    "jpg",
    "imagenes",
    "otros",
}


def _to_int(valor: object, default: int = 0) -> int:
    try:
        return int(valor)  # type: ignore[arg-type]
    except Exception:
        return default


def _limpiar_token(valor: str) -> str:
    limpio = re.sub(r"[_\-]+", " ", valor).strip()
    return re.sub(r"\s+", " ", limpio)


def extraer_contexto_virtual(ruta_archivo: str | Path) -> dict[str, str]:
    ruta = Path(ruta_archivo)
    tokens = []
    for p in ruta.parts:
        token = _limpiar_token(str(p))
        if not token:
            continue
        if re.match(r"^[a-zA-Z]:\\?$", token):
            continue
        tokens.append(token)
    tokens_lower = [t.lower() for t in tokens]

    year = "SIN_AÑO"
    month = "SIN_MES"
    provider = "SIN_PROVEEDOR"
    hospital = "SIN_HOSPITAL"

    for t in tokens_lower:
        m = re.search(r"(19\d{2}|20\d{2})", t)
        if m:
            year = m.group(1)
            break

    for t in tokens_lower:
        if t in MESES:
            month = f"{MESES[t]}-{t.title()}"
            break
        m_num = re.search(r"\b(0?[1-9]|1[0-2])\b", t)
        if m_num and month == "SIN_MES":
            month = f"{int(m_num.group(1)):02d}"

    for i, t in enumerate(tokens_lower):
        if "hospital" in t or "clinica" in t:
            hospital = tokens[i]
            break

    if hospital == "SIN_HOSPITAL" and year != "SIN_AÑO":
        for i, t in enumerate(tokens_lower):
            if year in t and i + 1 < len(tokens) and tokens_lower[i + 1] not in _GENERICOS:
                hospital = tokens[i + 1]
                break

    for t, original in zip(tokens_lower, tokens):
        if t in _GENERICOS:
            continue
        if year in t or t in MESES:
            continue
        if "hospital" in t or "clinica" in t:
            continue
        provider = original
        break

    return {
        "proveedor": provider,
        "anio": year,
        "hospital": hospital,
        "mes": month,
    }


def construir_arbol_virtual(registros: list[dict[str, object]]) -> dict[str, object]:
    root: dict[str, Any] = {
        "nombre": "FACTURACION",
        "tipo": "folder",
        "path": "FACTURACION",
        "children": {},
        "stats": {"archivos": 0, "tamano_bytes": 0},
    }

    for item in registros:
        ruta = str(item.get("ruta_completa", "")).strip()
        if not ruta:
            continue

        contexto = extraer_contexto_virtual(ruta)
        item["proveedor_virtual"] = contexto["proveedor"]
        item["anio_virtual"] = contexto["anio"]
        item["hospital_virtual"] = contexto["hospital"]
        item["mes_virtual"] = contexto["mes"]

        niveles = [
            contexto["proveedor"],
            contexto["anio"],
            contexto["hospital"],
            contexto["mes"],
        ]

        nodo: dict[str, Any] = root
        for nivel in niveles:
            hijos = cast(dict[str, Any], nodo.setdefault("children", {}))
            if nivel not in hijos:
                hijos[nivel] = {
                    "nombre": nivel,
                    "tipo": "folder",
                    "path": f"{nodo.get('path', '')}/{nivel}".strip("/"),
                    "children": {},
                    "stats": {"archivos": 0, "tamano_bytes": 0},
                }
            nodo = hijos[nivel]
            nodo["stats"]["archivos"] = int(nodo["stats"].get("archivos", 0)) + 1
            nodo["stats"]["tamano_bytes"] = int(nodo["stats"].get("tamano_bytes", 0)) + _to_int(item.get("tamaño", 0), 0)

        archivos = cast(list[dict[str, Any]], nodo.setdefault("files", []))
        archivos.append(
            {
                "nombre": str(item.get("nombre_archivo", "")),
                "ruta": ruta,
                "extension": str(item.get("extension", "")).lower(),
                "categoria": str(item.get("categoria", "")),
                "tamano": _to_int(item.get("tamaño", 0), 0),
                "fecha": str(item.get("fecha_modificacion", "")),
            }
        )

        root_stats = cast(dict[str, Any], root["stats"])
        root_stats["archivos"] = int(root_stats.get("archivos", 0)) + 1
        root_stats["tamano_bytes"] = int(root_stats.get("tamano_bytes", 0)) + _to_int(item.get("tamaño", 0), 0)

    return cast(dict[str, object], root)


def aplicar_filtros_virtuales(
    registros: list[dict[str, object]],
    proveedor: str = "TODOS",
    anio: str = "TODOS",
    hospital: str = "TODOS",
    mes: str = "TODOS",
) -> list[dict[str, object]]:
    salida = registros
    if proveedor != "TODOS":
        salida = [r for r in salida if str(r.get("proveedor_virtual", "")) == proveedor]
    if anio != "TODOS":
        salida = [r for r in salida if str(r.get("anio_virtual", "")) == anio]
    if hospital != "TODOS":
        salida = [r for r in salida if str(r.get("hospital_virtual", "")) == hospital]
    if mes != "TODOS":
        salida = [r for r in salida if str(r.get("mes_virtual", "")) == mes]
    return salida


def opciones_filtros_virtuales(registros: list[dict[str, object]]) -> dict[str, list[str]]:
    return {
        "proveedores": sorted({str(r.get("proveedor_virtual", "SIN_PROVEEDOR")) for r in registros}),
        "anios": sorted({str(r.get("anio_virtual", "SIN_AÑO")) for r in registros}),
        "hospitales": sorted({str(r.get("hospital_virtual", "SIN_HOSPITAL")) for r in registros}),
        "meses": sorted({str(r.get("mes_virtual", "SIN_MES")) for r in registros}),
    }


def breadcrumbs_virtuales(registro: dict[str, object]) -> str:
    return " / ".join(
        [
            str(registro.get("proveedor_virtual", "SIN_PROVEEDOR")),
            str(registro.get("anio_virtual", "SIN_AÑO")),
            str(registro.get("hospital_virtual", "SIN_HOSPITAL")),
            str(registro.get("mes_virtual", "SIN_MES")),
        ]
    )


def resumen_arbol(arbol: dict[str, object]) -> dict[str, object]:
    proveedores = Counter()
    hospitales = Counter()
    meses = Counter()

    children_root = cast(dict[str, Any], arbol.get("children", {}))
    for proveedor, p_nodo in children_root.items():
        proveedores[proveedor] += int(p_nodo.get("stats", {}).get("archivos", 0))
        for _anio, y_nodo in p_nodo.get("children", {}).items():
            for hospital, h_nodo in y_nodo.get("children", {}).items():
                hospitales[hospital] += int(h_nodo.get("stats", {}).get("archivos", 0))
                for mes, m_nodo in h_nodo.get("children", {}).items():
                    meses[mes] += int(m_nodo.get("stats", {}).get("archivos", 0))

    stats_root = cast(dict[str, Any], arbol.get("stats", {}))
    return {
        "total_archivos": int(stats_root.get("archivos", 0)),
        "proveedores_top": dict(proveedores.most_common(10)),
        "hospitales_top": dict(hospitales.most_common(10)),
        "meses_top": dict(meses.most_common(12)),
    }

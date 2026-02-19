from __future__ import annotations

from collections import Counter
from datetime import datetime
from typing import Any


def calcular_metricas(registros: list[dict[str, Any]]) -> dict[str, Any]:
    """Calcula métricas y estadísticas de documentos indexados."""
    total = len(registros)
    por_tipo = Counter(str(r.get("categoria", "Sin clasificar")) for r in registros)
    por_carpeta = Counter(str(r.get("carpeta", "")) for r in registros)
    por_extension = Counter(str(r.get("extension", "")) for r in registros)
    tam_total = sum(int(r.get("tamaño", 0) or 0) for r in registros)

    orden_fecha = sorted(
        registros,
        key=lambda r: str(r.get("fecha_modificacion", "")),
        reverse=True,
    )
    orden_tamano = sorted(
        registros,
        key=lambda r: int(r.get("tamaño", 0) or 0),
        reverse=True,
    )

    return {
        "total_archivos": total,
        "por_tipo": dict(por_tipo),
        "por_carpeta": dict(por_carpeta),
        "por_extension": dict(por_extension),
        "tamano_total_bytes": tam_total,
        "mas_recientes": orden_fecha[:10],
        "mas_pesados": orden_tamano[:10],
    }


def bytes_humanos(valor: int) -> str:
    unidad = ["B", "KB", "MB", "GB", "TB"]
    n = float(valor)
    i = 0
    while n >= 1024 and i < len(unidad) - 1:
        n /= 1024
        i += 1
    return f"{n:,.2f} {unidad[i]}"

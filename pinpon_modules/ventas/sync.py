"""Hooks de sincronización futura ERP para el módulo de Ventas."""

from __future__ import annotations

from typing import Any


def exportar_facturas_a_erp(facturas: list[dict[str, Any]], erp_target: str) -> dict[str, Any]:
    """Placeholder para exportar facturas emitidas a ERP externo."""
    return {
        "ok": False,
        "erp_target": erp_target,
        "count": len(facturas),
        "message": "Integración ERP no implementada aún.",
    }


def importar_clientes_desde_erp(erp_target: str) -> dict[str, Any]:
    """Placeholder para importar clientes desde ERP externo."""
    return {
        "ok": False,
        "erp_target": erp_target,
        "data": [],
        "message": "Integración ERP no implementada aún.",
    }


def exportar_cobranza_a_erp(cobranzas: list[dict[str, Any]], erp_target: str) -> dict[str, Any]:
    """Placeholder para exportar cobranza hacia ERP externo."""
    return {
        "ok": False,
        "erp_target": erp_target,
        "count": len(cobranzas),
        "message": "Integración ERP no implementada aún.",
    }

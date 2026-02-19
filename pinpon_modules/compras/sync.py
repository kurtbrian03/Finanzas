"""Puntos de extensión para sincronización ERP externa del módulo Compras."""

from __future__ import annotations

from typing import Any


def exportar_ordenes_compra_a_erp(ordenes: list[dict[str, Any]], erp_target: str) -> dict[str, Any]:
    """Placeholder para exportar órdenes de compra hacia ERP externo.

    Args:
        ordenes: Colección de órdenes de compra normalizadas desde PINPON.
        erp_target: Identificador del ERP destino (ej. sap-b1, contpaqi, aspel).

    Returns:
        Estructura estándar de respuesta para implementar integración real.
    """
    return {
        "ok": False,
        "erp_target": erp_target,
        "count": len(ordenes),
        "message": "Integración ERP no implementada aún.",
    }


def importar_ordenes_compra_desde_erp(erp_target: str) -> dict[str, Any]:
    """Placeholder para importar órdenes de compra desde ERP externo."""
    return {
        "ok": False,
        "erp_target": erp_target,
        "data": [],
        "message": "Integración ERP no implementada aún.",
    }


def exportar_cxp_a_erp(cuentas_por_pagar: list[dict[str, Any]], erp_target: str) -> dict[str, Any]:
    """Placeholder para exportar cuentas por pagar hacia ERP externo."""
    return {
        "ok": False,
        "erp_target": erp_target,
        "count": len(cuentas_por_pagar),
        "message": "Integración ERP no implementada aún.",
    }


def importar_proveedores_desde_erp(erp_target: str) -> dict[str, Any]:
    """Placeholder para importar catálogo de proveedores desde ERP externo."""
    return {
        "ok": False,
        "erp_target": erp_target,
        "data": [],
        "message": "Integración ERP no implementada aún.",
    }

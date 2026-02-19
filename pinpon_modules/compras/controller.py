"""Controlador de integración UI ↔ servicios para el módulo de Compras."""

from __future__ import annotations

from typing import Any

from .services import ComprasService
from .validators import (
    validar_cuenta_por_pagar,
    validar_orden_compra,
    validar_proveedor,
    validar_recepcion,
)


class ComprasController:
    def __init__(self, service: ComprasService | None = None) -> None:
        self.service = service or ComprasService()

    def crear_proveedor_desde_form(self, **datos: Any) -> dict[str, Any]:
        errores = validar_proveedor(datos)
        if errores:
            return {"ok": False, "errors": errores, "data": None}
        proveedor = self.service.crear_proveedor(**datos)
        return {"ok": True, "errors": [], "data": proveedor, "message": "Proveedor creado correctamente."}

    def crear_oc_desde_form(self, **datos: Any) -> dict[str, Any]:
        errores = validar_orden_compra(datos)
        if errores:
            return {"ok": False, "errors": errores, "data": None}
        try:
            oc = self.service.crear_orden_compra(**datos)
        except ValueError as error:
            return {"ok": False, "errors": [str(error)], "data": None}
        return {"ok": True, "errors": [], "data": oc, "message": "Orden de compra creada correctamente."}

    def registrar_recepcion_desde_form(self, **datos: Any) -> dict[str, Any]:
        errores = validar_recepcion(datos)
        if errores:
            return {"ok": False, "errors": errores, "data": None}
        try:
            recepcion = self.service.registrar_recepcion(**datos)
        except ValueError as error:
            return {"ok": False, "errors": [str(error)], "data": None}
        return {"ok": True, "errors": [], "data": recepcion, "message": "Recepción registrada correctamente."}

    def generar_cxp_desde_oc(self, orden_compra_id: int, fecha_vencimiento: str, monto: float | None = None) -> dict[str, Any]:
        datos = {
            "proveedor_id": 1,
            "orden_compra_id": orden_compra_id,
            "monto": monto if monto is not None else 1,
            "fecha_vencimiento": fecha_vencimiento,
        }
        errores = validar_cuenta_por_pagar(datos)
        if errores:
            return {"ok": False, "errors": errores, "data": None}
        try:
            cxp = self.service.generar_cuenta_por_pagar(
                orden_compra_id=orden_compra_id,
                fecha_vencimiento=fecha_vencimiento,
                monto=monto,
            )
        except ValueError as error:
            return {"ok": False, "errors": [str(error)], "data": None}
        return {"ok": True, "errors": [], "data": cxp, "message": "Cuenta por pagar generada correctamente."}

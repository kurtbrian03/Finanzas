"""Controller de alto nivel para UI del módulo de Ventas."""

from __future__ import annotations

from typing import Any

from .services import VentasService
from .validators import (
    validar_cliente,
    validar_cobranza,
    validar_cotizacion,
    validar_factura_emitida,
    validar_pedido,
)


class VentasController:
    def __init__(self, service: VentasService | None = None) -> None:
        self.service = service or VentasService()

    def crear_cliente_desde_form(self, **datos: Any) -> dict[str, Any]:
        errores = validar_cliente(datos)
        if errores:
            return {"ok": False, "errors": errores, "data": None}
        cliente = self.service.crear_cliente(**datos)
        return {"ok": True, "errors": [], "data": cliente, "message": "Cliente creado correctamente."}

    def crear_cotizacion_desde_form(self, **datos: Any) -> dict[str, Any]:
        errores = validar_cotizacion(datos)
        if errores:
            return {"ok": False, "errors": errores, "data": None}
        try:
            cotizacion = self.service.crear_cotizacion(**datos)
        except ValueError as error:
            return {"ok": False, "errors": [str(error)], "data": None}
        return {"ok": True, "errors": [], "data": cotizacion, "message": "Cotización creada correctamente."}

    def crear_pedido_desde_form(self, **datos: Any) -> dict[str, Any]:
        errores = validar_pedido(datos)
        if errores:
            return {"ok": False, "errors": errores, "data": None}
        cotizacion_id = int(datos.get("cotizacion_id", 0) or 0)
        try:
            if cotizacion_id > 0:
                pedido = self.service.convertir_cotizacion_a_pedido(
                    cotizacion_id=cotizacion_id,
                    fecha=str(datos.get("fecha", "")).strip() or None,
                )
            else:
                raise ValueError("Para crear pedido desde form se requiere cotizacion_id válido.")
        except ValueError as error:
            return {"ok": False, "errors": [str(error)], "data": None}
        return {"ok": True, "errors": [], "data": pedido, "message": "Pedido creado correctamente."}

    def registrar_factura_desde_form(self, **datos: Any) -> dict[str, Any]:
        errores = validar_factura_emitida(datos)
        if errores:
            return {"ok": False, "errors": errores, "data": None}
        try:
            factura = self.service.registrar_factura_emitida(**datos)
        except ValueError as error:
            return {"ok": False, "errors": [str(error)], "data": None}
        return {"ok": True, "errors": [], "data": factura, "message": "Factura emitida registrada correctamente."}

    def registrar_cobranza_desde_form(self, **datos: Any) -> dict[str, Any]:
        errores = validar_cobranza(datos)
        if errores:
            return {"ok": False, "errors": errores, "data": None}
        try:
            cobranza = self.service.registrar_cobranza(**datos)
        except ValueError as error:
            return {"ok": False, "errors": [str(error)], "data": None}
        return {"ok": True, "errors": [], "data": cobranza, "message": "Cobranza registrada correctamente."}

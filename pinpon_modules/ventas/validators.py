"""Validaciones del módulo de Ventas."""

from __future__ import annotations

import re
from typing import Any


RFC_PATTERN = re.compile(r"^[A-Z&Ñ]{3,4}\d{6}[A-Z0-9]{3}$")


def validar_cliente(datos: dict[str, Any]) -> list[str]:
    errores: list[str] = []
    if not str(datos.get("nombre", "")).strip():
        errores.append("El nombre del cliente es obligatorio.")

    rfc = str(datos.get("rfc", "")).strip().upper()
    if not rfc:
        errores.append("El RFC del cliente es obligatorio.")
    elif not RFC_PATTERN.match(rfc):
        errores.append("El RFC del cliente no tiene un formato válido.")

    email = str(datos.get("email", "")).strip()
    if email and "@" not in email:
        errores.append("El email del cliente no es válido.")
    return errores


def validar_cotizacion(datos: dict[str, Any]) -> list[str]:
    errores: list[str] = []
    if int(datos.get("cliente_id", 0) or 0) <= 0:
        errores.append("cliente_id es obligatorio para cotización.")
    if not str(datos.get("fecha", "")).strip():
        errores.append("La fecha de cotización es obligatoria.")
    if float(datos.get("total", 0) or 0) <= 0:
        errores.append("El total de la cotización debe ser mayor a 0.")
    return errores


def validar_pedido(datos: dict[str, Any]) -> list[str]:
    errores: list[str] = []
    if int(datos.get("cliente_id", 0) or 0) <= 0:
        errores.append("cliente_id es obligatorio para pedido.")
    if not str(datos.get("fecha", "")).strip():
        errores.append("La fecha del pedido es obligatoria.")
    if float(datos.get("total", 0) or 0) <= 0:
        errores.append("El total del pedido debe ser mayor a 0.")
    return errores


def validar_factura_emitida(datos: dict[str, Any]) -> list[str]:
    errores: list[str] = []
    if int(datos.get("pedido_id", 0) or 0) <= 0:
        errores.append("pedido_id es obligatorio para factura emitida.")
    if int(datos.get("cliente_id", 0) or 0) <= 0:
        errores.append("cliente_id es obligatorio para factura emitida.")
    if not str(datos.get("fecha", "")).strip():
        errores.append("La fecha de factura es obligatoria.")
    if float(datos.get("total", 0) or 0) <= 0:
        errores.append("El total de la factura emitida debe ser mayor a 0.")
    return errores


def validar_cobranza(datos: dict[str, Any]) -> list[str]:
    errores: list[str] = []
    if int(datos.get("factura_id", 0) or 0) <= 0:
        errores.append("factura_id es obligatorio para cobranza.")
    if not str(datos.get("fecha", "")).strip():
        errores.append("La fecha de cobranza es obligatoria.")
    if float(datos.get("monto", 0) or 0) <= 0:
        errores.append("El monto de cobranza debe ser mayor a 0.")
    if not str(datos.get("metodo_pago", "")).strip():
        errores.append("El método de pago es obligatorio.")
    return errores

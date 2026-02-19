"""Validaciones del módulo de Compras."""

from __future__ import annotations

import re
from typing import Any


RFC_PATTERN = re.compile(r"^[A-Z&Ñ]{3,4}\d{6}[A-Z0-9]{3}$")


def validar_proveedor(datos: dict[str, Any]) -> list[str]:
    errores: list[str] = []
    if not str(datos.get("nombre", "")).strip():
        errores.append("El nombre del proveedor es obligatorio.")

    rfc = str(datos.get("rfc", "")).strip().upper()
    if not rfc:
        errores.append("El RFC del proveedor es obligatorio.")
    elif not RFC_PATTERN.match(rfc):
        errores.append("El RFC no tiene un formato válido.")

    email = str(datos.get("email", "")).strip()
    if email and "@" not in email:
        errores.append("El email del proveedor no es válido.")

    return errores


def validar_orden_compra(datos: dict[str, Any]) -> list[str]:
    errores: list[str] = []
    if int(datos.get("proveedor_id", 0) or 0) <= 0:
        errores.append("El proveedor de la orden de compra es obligatorio.")
    if not str(datos.get("fecha", "")).strip():
        errores.append("La fecha de la orden de compra es obligatoria.")
    if float(datos.get("total", 0) or 0) <= 0:
        errores.append("El total de la orden de compra debe ser mayor a 0.")
    if not str(datos.get("moneda", "")).strip():
        errores.append("La moneda es obligatoria.")
    return errores


def validar_recepcion(datos: dict[str, Any]) -> list[str]:
    errores: list[str] = []
    if int(datos.get("orden_compra_id", 0) or 0) <= 0:
        errores.append("La orden de compra asociada es obligatoria.")
    if not str(datos.get("fecha", "")).strip():
        errores.append("La fecha de recepción es obligatoria.")
    if float(datos.get("cantidad_recibida", 0) or 0) <= 0:
        errores.append("La cantidad recibida debe ser mayor a 0.")
    return errores


def validar_cuenta_por_pagar(datos: dict[str, Any]) -> list[str]:
    errores: list[str] = []
    if int(datos.get("proveedor_id", 0) or 0) <= 0:
        errores.append("El proveedor es obligatorio para la cuenta por pagar.")
    if int(datos.get("orden_compra_id", 0) or 0) <= 0:
        errores.append("La orden de compra es obligatoria para la cuenta por pagar.")
    if float(datos.get("monto", 0) or 0) <= 0:
        errores.append("El monto de la cuenta por pagar debe ser mayor a 0.")
    if not str(datos.get("fecha_vencimiento", "")).strip():
        errores.append("La fecha de vencimiento es obligatoria.")
    return errores

"""Modelos de dominio para el módulo de Ventas ERP."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class Cliente:
    id: int
    nombre: str
    rfc: str
    email: str
    telefono: str
    activo: bool = True

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.nombre.strip():
            errors.append("El nombre del cliente es obligatorio.")
        if not self.rfc.strip():
            errors.append("El RFC del cliente es obligatorio.")
        return errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "nombre": self.nombre,
            "rfc": self.rfc,
            "email": self.email,
            "telefono": self.telefono,
            "activo": self.activo,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Cliente":
        return cls(
            id=int(data.get("id", 0)),
            nombre=str(data.get("nombre", "")),
            rfc=str(data.get("rfc", "")),
            email=str(data.get("email", "")),
            telefono=str(data.get("telefono", "")),
            activo=bool(data.get("activo", True)),
        )

    def __repr__(self) -> str:
        return f"Cliente(id={self.id}, nombre='{self.nombre}', rfc='{self.rfc}', activo={self.activo})"


@dataclass(slots=True)
class Cotizacion:
    id: int
    cliente_id: int
    fecha: str
    estado: str
    total: float
    moneda: str

    def validate(self) -> list[str]:
        errors: list[str] = []
        if self.cliente_id <= 0:
            errors.append("cliente_id inválido para cotización.")
        if self.total <= 0:
            errors.append("El total de la cotización debe ser mayor a 0.")
        return errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "cliente_id": self.cliente_id,
            "fecha": self.fecha,
            "estado": self.estado,
            "total": self.total,
            "moneda": self.moneda,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Cotizacion":
        return cls(
            id=int(data.get("id", 0)),
            cliente_id=int(data.get("cliente_id", 0)),
            fecha=str(data.get("fecha", "")),
            estado=str(data.get("estado", "abierta")),
            total=float(data.get("total", 0.0)),
            moneda=str(data.get("moneda", "MXN")),
        )

    def __repr__(self) -> str:
        return (
            "Cotizacion("
            f"id={self.id}, cliente_id={self.cliente_id}, estado='{self.estado}', "
            f"total={self.total}, moneda='{self.moneda}'"
            ")"
        )


@dataclass(slots=True)
class Pedido:
    id: int
    cliente_id: int
    cotizacion_id: int | None
    fecha: str
    estado: str
    total: float

    def validate(self) -> list[str]:
        errors: list[str] = []
        if self.cliente_id <= 0:
            errors.append("cliente_id inválido para pedido.")
        if self.total <= 0:
            errors.append("El total del pedido debe ser mayor a 0.")
        return errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "cliente_id": self.cliente_id,
            "cotizacion_id": self.cotizacion_id,
            "fecha": self.fecha,
            "estado": self.estado,
            "total": self.total,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Pedido":
        return cls(
            id=int(data.get("id", 0)),
            cliente_id=int(data.get("cliente_id", 0)),
            cotizacion_id=(int(data["cotizacion_id"]) if data.get("cotizacion_id") is not None else None),
            fecha=str(data.get("fecha", "")),
            estado=str(data.get("estado", "pendiente")),
            total=float(data.get("total", 0.0)),
        )

    def __repr__(self) -> str:
        return (
            "Pedido("
            f"id={self.id}, cliente_id={self.cliente_id}, cotizacion_id={self.cotizacion_id}, "
            f"estado='{self.estado}', total={self.total}"
            ")"
        )


@dataclass(slots=True)
class FacturaEmitida:
    id: int
    pedido_id: int
    cliente_id: int
    fecha: str
    total: float
    moneda: str
    uuid_xml: str | None = None
    sat_status: str = "pendiente"

    def validate(self) -> list[str]:
        errors: list[str] = []
        if self.pedido_id <= 0:
            errors.append("pedido_id inválido para factura emitida.")
        if self.cliente_id <= 0:
            errors.append("cliente_id inválido para factura emitida.")
        if self.total <= 0:
            errors.append("El total de la factura emitida debe ser mayor a 0.")
        return errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "pedido_id": self.pedido_id,
            "cliente_id": self.cliente_id,
            "fecha": self.fecha,
            "total": self.total,
            "moneda": self.moneda,
            "uuid_xml": self.uuid_xml,
            "sat_status": self.sat_status,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FacturaEmitida":
        return cls(
            id=int(data.get("id", 0)),
            pedido_id=int(data.get("pedido_id", 0)),
            cliente_id=int(data.get("cliente_id", 0)),
            fecha=str(data.get("fecha", "")),
            total=float(data.get("total", 0.0)),
            moneda=str(data.get("moneda", "MXN")),
            uuid_xml=(str(data["uuid_xml"]) if data.get("uuid_xml") else None),
            sat_status=str(data.get("sat_status", "pendiente")),
        )

    def __repr__(self) -> str:
        return (
            "FacturaEmitida("
            f"id={self.id}, pedido_id={self.pedido_id}, cliente_id={self.cliente_id}, "
            f"total={self.total}, sat_status='{self.sat_status}', uuid_xml='{self.uuid_xml}'"
            ")"
        )


@dataclass(slots=True)
class Cobranza:
    id: int
    factura_id: int
    fecha: str
    monto: float
    metodo_pago: str
    referencia: str | None = None

    def validate(self) -> list[str]:
        errors: list[str] = []
        if self.factura_id <= 0:
            errors.append("factura_id inválido para cobranza.")
        if self.monto <= 0:
            errors.append("El monto de cobranza debe ser mayor a 0.")
        if not self.metodo_pago.strip():
            errors.append("El método de pago es obligatorio.")
        return errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "factura_id": self.factura_id,
            "fecha": self.fecha,
            "monto": self.monto,
            "metodo_pago": self.metodo_pago,
            "referencia": self.referencia,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Cobranza":
        return cls(
            id=int(data.get("id", 0)),
            factura_id=int(data.get("factura_id", 0)),
            fecha=str(data.get("fecha", "")),
            monto=float(data.get("monto", 0.0)),
            metodo_pago=str(data.get("metodo_pago", "")),
            referencia=(str(data["referencia"]) if data.get("referencia") else None),
        )

    def __repr__(self) -> str:
        return (
            "Cobranza("
            f"id={self.id}, factura_id={self.factura_id}, monto={self.monto}, metodo_pago='{self.metodo_pago}'"
            ")"
        )

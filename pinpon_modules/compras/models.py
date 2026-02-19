"""Modelos de dominio para el módulo de Compras ERP."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class Proveedor:
    id: int
    nombre: str
    rfc: str
    email: str
    telefono: str
    activo: bool = True

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
    def from_dict(cls, data: dict[str, Any]) -> "Proveedor":
        return cls(
            id=int(data.get("id", 0)),
            nombre=str(data.get("nombre", "")),
            rfc=str(data.get("rfc", "")),
            email=str(data.get("email", "")),
            telefono=str(data.get("telefono", "")),
            activo=bool(data.get("activo", True)),
        )

    def __repr__(self) -> str:
        return f"Proveedor(id={self.id}, nombre='{self.nombre}', rfc='{self.rfc}', activo={self.activo})"


@dataclass(slots=True)
class OrdenCompra:
    id: int
    proveedor_id: int
    fecha: str
    estado: str
    total: float
    moneda: str
    uuid_xml: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "proveedor_id": self.proveedor_id,
            "fecha": self.fecha,
            "estado": self.estado,
            "total": self.total,
            "moneda": self.moneda,
            "uuid_xml": self.uuid_xml,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OrdenCompra":
        return cls(
            id=int(data.get("id", 0)),
            proveedor_id=int(data.get("proveedor_id", 0)),
            fecha=str(data.get("fecha", "")),
            estado=str(data.get("estado", "abierta")),
            total=float(data.get("total", 0.0)),
            moneda=str(data.get("moneda", "MXN")),
            uuid_xml=(str(data["uuid_xml"]) if data.get("uuid_xml") else None),
        )

    def __repr__(self) -> str:
        return (
            "OrdenCompra("
            f"id={self.id}, proveedor_id={self.proveedor_id}, estado='{self.estado}', "
            f"total={self.total}, moneda='{self.moneda}', uuid_xml='{self.uuid_xml}'"
            ")"
        )


@dataclass(slots=True)
class Recepcion:
    id: int
    orden_compra_id: int
    fecha: str
    cantidad_recibida: float
    referencia_xml: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "orden_compra_id": self.orden_compra_id,
            "fecha": self.fecha,
            "cantidad_recibida": self.cantidad_recibida,
            "referencia_xml": self.referencia_xml,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Recepcion":
        return cls(
            id=int(data.get("id", 0)),
            orden_compra_id=int(data.get("orden_compra_id", 0)),
            fecha=str(data.get("fecha", "")),
            cantidad_recibida=float(data.get("cantidad_recibida", 0.0)),
            referencia_xml=(str(data["referencia_xml"]) if data.get("referencia_xml") else None),
        )

    def __repr__(self) -> str:
        return (
            "Recepcion("
            f"id={self.id}, orden_compra_id={self.orden_compra_id}, "
            f"cantidad_recibida={self.cantidad_recibida}, referencia_xml='{self.referencia_xml}'"
            ")"
        )


@dataclass(slots=True)
class CuentaPorPagar:
    id: int
    proveedor_id: int
    orden_compra_id: int
    monto: float
    fecha_vencimiento: str
    pagada: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "proveedor_id": self.proveedor_id,
            "orden_compra_id": self.orden_compra_id,
            "monto": self.monto,
            "fecha_vencimiento": self.fecha_vencimiento,
            "pagada": self.pagada,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CuentaPorPagar":
        return cls(
            id=int(data.get("id", 0)),
            proveedor_id=int(data.get("proveedor_id", 0)),
            orden_compra_id=int(data.get("orden_compra_id", 0)),
            monto=float(data.get("monto", 0.0)),
            fecha_vencimiento=str(data.get("fecha_vencimiento", "")),
            pagada=bool(data.get("pagada", False)),
        )

    def __repr__(self) -> str:
        return (
            "CuentaPorPagar("
            f"id={self.id}, proveedor_id={self.proveedor_id}, orden_compra_id={self.orden_compra_id}, "
            f"monto={self.monto}, pagada={self.pagada}"
            ")"
        )

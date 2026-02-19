"""Servicios de negocio del módulo de Compras."""

from __future__ import annotations

from typing import Any

from .models import CuentaPorPagar, OrdenCompra, Proveedor, Recepcion
from .repository import ComprasRepository


class ComprasService:
    """Orquesta la lógica de negocio y delega persistencia al repositorio."""

    def __init__(self, repository: ComprasRepository | None = None) -> None:
        self.repository = repository or ComprasRepository()

    def crear_proveedor(self, nombre: str, rfc: str, email: str, telefono: str, activo: bool = True) -> dict[str, Any]:
        proveedor = Proveedor(id=0, nombre=nombre.strip(), rfc=rfc.strip().upper(), email=email.strip(), telefono=telefono.strip(), activo=bool(activo))
        record = self.repository.create("proveedores", proveedor.to_dict())
        return Proveedor.from_dict(record).to_dict()

    def crear_orden_compra(
        self,
        proveedor_id: int,
        fecha: str,
        estado: str,
        total: float,
        moneda: str,
        uuid_xml: str | None = None,
    ) -> dict[str, Any]:
        if not self.repository.get_by_id("proveedores", proveedor_id):
            raise ValueError(f"No existe el proveedor con id {proveedor_id}.")

        orden = OrdenCompra(
            id=0,
            proveedor_id=int(proveedor_id),
            fecha=fecha.strip(),
            estado=estado.strip() or "abierta",
            total=float(total),
            moneda=moneda.strip().upper() or "MXN",
            uuid_xml=(uuid_xml.strip() if uuid_xml else None),
        )
        record = self.repository.create("ordenes_compra", orden.to_dict())
        return OrdenCompra.from_dict(record).to_dict()

    def registrar_recepcion(
        self,
        orden_compra_id: int,
        fecha: str,
        cantidad_recibida: float,
        referencia_xml: str | None = None,
    ) -> dict[str, Any]:
        orden = self.repository.get_by_id("ordenes_compra", orden_compra_id)
        if not orden:
            raise ValueError(f"No existe la orden de compra con id {orden_compra_id}.")

        recepcion = Recepcion(
            id=0,
            orden_compra_id=int(orden_compra_id),
            fecha=fecha.strip(),
            cantidad_recibida=float(cantidad_recibida),
            referencia_xml=(referencia_xml.strip() if referencia_xml else None),
        )
        record = self.repository.create("recepciones", recepcion.to_dict())

        orden_actualizada = dict(orden)
        orden_actualizada["estado"] = "recibida"
        self.repository.update("ordenes_compra", int(orden_compra_id), orden_actualizada)

        return Recepcion.from_dict(record).to_dict()

    def generar_cuenta_por_pagar(self, orden_compra_id: int, fecha_vencimiento: str, monto: float | None = None) -> dict[str, Any]:
        orden = self.repository.get_by_id("ordenes_compra", orden_compra_id)
        if not orden:
            raise ValueError(f"No existe la orden de compra con id {orden_compra_id}.")

        monto_final = float(monto if monto is not None else orden.get("total", 0.0))
        cuenta = CuentaPorPagar(
            id=0,
            proveedor_id=int(orden.get("proveedor_id", 0)),
            orden_compra_id=int(orden_compra_id),
            monto=monto_final,
            fecha_vencimiento=fecha_vencimiento.strip(),
            pagada=False,
        )
        record = self.repository.create("cuentas_por_pagar", cuenta.to_dict())
        return CuentaPorPagar.from_dict(record).to_dict()

    def vincular_xml_a_orden_compra(self, uuid_xml: str, orden_id: int) -> dict[str, Any]:
        orden = self.repository.get_by_id("ordenes_compra", orden_id)
        if not orden:
            raise ValueError(f"No existe la orden de compra con id {orden_id}.")

        sat_resultado = self._validar_sat_placeholder(uuid_xml)

        orden_actualizada = dict(orden)
        orden_actualizada["uuid_xml"] = uuid_xml.strip()
        self.repository.update("ordenes_compra", int(orden_id), orden_actualizada)
        return {
            "orden_compra": OrdenCompra.from_dict(orden_actualizada).to_dict(),
            "sat": sat_resultado,
        }

    def listar_proveedores(self) -> list[dict[str, Any]]:
        return self.repository.list_all("proveedores")

    def listar_ordenes_compra(self) -> list[dict[str, Any]]:
        return self.repository.list_all("ordenes_compra")

    def listar_recepciones(self) -> list[dict[str, Any]]:
        return self.repository.list_all("recepciones")

    def listar_cuentas_por_pagar(self) -> list[dict[str, Any]]:
        return self.repository.list_all("cuentas_por_pagar")

    def _validar_sat_placeholder(self, uuid_xml: str) -> dict[str, Any]:
        return {
            "uuid": uuid_xml.strip(),
            "status": "pendiente_cliente_sat",
            "valid": True,
            "message": "Validación SAT pendiente de integración con cliente oficial.",
        }


def crear_proveedor(service: ComprasService, **kwargs: Any) -> dict[str, Any]:
    return service.crear_proveedor(**kwargs)


def crear_orden_compra(service: ComprasService, **kwargs: Any) -> dict[str, Any]:
    return service.crear_orden_compra(**kwargs)


def registrar_recepcion(service: ComprasService, **kwargs: Any) -> dict[str, Any]:
    return service.registrar_recepcion(**kwargs)


def generar_cuenta_por_pagar(service: ComprasService, **kwargs: Any) -> dict[str, Any]:
    return service.generar_cuenta_por_pagar(**kwargs)


def vincular_xml_a_orden_compra(service: ComprasService, uuid_xml: str, orden_id: int) -> dict[str, Any]:
    return service.vincular_xml_a_orden_compra(uuid_xml=uuid_xml, orden_id=orden_id)

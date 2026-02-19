"""Servicios de negocio del módulo de Ventas."""

from __future__ import annotations

from typing import Any

from .models import Cliente, Cobranza, Cotizacion, FacturaEmitida, Pedido
from .repository import VentasRepository


class VentasService:
    def __init__(self, repository: VentasRepository | None = None) -> None:
        self.repository = repository or VentasRepository()

    def crear_cliente(self, nombre: str, rfc: str, email: str, telefono: str, activo: bool = True) -> dict[str, Any]:
        cliente = Cliente(id=0, nombre=nombre.strip(), rfc=rfc.strip().upper(), email=email.strip(), telefono=telefono.strip(), activo=bool(activo))
        record = self.repository.create("clientes", cliente.to_dict())
        return Cliente.from_dict(record).to_dict()

    def crear_cotizacion(self, cliente_id: int, fecha: str, estado: str, total: float, moneda: str) -> dict[str, Any]:
        if not self.repository.get_by_id("clientes", cliente_id):
            raise ValueError(f"No existe el cliente con id {cliente_id}.")
        cotizacion = Cotizacion(
            id=0,
            cliente_id=int(cliente_id),
            fecha=fecha.strip(),
            estado=estado.strip() or "abierta",
            total=float(total),
            moneda=moneda.strip().upper() or "MXN",
        )
        record = self.repository.create("cotizaciones", cotizacion.to_dict())
        return Cotizacion.from_dict(record).to_dict()

    def convertir_cotizacion_a_pedido(self, cotizacion_id: int, fecha: str | None = None) -> dict[str, Any]:
        cotizacion = self.repository.get_by_id("cotizaciones", cotizacion_id)
        if not cotizacion:
            raise ValueError(f"No existe la cotización con id {cotizacion_id}.")

        pedido = Pedido(
            id=0,
            cliente_id=int(cotizacion["cliente_id"]),
            cotizacion_id=int(cotizacion_id),
            fecha=(fecha or str(cotizacion.get("fecha", ""))).strip(),
            estado="pendiente",
            total=float(cotizacion.get("total", 0.0)),
        )
        record = self.repository.create("pedidos", pedido.to_dict())

        cotizacion_update = dict(cotizacion)
        cotizacion_update["estado"] = "convertida"
        self.repository.update("cotizaciones", int(cotizacion_id), cotizacion_update)

        return Pedido.from_dict(record).to_dict()

    def registrar_factura_emitida(
        self,
        pedido_id: int,
        cliente_id: int,
        fecha: str,
        total: float,
        moneda: str,
        uuid_xml: str | None = None,
    ) -> dict[str, Any]:
        if not self.repository.get_by_id("pedidos", pedido_id):
            raise ValueError(f"No existe el pedido con id {pedido_id}.")
        if not self.repository.get_by_id("clientes", cliente_id):
            raise ValueError(f"No existe el cliente con id {cliente_id}.")

        factura = FacturaEmitida(
            id=0,
            pedido_id=int(pedido_id),
            cliente_id=int(cliente_id),
            fecha=fecha.strip(),
            total=float(total),
            moneda=moneda.strip().upper() or "MXN",
            uuid_xml=(uuid_xml.strip() if uuid_xml else None),
            sat_status="pendiente",
        )
        record = self.repository.create("facturas_emitidas", factura.to_dict())
        return FacturaEmitida.from_dict(record).to_dict()

    def vincular_xml_a_factura(self, uuid_xml: str, factura_id: int) -> dict[str, Any]:
        factura = self.repository.get_by_id("facturas_emitidas", factura_id)
        if not factura:
            raise ValueError(f"No existe la factura emitida con id {factura_id}.")

        sat_resultado = self._validar_sat_placeholder(uuid_xml)
        factura_actualizada = dict(factura)
        factura_actualizada["uuid_xml"] = uuid_xml.strip()
        factura_actualizada["sat_status"] = str(sat_resultado.get("status", "pendiente"))
        self.repository.update("facturas_emitidas", int(factura_id), factura_actualizada)
        return {"factura": FacturaEmitida.from_dict(factura_actualizada).to_dict(), "sat": sat_resultado}

    def registrar_cobranza(
        self,
        factura_id: int,
        fecha: str,
        monto: float,
        metodo_pago: str,
        referencia: str | None = None,
    ) -> dict[str, Any]:
        factura = self.repository.get_by_id("facturas_emitidas", factura_id)
        if not factura:
            raise ValueError(f"No existe la factura emitida con id {factura_id}.")

        cobranza = Cobranza(
            id=0,
            factura_id=int(factura_id),
            fecha=fecha.strip(),
            monto=float(monto),
            metodo_pago=metodo_pago.strip(),
            referencia=(referencia.strip() if referencia else None),
        )
        record = self.repository.create("cobranzas", cobranza.to_dict())
        return Cobranza.from_dict(record).to_dict()

    def listar_clientes(self) -> list[dict[str, Any]]:
        return self.repository.list_all("clientes")

    def listar_cotizaciones(self) -> list[dict[str, Any]]:
        return self.repository.list_all("cotizaciones")

    def listar_pedidos(self) -> list[dict[str, Any]]:
        return self.repository.list_all("pedidos")

    def listar_facturas_emitidas(self) -> list[dict[str, Any]]:
        return self.repository.list_all("facturas_emitidas")

    def listar_cobranzas(self) -> list[dict[str, Any]]:
        return self.repository.list_all("cobranzas")

    def _validar_sat_placeholder(self, uuid_xml: str) -> dict[str, Any]:
        return {
            "uuid": uuid_xml.strip(),
            "status": "pendiente_cliente_sat",
            "valid": True,
            "message": "Validación SAT pendiente de integración con cliente oficial.",
        }

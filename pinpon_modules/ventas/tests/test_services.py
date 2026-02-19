from pathlib import Path

from pinpon_modules.ventas.repository import VentasRepository
from pinpon_modules.ventas.services import VentasService


def _service_tmp(tmp_path: Path) -> VentasService:
    repo = VentasRepository(db_path=tmp_path / "ventas_test_db.json")
    return VentasService(repository=repo)


def test_flujo_servicios_ventas(tmp_path: Path) -> None:
    service = _service_tmp(tmp_path)

    cliente = service.crear_cliente(
        nombre="Cliente Uno",
        rfc="AAA010101AAA",
        email="cliente@demo.com",
        telefono="555-2222",
        activo=True,
    )
    assert cliente["id"] == 1

    cotizacion = service.crear_cotizacion(
        cliente_id=cliente["id"],
        fecha="2026-02-19",
        estado="abierta",
        total=3200.0,
        moneda="MXN",
    )
    assert cotizacion["cliente_id"] == cliente["id"]

    pedido = service.convertir_cotizacion_a_pedido(cotizacion_id=cotizacion["id"])
    assert pedido["cotizacion_id"] == cotizacion["id"]

    factura = service.registrar_factura_emitida(
        pedido_id=pedido["id"],
        cliente_id=cliente["id"],
        fecha="2026-02-20",
        total=3200.0,
        moneda="MXN",
        uuid_xml=None,
    )
    assert factura["pedido_id"] == pedido["id"]

    vinculada = service.vincular_xml_a_factura(uuid_xml="UUID-VENTA-1", factura_id=factura["id"])
    assert vinculada["factura"]["uuid_xml"] == "UUID-VENTA-1"

    cobranza = service.registrar_cobranza(
        factura_id=factura["id"],
        fecha="2026-02-21",
        monto=3200.0,
        metodo_pago="transferencia",
        referencia="REF-001",
    )
    assert cobranza["factura_id"] == factura["id"]

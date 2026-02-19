from pinpon_modules.compras.models import CuentaPorPagar, OrdenCompra, Proveedor, Recepcion


def test_modelos_to_dict_y_from_dict() -> None:
    proveedor = Proveedor(id=1, nombre="Proveedor Demo", rfc="AAA010101AAA", email="a@b.com", telefono="555", activo=True)
    orden = OrdenCompra(id=1, proveedor_id=1, fecha="2026-02-19", estado="abierta", total=1000.0, moneda="MXN", uuid_xml=None)
    recepcion = Recepcion(id=1, orden_compra_id=1, fecha="2026-02-19", cantidad_recibida=10, referencia_xml="UUID-1")
    cxp = CuentaPorPagar(id=1, proveedor_id=1, orden_compra_id=1, monto=1000.0, fecha_vencimiento="2026-03-01", pagada=False)

    assert Proveedor.from_dict(proveedor.to_dict()).nombre == "Proveedor Demo"
    assert OrdenCompra.from_dict(orden.to_dict()).total == 1000.0
    assert Recepcion.from_dict(recepcion.to_dict()).referencia_xml == "UUID-1"
    assert CuentaPorPagar.from_dict(cxp.to_dict()).pagada is False

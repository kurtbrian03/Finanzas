from pinpon_modules.ventas.models import Cliente, Cobranza, Cotizacion, FacturaEmitida, Pedido


def test_modelos_ventas_to_dict_from_dict() -> None:
    cliente = Cliente(id=1, nombre="Cliente Demo", rfc="AAA010101AAA", email="demo@mail.com", telefono="555")
    cotizacion = Cotizacion(id=1, cliente_id=1, fecha="2026-02-19", estado="abierta", total=2000.0, moneda="MXN")
    pedido = Pedido(id=1, cliente_id=1, cotizacion_id=1, fecha="2026-02-19", estado="pendiente", total=2000.0)
    factura = FacturaEmitida(id=1, pedido_id=1, cliente_id=1, fecha="2026-02-19", total=2000.0, moneda="MXN")
    cobranza = Cobranza(id=1, factura_id=1, fecha="2026-02-20", monto=1000.0, metodo_pago="transferencia")

    assert Cliente.from_dict(cliente.to_dict()).nombre == "Cliente Demo"
    assert Cotizacion.from_dict(cotizacion.to_dict()).total == 2000.0
    assert Pedido.from_dict(pedido.to_dict()).cotizacion_id == 1
    assert FacturaEmitida.from_dict(factura.to_dict()).pedido_id == 1
    assert Cobranza.from_dict(cobranza.to_dict()).monto == 1000.0

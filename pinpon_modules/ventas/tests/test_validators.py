from pinpon_modules.ventas.validators import (
    validar_cliente,
    validar_cobranza,
    validar_cotizacion,
    validar_factura_emitida,
    validar_pedido,
)


def test_validar_cliente_ok() -> None:
    errores = validar_cliente({"nombre": "Cliente", "rfc": "AAA010101AAA", "email": "ok@mail.com"})
    assert errores == []


def test_validar_cliente_error() -> None:
    errores = validar_cliente({"nombre": "", "rfc": "XXX", "email": "sin-arroba"})
    assert len(errores) >= 2


def test_validar_cotizacion_error() -> None:
    errores = validar_cotizacion({"cliente_id": 0, "fecha": "", "total": 0})
    assert len(errores) >= 2


def test_validar_pedido_error() -> None:
    errores = validar_pedido({"cliente_id": 0, "fecha": "", "total": 0})
    assert len(errores) >= 2


def test_validar_factura_emitida_error() -> None:
    errores = validar_factura_emitida({"pedido_id": 0, "cliente_id": 0, "fecha": "", "total": 0})
    assert len(errores) >= 3


def test_validar_cobranza_error() -> None:
    errores = validar_cobranza({"factura_id": 0, "fecha": "", "monto": 0, "metodo_pago": ""})
    assert len(errores) >= 3

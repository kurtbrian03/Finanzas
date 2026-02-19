from pinpon_modules.compras.validators import (
    validar_cuenta_por_pagar,
    validar_orden_compra,
    validar_proveedor,
    validar_recepcion,
)


def test_validar_proveedor_ok() -> None:
    errores = validar_proveedor(
        {
            "nombre": "Proveedor Uno",
            "rfc": "AAA010101AAA",
            "email": "demo@mail.com",
        }
    )
    assert errores == []


def test_validar_proveedor_error() -> None:
    errores = validar_proveedor(
        {
            "nombre": "",
            "rfc": "RFC_INVALIDO",
            "email": "correo-invalido",
        }
    )
    assert len(errores) >= 2


def test_validar_orden_compra_error() -> None:
    errores = validar_orden_compra(
        {
            "proveedor_id": 0,
            "fecha": "",
            "total": 0,
            "moneda": "",
        }
    )
    assert len(errores) >= 3


def test_validar_recepcion_error() -> None:
    errores = validar_recepcion(
        {
            "orden_compra_id": 0,
            "fecha": "",
            "cantidad_recibida": 0,
        }
    )
    assert len(errores) >= 2


def test_validar_cxp_error() -> None:
    errores = validar_cuenta_por_pagar(
        {
            "proveedor_id": 0,
            "orden_compra_id": 0,
            "monto": 0,
            "fecha_vencimiento": "",
        }
    )
    assert len(errores) >= 3

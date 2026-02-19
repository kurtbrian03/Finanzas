from pathlib import Path

from pinpon_modules.compras.repository import ComprasRepository
from pinpon_modules.compras.services import ComprasService


def _service_tmp(tmp_path: Path) -> ComprasService:
    repo = ComprasRepository(db_path=tmp_path / "compras_test_db.json")
    return ComprasService(repository=repo)


def test_flujo_servicios_compras(tmp_path: Path) -> None:
    service = _service_tmp(tmp_path)

    proveedor = service.crear_proveedor(
        nombre="Proveedor Uno",
        rfc="AAA010101AAA",
        email="proveedor@demo.com",
        telefono="555-1111",
        activo=True,
    )
    assert proveedor["id"] == 1

    oc = service.crear_orden_compra(
        proveedor_id=proveedor["id"],
        fecha="2026-02-19",
        estado="abierta",
        total=1250.5,
        moneda="MXN",
        uuid_xml=None,
    )
    assert oc["proveedor_id"] == proveedor["id"]

    recepcion = service.registrar_recepcion(
        orden_compra_id=oc["id"],
        fecha="2026-02-20",
        cantidad_recibida=20,
        referencia_xml="UUID-XYZ",
    )
    assert recepcion["orden_compra_id"] == oc["id"]

    cxp = service.generar_cuenta_por_pagar(
        orden_compra_id=oc["id"],
        fecha_vencimiento="2026-03-20",
        monto=None,
    )
    assert cxp["monto"] == 1250.5

    vinculo = service.vincular_xml_a_orden_compra(uuid_xml="UUID-XYZ", orden_id=oc["id"])
    assert vinculo["orden_compra"]["uuid_xml"] == "UUID-XYZ"

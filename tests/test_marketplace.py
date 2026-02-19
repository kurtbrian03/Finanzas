from __future__ import annotations

from pinpon_marketplace.installer import list_available_modules


def test_marketplace_registry_list() -> None:
    modules = list_available_modules()
    assert isinstance(modules, list)
    assert modules, "El marketplace no contiene módulos registrados"

    ids = {m["id"] for m in modules}
    assert "erp_compras" in ids
    assert "erp_ventas" in ids
    assert "erp_inventarios" in ids

    for module in modules:
        assert "installation_mode" in module
        assert module["installation_mode"] in {"none", "local", "submodule", "pip"}
        assert "status" in module
        assert "can_uninstall" in module
        assert "can_update" in module

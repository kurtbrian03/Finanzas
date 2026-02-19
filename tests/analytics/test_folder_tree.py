from dropbox_integration.folder_tree import (
    aplicar_filtros_virtuales,
    breadcrumbs_virtuales,
    construir_arbol_virtual,
    extraer_contexto_virtual,
)


def _registros_demo() -> list[dict[str, object]]:
    return [
        {
            "ruta_completa": "C:/FACTURACION/ProveedorUno/2026/Hospital Central/enero/factura_001.pdf",
            "nombre_archivo": "factura_001.pdf",
            "extension": ".pdf",
            "categoria": "PDF",
            "tamaño": 100,
            "fecha_modificacion": "2026-02-18",
        },
        {
            "ruta_completa": "C:/FACTURACION/ProveedorUno/2026/Hospital Central/febrero/factura_002.pdf",
            "nombre_archivo": "factura_002.pdf",
            "extension": ".pdf",
            "categoria": "PDF",
            "tamaño": 120,
            "fecha_modificacion": "2026-02-18",
        },
    ]


def test_extraer_contexto_virtual() -> None:
    contexto = extraer_contexto_virtual("C:/FACTURACION/ProveedorUno/2026/Hospital Central/enero/factura.pdf")
    assert contexto["anio"] == "2026"
    assert contexto["mes"].startswith("01")


def test_construir_arbol_virtual_y_filtros() -> None:
    registros = _registros_demo()
    arbol = construir_arbol_virtual(registros)

    assert arbol["stats"]["archivos"] == 2
    assert "ProveedorUno" in arbol["children"]

    filtrados = aplicar_filtros_virtuales(registros, proveedor="ProveedorUno", anio="2026")
    assert len(filtrados) == 2

    bc = breadcrumbs_virtuales(filtrados[0])
    assert "ProveedorUno" in bc
    assert "2026" in bc

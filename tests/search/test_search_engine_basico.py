from dropbox_integration.search_engine import SearchEngine


def _docs() -> list[dict[str, object]]:
    return [
        {
            "nombre_archivo": "factura_enero.pdf",
            "ruta_completa": "C:/tmp/factura_enero.pdf",
            "extension": ".pdf",
            "carpeta": "PDF",
            "categoria": "PDF",
            "etiquetas": ["factura", "enero"],
            "tamaño": 120,
            "fecha_modificacion": "2026-01-10",
            "hash": "h1",
            "contenido_extraido": "factura mensual cliente uno",
        },
        {
            "nombre_archivo": "imagen_ticket.png",
            "ruta_completa": "C:/tmp/imagen_ticket.png",
            "extension": ".png",
            "carpeta": "JPG",
            "categoria": "Imagen",
            "etiquetas": ["ticket", "imagen"],
            "tamaño": 200,
            "fecha_modificacion": "2026-01-11",
            "hash": "h2",
            "contenido_extraido": "",
        },
    ]


def test_indexacion_basica() -> None:
    engine = SearchEngine(_docs())
    engine.indexar_documentos()
    assert len(engine.index) == 2


def test_busqueda_nombre_exacta_parcial_fuzzy() -> None:
    engine = SearchEngine(_docs())
    engine.indexar_documentos()
    exactos = engine.buscar_por_nombre("factura_enero.pdf")
    parciales = engine.buscar_por_nombre("factura")
    fuzzy = engine.buscar_por_nombre("facturra enro", usar_fuzzy=True)
    assert exactos and str(exactos[0]["relevancia"]) and float(str(exactos[0]["relevancia"])) >= 90
    assert parciales and str(parciales[0]["nombre"]).startswith("factura")
    assert fuzzy


def test_filtros_basicos() -> None:
    engine = SearchEngine(_docs())
    engine.indexar_documentos()
    assert len(engine.buscar_por_extension("pdf")) == 1
    assert len(engine.buscar_por_carpeta("pdf")) == 1
    assert len(engine.buscar_por_tipo("pdf")) == 1
    assert len(engine.buscar_por_etiquetas(["ticket"])) == 1

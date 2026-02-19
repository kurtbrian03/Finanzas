from dropbox_integration.search_engine import SearchEngine


def test_busqueda_contenido_relevancia_por_ocurrencias() -> None:
    docs = [
        {
            "nombre_archivo": "a.txt",
            "ruta_completa": "a.txt",
            "extension": ".txt",
            "carpeta": "TEXTO",
            "categoria": "Texto",
            "etiquetas": [],
            "tamaño": 1,
            "fecha_modificacion": "2026-01-01",
            "hash": "1",
            "contenido_extraido": "factura factura factura proveedor",
        },
        {
            "nombre_archivo": "b.txt",
            "ruta_completa": "b.txt",
            "extension": ".txt",
            "carpeta": "TEXTO",
            "categoria": "Texto",
            "etiquetas": [],
            "tamaño": 1,
            "fecha_modificacion": "2026-01-02",
            "hash": "2",
            "contenido_extraido": "factura proveedor",
        },
    ]
    engine = SearchEngine(docs)
    engine.indexar_documentos()
    resultados = engine.buscar_por_contenido("factura proveedor")
    assert len(resultados) == 2
    assert resultados[0]["nombre"] == "a.txt"
    assert resultados[0]["relevancia"] >= resultados[1]["relevancia"]

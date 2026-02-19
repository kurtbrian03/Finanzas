from dropbox_integration.search_engine import SearchEngine


def test_modelo_tfidf_y_ranking_semantico() -> None:
    docs = [
        {
            "nombre_archivo": "factura_mensual.pdf",
            "ruta_completa": "f1",
            "extension": ".pdf",
            "carpeta": "PDF",
            "categoria": "PDF",
            "etiquetas": ["factura"],
            "tamaño": 1,
            "fecha_modificacion": "2026-01-01",
            "hash": "h1",
            "contenido_extraido": "factura mensual enero cliente",
        },
        {
            "nombre_archivo": "manual_usuario.txt",
            "ruta_completa": "f2",
            "extension": ".txt",
            "carpeta": "TEXTO",
            "categoria": "Texto",
            "etiquetas": ["manual"],
            "tamaño": 1,
            "fecha_modificacion": "2026-01-01",
            "hash": "h2",
            "contenido_extraido": "manual de instalacion y usuario",
        },
    ]

    engine = SearchEngine(docs)
    engine.indexar_documentos()
    engine.construir_modelo_semantico()
    resultados = engine.buscar_semantico("factura de cliente", top_k=5)
    assert resultados
    assert resultados[0]["nombre"] == "factura_mensual.pdf"

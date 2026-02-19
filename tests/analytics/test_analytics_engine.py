from pathlib import Path
import zipfile

from dropbox_integration.analytics_engine import analizar_archivo, construir_resumen_analitico


def test_analizar_archivo_texto(tmp_path: Path) -> None:
    archivo = tmp_path / "factura.txt"
    archivo.write_text("Factura proveedor uno\nHospital central\n", encoding="utf-8")

    resultado = analizar_archivo(archivo)

    assert resultado["tipo"] == "TEXTO"
    assert resultado["metricas"]["lineas"] >= 2
    assert resultado["metricas"]["palabras"] >= 4


def test_analizar_archivo_zip(tmp_path: Path) -> None:
    zip_path = tmp_path / "paquete.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("a.txt", "hola")
        zf.writestr("b.csv", "x,y")

    resultado = analizar_archivo(zip_path)

    assert resultado["tipo"] == "ZIP"
    assert int(resultado["metricas"]["entradas"]) == 2


def test_resumen_analitico_basico() -> None:
    detalle = [
        {"tipo": "TEXTO", "extension": ".txt", "carpeta": "TEXTO", "tamano_bytes": 10, "metricas": {"palabras": 3}, "error": ""},
        {"tipo": "ZIP", "extension": ".zip", "carpeta": "ZIPPED", "tamano_bytes": 30, "metricas": {"entradas": 2}, "error": ""},
    ]

    resumen = construir_resumen_analitico(detalle)

    assert resumen["total_archivos"] == 2
    assert resumen["total_bytes"] == 40
    assert resumen["tipos"]["TEXTO"] == 1
    assert resumen["zip_entradas"] == 2

from pathlib import Path

from dropbox_integration.content_extractor import extraer_texto_archivo, limpiar_texto


def test_limpieza_texto_normaliza_espacios_y_minusculas() -> None:
    texto = " HOLA\x00\x01   Mundo\n\nRFC "
    limpio = limpiar_texto(texto)
    assert limpio == "hola mundo rfc"


def test_extrae_txt(tmp_path: Path) -> None:
    archivo = tmp_path / "demo.txt"
    archivo.write_text("Factura   TOTAL\n\n100", encoding="utf-8")
    out = extraer_texto_archivo(archivo)
    assert "factura" in out
    assert "total" in out


def test_pdf_mocked(monkeypatch: object, tmp_path: Path) -> None:
    from dropbox_integration import content_extractor

    archivo = tmp_path / "a.pdf"
    archivo.write_bytes(b"%PDF")
    monkeypatch.setattr(content_extractor, "_leer_pdf", lambda _p: "contenido pdf")
    out = content_extractor.extraer_texto_archivo(archivo)
    assert out == "contenido pdf"


def test_docx_mocked(monkeypatch: object, tmp_path: Path) -> None:
    from dropbox_integration import content_extractor

    archivo = tmp_path / "a.docx"
    archivo.write_bytes(b"PK")
    monkeypatch.setattr(content_extractor, "_leer_docx", lambda _p: "contenido docx")
    out = content_extractor.extraer_texto_archivo(archivo)
    assert out == "contenido docx"


def test_archivo_inexistente_retorna_vacio(tmp_path: Path) -> None:
    out = extraer_texto_archivo(tmp_path / "no_existe.txt")
    assert out == ""

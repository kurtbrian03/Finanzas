from pathlib import Path

from dropbox_integration import aspel_invoice_menu


def test_is_aspel_invoice_detects_from_record() -> None:
    row = {
        "nombre_archivo": "Factura_Aspel_001.pdf",
        "extension": ".pdf",
        "contenido_extraido": "CFDI emitido",
    }
    assert aspel_invoice_menu._is_aspel_invoice(row)


def test_extract_invoice_metadata_prefers_xml_data(monkeypatch: object, tmp_path: Path) -> None:
    pdf = tmp_path / "factura.pdf"
    pdf.write_bytes(b"%PDF")

    monkeypatch.setattr(
        aspel_invoice_menu,
        "extract_cfdi_from_pdf",
        lambda _p: {
            "uuid": "123e4567-e89b-12d3-a456-426614174000",
            "rfc_emisor": "AAA010101AAA",
            "rfc_receptor": "BBB010101BBB",
            "total": "321.00",
            "fecha": "2026-02-18T10:00:00",
            "source": "xml",
        },
    )

    out = aspel_invoice_menu._extract_invoice_metadata(pdf)
    assert out["uuid"] == "123e4567-e89b-12d3-a456-426614174000"
    assert out["rfc_emisor"] == "AAA010101AAA"
    assert out["rfc_receptor"] == "BBB010101BBB"
    assert out["total"] == "321.00"


def test_find_pdf_invoices_from_records(monkeypatch: object) -> None:
    rows = [
        {
            "nombre_archivo": "Factura_Aspel_001.pdf",
            "extension": ".pdf",
            "ruta_completa": "C:/tmp/factura1.pdf",
            "contenido_extraido": "CFDI ASPel factura",
            "proveedor_virtual": "ACME",
        },
        {
            "nombre_archivo": "nota.txt",
            "extension": ".txt",
            "ruta_completa": "C:/tmp/nota.txt",
            "contenido_extraido": "texto",
        },
    ]

    monkeypatch.setattr(
        aspel_invoice_menu,
        "_extract_invoice_metadata",
        lambda row: {"nombre_archivo": row["nombre_archivo"], "uuid": "u", "proveedor": "ACME", "fecha": "", "total": "", "rfc_emisor": "", "rfc_receptor": "", "ruta": row["ruta_completa"], "xml_source": "none"},
    )

    out = aspel_invoice_menu._find_pdf_invoices(rows)
    assert len(out) == 1
    assert out[0]["nombre_archivo"].endswith(".pdf")

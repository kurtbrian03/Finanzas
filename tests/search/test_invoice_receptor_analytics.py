import dropbox_integration.invoice_receptor_analytics as analytics


def test_build_invoices_dataset_filters_pdf_and_invoice_content(monkeypatch: object) -> None:
    rows = [
        {"extension": ".pdf", "contenido_extraido": "Factura CFDI", "nombre_archivo": "ok.pdf"},
        {"extension": ".txt", "contenido_extraido": "Factura CFDI", "nombre_archivo": "skip.txt"},
        {"extension": ".pdf", "contenido_extraido": "documento sin match", "nombre_archivo": "skip.pdf"},
    ]

    monkeypatch.setattr(
        analytics,
        "_extract_invoice_metadata",
        lambda _row: {
            "nombre_archivo": "ok.pdf",
            "rfc_receptor": "AAA010101AAA",
            "total": "100.00",
            "fecha": "2026-02-18T10:00:00",
            "proveedor_detectado": "Aspel",
        },
    )
    monkeypatch.setattr(analytics, "classify_receptor_bucket", lambda _rfc, text: "AG DISTRIBUIDORA" if "cfdi" in text.lower() else "OTROS")

    out = analytics.build_invoices_dataset(rows)

    assert len(out) == 1
    assert out[0]["receptor_bucket"] == "AG DISTRIBUIDORA"
    assert out[0]["proveedor_detectado"] == "Aspel"


def test_summarize_by_receptor_aggregates_totals_counts_and_monthly() -> None:
    data = [
        {"receptor_bucket": "AG DISTRIBUIDORA", "total": "100", "fecha": "2026-02-18"},
        {"receptor_bucket": "AG DISTRIBUIDORA", "total": "50", "fecha": "2026-02-20"},
        {"receptor_bucket": "MEDBRIGHT", "total": "30", "fecha": "2026-03-01"},
    ]

    summary = analytics.summarize_by_receptor(data)

    assert summary["counts"]["AG DISTRIBUIDORA"] == 2
    assert summary["totals"]["AG DISTRIBUIDORA"] == 150.0
    assert summary["totals"]["MEDBRIGHT"] == 30.0
    assert summary["monthly"]["AG DISTRIBUIDORA"]["2026-02"] == 150.0

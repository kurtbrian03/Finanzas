from dropbox_integration.invoice_provider_classifier import (
    classify_invoice_provider,
    classify_receptor_bucket,
)


def test_classify_invoice_provider_known_vendors() -> None:
    assert classify_invoice_provider(text="Factura emitida por Aspel CFDI") == "Aspel"
    assert classify_invoice_provider(text="Comprobante de Facturama") == "Facturama"
    assert classify_invoice_provider(text="Portal de Facture") == "Facture"
    assert classify_invoice_provider(text="Sistema Contpaqi") == "Contpaqi"


def test_classify_invoice_provider_from_xml_payload() -> None:
    assert classify_invoice_provider(text="sin pistas", xml_payload={"issuer": "FACTURAMA"}) == "Facturama"
    assert classify_invoice_provider(text="sin pistas", xml_payload={"tool": "aspel"}) == "Aspel"


def test_classify_invoice_provider_fallback_otros() -> None:
    assert classify_invoice_provider(text="Este documento es una factura simple") == "Otros"
    assert classify_invoice_provider(text="Documento administrativo") == "Otros"


def test_classify_receptor_bucket_rules() -> None:
    assert classify_receptor_bucket("", "Factura AG DISTRIBUIDORA SA de CV") == "AG DISTRIBUIDORA"
    assert classify_receptor_bucket("", "Servicio hospitalario Medbright") == "MEDBRIGHT"
    assert classify_receptor_bucket("XAXX010101000", "texto sin match") == "OTROS"

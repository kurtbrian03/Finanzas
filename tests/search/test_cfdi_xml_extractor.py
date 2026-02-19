from pathlib import Path

from analysis import cfdi_xml_extractor


XML_40 = """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<cfdi:Comprobante xmlns:cfdi=\"http://www.sat.gob.mx/cfd/4\" Version=\"4.0\" Fecha=\"2026-02-18T10:00:00\" Total=\"123.45\">
  <cfdi:Emisor Rfc=\"AAA010101AAA\" />
  <cfdi:Receptor Rfc=\"BBB010101BBB\" />
  <cfdi:Complemento>
    <tfd:TimbreFiscalDigital xmlns:tfd=\"http://www.sat.gob.mx/TimbreFiscalDigital\" UUID=\"123e4567-e89b-12d3-a456-426614174000\" />
  </cfdi:Complemento>
</cfdi:Comprobante>
"""


def test_parse_cfdi_xml_text_extracts_core_fields() -> None:
    parsed = cfdi_xml_extractor._parse_cfdi_xml_text(XML_40)
    assert parsed["uuid"] == "123e4567-e89b-12d3-a456-426614174000"
    assert parsed["rfc_emisor"] == "AAA010101AAA"
    assert parsed["rfc_receptor"] == "BBB010101BBB"
    assert parsed["total"] == "123.45"


def test_extract_cfdi_from_pdf_fallback_text_regex(monkeypatch: object, tmp_path: Path) -> None:
    pdf = tmp_path / "factura.pdf"
    pdf.write_bytes(b"%PDF")

    monkeypatch.setattr(cfdi_xml_extractor, "_xml_candidates_from_pdf", lambda _p: [])
    monkeypatch.setattr(
        cfdi_xml_extractor,
        "extraer_contenido_archivo",
        lambda _p: "UUID 123e4567-e89b-12d3-a456-426614174000 RFC AAA010101AAA BBB010101BBB Total 999.90 2026-02-18T10:00:00",
    )

    out = cfdi_xml_extractor.extract_cfdi_from_pdf(pdf)
    assert out["uuid"] == "123e4567-e89b-12d3-a456-426614174000"
    assert out["rfc_emisor"] == "AAA010101AAA"
    assert out["rfc_receptor"] == "BBB010101BBB"
    assert out["total"] == "999.90"
    assert out["source"] == "text_regex"

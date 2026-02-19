from validation.cfdi_sat_api import _validate_cfdi_sat


def test_cfdi_sat_api_mock_returns_expected_shape() -> None:
    result = _validate_cfdi_sat(
        uuid="123e4567-e89b-12d3-a456-426614174000",
        rfc_emisor="AAA010101AAA",
        rfc_receptor="BBB010101BBB",
        total="123.45",
    )

    assert "estado" in result
    assert "mensaje" in result
    assert "fecha_consulta" in result
    assert result["provider"] in {"mock", "http"}


def test_cfdi_sat_api_handles_missing_params() -> None:
    result = _validate_cfdi_sat(uuid="", rfc_emisor="", rfc_receptor="", total="")
    assert str(result.get("estado", "")) in {"no_encontrado", "vigente", "cancelado"}
    assert "mensaje" in result

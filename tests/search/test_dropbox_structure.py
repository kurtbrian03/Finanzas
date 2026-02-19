from pathlib import Path

from dropbox_integration.dropbox_structure import (
    EXPECTED_PATHS,
    ensure_dropbox_structure,
    move_invoices_to_provider_folders,
    normalize_images_to_pending,
    validate_dropbox_structure,
)


def test_ensure_and_validate_dropbox_structure(tmp_path: Path) -> None:
    result = ensure_dropbox_structure(tmp_path)
    assert result["total_created"] == len(EXPECTED_PATHS)

    validation = validate_dropbox_structure(tmp_path)
    assert validation["valid"] is True
    assert validation["missing"] == []


def test_normalize_images_to_pending_moves_only_pending_folders(tmp_path: Path) -> None:
    images = tmp_path / "Imagenes"
    cadera = images / "Cadera"
    persona = images / "Juan Perez"
    pending = images / "Pendiente"
    cadera.mkdir(parents=True)
    persona.mkdir(parents=True)
    pending.mkdir(parents=True)

    cadera_img = cadera / "a.jpg"
    persona_img = persona / "b.jpg"
    cadera_img.write_bytes(b"1")
    persona_img.write_bytes(b"2")

    moves = normalize_images_to_pending(tmp_path)

    assert len(moves) == 1
    assert moves[0]["status"] == "moved_pending"
    assert (pending / "a.jpg").exists()
    assert persona_img.exists()


def test_move_invoices_to_provider_folders(tmp_path: Path) -> None:
    src_dir = tmp_path / "entrada"
    src_dir.mkdir(parents=True)
    pdf = src_dir / "f1.pdf"
    pdf.write_bytes(b"%PDF")

    invoices = [{"ruta": str(pdf), "proveedor_detectado": "Facturama"}]
    moves = move_invoices_to_provider_folders(tmp_path, invoices)

    assert len(moves) == 1
    assert moves[0]["status"] == "moved_provider"
    assert (tmp_path / "Facturama" / "f1.pdf").exists()

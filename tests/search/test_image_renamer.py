from pathlib import Path

from dropbox_integration.image_renamer import _is_pending_folder, _rename_images_by_folder


def test_is_pending_folder_rules() -> None:
    assert _is_pending_folder("Cadera")
    assert _is_pending_folder("Pendiente para facturar")
    assert not _is_pending_folder("Juan Perez")


def test_rename_images_by_folder(tmp_path: Path) -> None:
    carpeta_persona = tmp_path / "Juan Perez"
    carpeta_pendiente = tmp_path / "Cadera"
    carpeta_persona.mkdir(parents=True)
    carpeta_pendiente.mkdir(parents=True)

    (carpeta_persona / "1.jpg").write_bytes(b"a")
    (carpeta_persona / "2.jpeg").write_bytes(b"b")
    (carpeta_pendiente / "x.jpg").write_bytes(b"c")

    cambios = _rename_images_by_folder(tmp_path)

    assert cambios
    assert any("Juan_Perez_001.jpg" in item["new"] for item in cambios)
    assert any("Pendiente_001.jpg" in item["new"] for item in cambios)

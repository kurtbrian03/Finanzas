from __future__ import annotations

from pathlib import Path

from dropbox_integration.image_renamer import _is_pending_folder

EXPECTED_PATHS = [
    "ASPel",
    "Facturama",
    "Facture",
    "Contpaqi",
    "Imagenes",
    "Imagenes/Cadera",
    "Imagenes/Rodilla",
    "Imagenes/Hallux valgus",
    "Imagenes/Pendiente",
    "HojaConsumo",
    "Otros",
]


def ensure_dropbox_structure(root: str | Path) -> dict[str, object]:
    base = Path(root)
    created: list[str] = []
    for rel in EXPECTED_PATHS:
        path = base / rel
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            created.append(str(path))
    return {"created": created, "total_created": len(created)}


def validate_dropbox_structure(root: str | Path) -> dict[str, object]:
    base = Path(root)
    missing = [str(base / rel) for rel in EXPECTED_PATHS if not (base / rel).exists()]
    return {"valid": len(missing) == 0, "missing": missing}


def normalize_images_to_pending(root: str | Path) -> list[dict[str, str]]:
    base = Path(root)
    images_root = base / "Imagenes"
    pending = images_root / "Pendiente"
    pending.mkdir(parents=True, exist_ok=True)

    moves: list[dict[str, str]] = []
    if not images_root.exists():
        return moves

    for folder in images_root.iterdir():
        if not folder.is_dir() or folder.resolve() == pending.resolve():
            continue
        if not _is_pending_folder(folder.name):
            continue

        for img in list(folder.glob("*.jpg")) + list(folder.glob("*.jpeg")):
            target = pending / img.name
            collision = 1
            while target.exists():
                target = pending / f"{img.stem}_{collision}{img.suffix}"
                collision += 1
            img.rename(target)
            moves.append({"old": str(img), "new": str(target), "status": "moved_pending"})

    return moves


def _provider_folder_name(provider: str) -> str:
    p = str(provider or "").strip().lower()
    if p == "aspel":
        return "ASPel"
    if p == "facturama":
        return "Facturama"
    if p == "facture":
        return "Facture"
    if p == "contpaqi":
        return "Contpaqi"
    return "Otros"


def move_invoices_to_provider_folders(root: str | Path, invoices: list[dict[str, object]]) -> list[dict[str, str]]:
    base = Path(root)
    moves: list[dict[str, str]] = []

    for row in invoices:
        src = Path(str(row.get("ruta", "") or row.get("ruta_completa", "")))
        if not src.exists() or src.suffix.lower() != ".pdf":
            continue

        folder = _provider_folder_name(str(row.get("proveedor_detectado", "Otros")))
        dst_dir = base / folder
        dst_dir.mkdir(parents=True, exist_ok=True)
        dst = dst_dir / src.name

        collision = 1
        while dst.exists() and dst.resolve() != src.resolve():
            dst = dst_dir / f"{src.stem}_{collision}{src.suffix}"
            collision += 1

        if dst.resolve() == src.resolve():
            continue

        src.rename(dst)
        moves.append({"old": str(src), "new": str(dst), "status": "moved_provider"})

    return moves

from __future__ import annotations

import re
from pathlib import Path

_PENDING_HINTS = {
    "pendiente",
    "pending",
    "sin_nombre",
    "sinnombre",
    "por_facturar",
    "porfacturar",
    "cadera",
    "rodilla",
    "hallux",
    "valgus",
    "hombro",
    "pie",
    "mano",
    "columna",
}


def _normalize_name(value: str) -> str:
    text = str(value or "").strip()
    text = re.sub(r"\s+", "_", text)
    text = re.sub(r"[^A-Za-z0-9_\-]", "", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text or "Pendiente"


def _find_jpg_images(root: str | Path) -> list[Path]:
    base = Path(root)
    if not base.exists() or not base.is_dir():
        return []
    images = list(base.rglob("*.jpg")) + list(base.rglob("*.jpeg"))
    return sorted({p.resolve() for p in images})


def _is_pending_folder(folder_name: str) -> bool:
    text = str(folder_name or "").strip().lower()
    if not text:
        return True

    normalized = _normalize_name(text).lower()
    if any(hint in normalized for hint in _PENDING_HINTS):
        return True

    words = [w for w in re.split(r"[^a-zA-ZáéíóúñÁÉÍÓÚÑ]+", text) if w]
    if len(words) < 2:
        return True

    long_words = [w for w in words if len(w) >= 2]
    return len(long_words) < 2


def _rename_images_by_folder(root: str | Path) -> list[dict[str, str]]:
    images = _find_jpg_images(root)
    if not images:
        return []

    by_folder: dict[Path, list[Path]] = {}
    for image in images:
        by_folder.setdefault(image.parent, []).append(image)

    renames: list[dict[str, str]] = []
    for folder, files in sorted(by_folder.items(), key=lambda x: str(x[0]).lower()):
        files_sorted = sorted(files, key=lambda x: x.name.lower())
        folder_base = "Pendiente" if _is_pending_folder(folder.name) else _normalize_name(folder.name)

        for index, old_path in enumerate(files_sorted, start=1):
            ext = ".jpg"
            base_name = f"{folder_base}_{index:03d}{ext}"
            target = old_path.with_name(base_name)
            collision = 1
            while target.exists() and target.resolve() != old_path.resolve():
                collision += 1
                target = old_path.with_name(f"{folder_base}_{index:03d}_{collision}{ext}")

            if target.resolve() == old_path.resolve():
                renames.append({"old": str(old_path), "new": str(target), "status": "unchanged"})
                continue

            old_path.rename(target)
            renames.append({"old": str(old_path), "new": str(target), "status": "renamed"})

    return renames

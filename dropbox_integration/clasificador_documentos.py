from __future__ import annotations

import json
from pathlib import Path

REGLAS_EXTENSION = {
    ".pdf": "PDF",
    ".jpg": "Imagen",
    ".jpeg": "Imagen",
    ".png": "Imagen",
    ".xlsx": "Excel",
    ".xls": "Excel",
    ".txt": "Texto",
    ".md": "Texto",
    ".py": "Script Python",
    ".ps1": "Script PowerShell",
    ".zip": "ZIP",
}


def clasificar_documentos(registros: list[dict[str, object]]) -> list[dict[str, object]]:
    """Clasifica lista de registros por extensión."""
    clasificados: list[dict[str, object]] = []
    for item in registros:
        extension = str(item.get("extension", "")).lower()
        categoria = REGLAS_EXTENSION.get(extension, "Sin clasificar")
        nuevo = dict(item)
        nuevo["categoria"] = categoria
        clasificados.append(nuevo)
    return clasificados


def exportar_mapeo(
    clasificados: list[dict[str, object]],
    json_path: Path,
    markdown_path: Path,
) -> None:
    """Exporta mapeo a JSON y tabla Markdown."""
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)

    json_path.write_text(json.dumps(clasificados, ensure_ascii=False, indent=2), encoding="utf-8")

    header = "| Nombre | Tipo | Carpeta | Ruta | Tamaño | Fecha | Categoría |\n"
    divider = "|---|---|---|---|---:|---|---|\n"
    lines = [
        f"| {row.get('nombre_archivo','')} | {row.get('extension','')} | {row.get('carpeta','')} | {row.get('ruta_completa','')} | {row.get('tamaño',0)} | {row.get('fecha_modificacion','')} | {row.get('categoria','')} |"
        for row in clasificados
    ]
    markdown = "# Mapeo Dropbox de Documentos\n\n" + header + divider + "\n".join(lines) + "\n"
    markdown_path.write_text(markdown, encoding="utf-8")

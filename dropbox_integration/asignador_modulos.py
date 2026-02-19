from __future__ import annotations

import json
from pathlib import Path


def _es_legal(nombre_archivo: str) -> bool:
    texto = nombre_archivo.lower()
    return any(token in texto for token in ("legal", "contrato", "jurid", "acuerdo"))


def asignar_modulos_app(clasificados: list[dict[str, object]]) -> list[dict[str, object]]:
    """Asigna módulo destino por categoría/tipo."""
    salida: list[dict[str, object]] = []
    for item in clasificados:
        categoria = str(item.get("categoria", ""))
        nombre = str(item.get("nombre_archivo", ""))

        if categoria == "PDF":
            modulo = "validation/legal/" if _es_legal(nombre) else "analysis/"
        elif categoria == "Imagen":
            modulo = "ui/assets/images/"
        elif categoria == "Excel":
            modulo = "analysis/data/"
        elif categoria == "Texto":
            modulo = "docs/text/"
        elif categoria == "ZIP":
            modulo = "docs/zipped/"
        elif categoria == "Script Python":
            modulo = "scripts/python/"
        elif categoria == "Script PowerShell":
            modulo = "scripts/powershell/"
        else:
            modulo = "docs/misc/"

        nuevo = dict(item)
        nuevo["modulo_asignado"] = modulo
        salida.append(nuevo)

    return salida


def exportar_asignacion(asignados: list[dict[str, object]], json_path: Path) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(asignados, ensure_ascii=False, indent=2), encoding="utf-8")

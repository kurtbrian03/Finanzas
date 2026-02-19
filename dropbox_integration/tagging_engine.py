from __future__ import annotations

from pathlib import Path


def asignar_etiquetas_automaticas(registros: list[dict[str, object]]) -> list[dict[str, object]]:
    """Asigna etiquetas automáticas según tipo/carpeta/nombre."""
    salida: list[dict[str, object]] = []
    for item in registros:
        etiquetas = {"importado-dropbox"}
        categoria = str(item.get("categoria", "")).lower()
        carpeta = str(item.get("carpeta", "")).lower()
        nombre = str(item.get("nombre_archivo", "")).lower()
        ext = str(item.get("extension", "")).lower()

        if "legal" in nombre or "legal" in categoria:
            etiquetas.add("legal")
        if "manual" in nombre:
            etiquetas.add("manual")
        if "arquitect" in nombre:
            etiquetas.add("arquitectura")
        if "imagen" in categoria or ext in {".jpg", ".jpeg", ".png"}:
            etiquetas.add("imagen")
        if ext:
            etiquetas.add(ext.lstrip("."))
        if carpeta:
            etiquetas.add(f"carpeta-{carpeta}")
        if categoria == "sin clasificar":
            etiquetas.add("sin-clasificar")

        nuevo = dict(item)
        nuevo["etiquetas"] = sorted(etiquetas)
        salida.append(nuevo)
    return salida


def agregar_etiqueta_manual(registros: list[dict[str, object]], ruta: str, etiqueta: str) -> None:
    for item in registros:
        if str(item.get("ruta_completa")) == ruta:
            actuales = item.get("etiquetas", [])
            etiquetas = set(actuales if isinstance(actuales, list) else [])
            etiquetas.add(etiqueta.strip().lower())
            item["etiquetas"] = sorted(etiquetas)
            return


def editar_etiqueta_manual(registros: list[dict[str, object]], ruta: str, anterior: str, nueva: str) -> None:
    for item in registros:
        if str(item.get("ruta_completa")) == ruta:
            actuales = item.get("etiquetas", [])
            etiquetas = set(actuales if isinstance(actuales, list) else [])
            if anterior in etiquetas:
                etiquetas.remove(anterior)
                etiquetas.add(nueva)
            item["etiquetas"] = sorted(etiquetas)
            return


def eliminar_etiqueta_manual(registros: list[dict[str, object]], ruta: str, etiqueta: str) -> None:
    for item in registros:
        if str(item.get("ruta_completa")) == ruta:
            actuales = item.get("etiquetas", [])
            etiquetas = set(actuales if isinstance(actuales, list) else [])
            etiquetas.discard(etiqueta)
            item["etiquetas"] = sorted(etiquetas)
            return

from __future__ import annotations

from collections import Counter
from datetime import datetime
from pathlib import Path
import re
from typing import Any, cast
import zipfile

import pymupdf as fitz
import pandas as pd
from PIL import Image

try:
    import cv2
except Exception:  # pragma: no cover
    cv2 = None


_EXT_TIPO = {
    ".pdf": "PDF",
    ".xls": "EXCEL",
    ".xlsx": "EXCEL",
    ".xlsm": "EXCEL",
    ".csv": "EXCEL",
    ".jpg": "IMAGEN",
    ".jpeg": "IMAGEN",
    ".png": "IMAGEN",
    ".bmp": "IMAGEN",
    ".tiff": "IMAGEN",
    ".txt": "TEXTO",
    ".md": "TEXTO",
    ".json": "TEXTO",
    ".xml": "TEXTO",
    ".py": "TEXTO",
    ".ps1": "TEXTO",
    ".zip": "ZIP",
}


def _to_int(valor: object, default: int = 0) -> int:
    try:
        return int(valor)  # type: ignore[arg-type]
    except Exception:
        return default


def _tipo_por_extension(extension: str) -> str:
    return _EXT_TIPO.get(extension.lower(), "OTRO")


def _analitica_pdf(ruta: Path) -> dict[str, object]:
    metricas: dict[str, object] = {
        "paginas": 0,
        "palabras": 0,
        "tablas_estimadas": 0,
        "imagenes_embebidas": 0,
    }
    documento = fitz.open(ruta)
    try:
        metricas["paginas"] = documento.page_count
        palabras = 0
        tablas = 0
        imagenes = 0
        for pagina in documento:
            palabras += len(pagina.get_text("words"))
            imagenes += len(pagina.get_images(full=True))
            texto_raw = pagina.get_text("text")
            texto = texto_raw if isinstance(texto_raw, str) else ""
            tablas += len(re.findall(r"\|", texto)) // 8
        metricas["palabras"] = palabras
        metricas["tablas_estimadas"] = int(tablas)
        metricas["imagenes_embebidas"] = int(imagenes)
    finally:
        documento.close()
    return metricas


def _analitica_excel(ruta: Path) -> dict[str, object]:
    metricas: dict[str, object] = {
        "hojas": 0,
        "filas_totales": 0,
        "columnas_max": 0,
    }
    excel = pd.ExcelFile(ruta)
    metricas["hojas"] = len(excel.sheet_names)
    filas = 0
    columnas_max = 0
    for hoja in excel.sheet_names[:8]:
        df = pd.read_excel(ruta, sheet_name=hoja)
        filas += int(df.shape[0])
        columnas_max = max(columnas_max, int(df.shape[1]))
    metricas["filas_totales"] = filas
    metricas["columnas_max"] = columnas_max
    return metricas


def _detectar_logo_probable(ruta: Path) -> bool:
    if cv2 is None:
        return False
    imagen = cv2.imread(str(ruta))
    if imagen is None:
        return False
    alto, ancho = imagen.shape[:2]
    if alto < 40 or ancho < 40:
        return False
    zona = imagen[0 : max(40, alto // 4), 0 : max(60, ancho // 3)]
    gris = cv2.cvtColor(zona, cv2.COLOR_BGR2GRAY)
    bordes = cv2.Canny(gris, threshold1=60, threshold2=160)
    densidad = float((bordes > 0).sum()) / float(bordes.size)
    return densidad > 0.08


def _analitica_imagen(ruta: Path) -> dict[str, object]:
    metricas: dict[str, object] = {
        "ancho": 0,
        "alto": 0,
        "modo": "",
        "logo_probable": False,
    }
    with Image.open(ruta) as imagen:
        metricas["ancho"] = int(imagen.width)
        metricas["alto"] = int(imagen.height)
        metricas["modo"] = str(imagen.mode)
    metricas["logo_probable"] = _detectar_logo_probable(ruta)
    return metricas


def _analitica_texto(ruta: Path) -> dict[str, object]:
    contenido = ruta.read_text(encoding="utf-8", errors="ignore")
    lineas = contenido.splitlines()
    palabras = re.findall(r"\b\w+\b", contenido, flags=re.UNICODE)
    return {
        "lineas": len(lineas),
        "palabras": len(palabras),
        "caracteres": len(contenido),
    }


def _analitica_zip(ruta: Path) -> dict[str, object]:
    with zipfile.ZipFile(ruta) as zf:
        infos = zf.infolist()
        extensiones = Counter(Path(info.filename).suffix.lower() for info in infos if not info.is_dir())
        return {
            "entradas": len(infos),
            "tamano_comprimido": int(sum(info.compress_size for info in infos)),
            "tamano_descomprimido": int(sum(info.file_size for info in infos)),
            "extensiones_internas": dict(extensiones.most_common(10)),
        }


def analizar_archivo(ruta_archivo: str | Path) -> dict[str, object]:
    ruta = Path(ruta_archivo)
    extension = ruta.suffix.lower()
    tipo = _tipo_por_extension(extension)

    salida: dict[str, object] = {
        "ruta": str(ruta),
        "nombre": ruta.name,
        "extension": extension,
        "tipo": tipo,
        "tamano_bytes": 0,
        "fecha_modificacion": "",
        "metricas": {},
        "error": "",
    }

    if not ruta.exists():
        salida["error"] = "archivo_no_existe"
        return salida

    salida["tamano_bytes"] = int(ruta.stat().st_size)
    salida["fecha_modificacion"] = datetime.fromtimestamp(ruta.stat().st_mtime).isoformat()

    try:
        if tipo == "PDF":
            salida["metricas"] = _analitica_pdf(ruta)
        elif tipo == "EXCEL":
            salida["metricas"] = _analitica_excel(ruta)
        elif tipo == "IMAGEN":
            salida["metricas"] = _analitica_imagen(ruta)
        elif tipo == "TEXTO":
            salida["metricas"] = _analitica_texto(ruta)
        elif tipo == "ZIP":
            salida["metricas"] = _analitica_zip(ruta)
        else:
            salida["metricas"] = {}
    except Exception as error:
        salida["error"] = str(error)

    return salida


def analizar_documentos(registros: list[dict[str, object]]) -> list[dict[str, object]]:
    analitica: list[dict[str, object]] = []
    for item in registros:
        ruta = str(item.get("ruta_completa", "")).strip()
        if not ruta:
            continue
        a = analizar_archivo(ruta)
        a["categoria"] = str(item.get("categoria", ""))
        a["carpeta"] = str(item.get("carpeta", ""))
        a["modulo_asignado"] = str(item.get("modulo_asignado", ""))
        analitica.append(a)
    return analitica


def construir_resumen_analitico(analitica: list[dict[str, object]]) -> dict[str, object]:
    total = len(analitica)
    por_tipo = Counter(str(a.get("tipo", "OTRO")) for a in analitica)
    por_extension = Counter(str(a.get("extension", "")) for a in analitica)
    por_carpeta = Counter(str(a.get("carpeta", "")) for a in analitica)

    pdf_paginas = 0
    excel_hojas = 0
    imagenes_logo = 0
    texto_palabras = 0
    zip_entradas = 0
    total_bytes = 0
    for item in analitica:
        metricas = cast(dict[str, Any], item.get("metricas", {}))
        tipo = str(item.get("tipo", ""))
        total_bytes += _to_int(item.get("tamano_bytes", 0), 0)
        pdf_paginas += _to_int(metricas.get("paginas", 0), 0)
        excel_hojas += _to_int(metricas.get("hojas", 0), 0)
        if bool(metricas.get("logo_probable", False)):
            imagenes_logo += 1
        if tipo == "TEXTO":
            texto_palabras += _to_int(metricas.get("palabras", 0), 0)
        if tipo == "ZIP":
            zip_entradas += _to_int(metricas.get("entradas", 0), 0)

    return {
        "total_archivos": total,
        "total_bytes": total_bytes,
        "tipos": dict(por_tipo),
        "extensiones": dict(por_extension.most_common(20)),
        "carpetas": dict(por_carpeta),
        "pdf_paginas": pdf_paginas,
        "excel_hojas": excel_hojas,
        "imagenes_logo_probable": imagenes_logo,
        "texto_palabras": texto_palabras,
        "zip_entradas": zip_entradas,
        "errores": [a for a in analitica if str(a.get("error", "")).strip()],
    }

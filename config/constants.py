"""Constantes funcionales del sistema.

Responsabilidad:
- Definir catálogos y valores inmutables usados por análisis, validación y descargas.
"""

CARPETAS_FORMATO = {
    "EXCEL": {".xlsx", ".xls"},
    "JPG": {".jpg", ".jpeg", ".png"},
    "PDF": {".pdf"},
    "POWERSHELL": {".ps1"},
    "PYTHON": {".py"},
    "TEXTO": {".txt", ".csv", ".md"},
    "ZIPPED": {".zip"},
}

TIPOS_DESCARGA = {".pdf", ".xml", ".zip", ".json", ".xlsx", ".xls"}

RFC_AUTORIZADOS = {"AAVS781006P72"}

RUTAS_APP = {
    "Visor de documentos": "viewer",
    "Dropbox IA": "dropbox",
    "Dropbox Explorer": "dropbox_explorer",
    "Dashboard facturas receptor": "receptor_dashboard",
    "Validación RFC/Folio": "validation",
    "Descargas controladas": "downloads",
    "Historial": "history",
    "Configuración": "settings",
}

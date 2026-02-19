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

ERP_MODULES = {
    "erp_compras": "Módulo de Compras (ERP)",
    "erp_ventas": "Módulo de Ventas (ERP)",
    "erp_inventarios": "Módulo de Inventarios (ERP)",
    "erp_marketplace": "Marketplace ERP",
}


def _build_erp_routes() -> dict[str, str]:
    """Construye mapeo de etiqueta -> clave de ruta para módulos ERP."""
    return {label: key for key, label in ERP_MODULES.items()}

RUTAS_APP = {
    "Visor de documentos": "viewer",
    "Dropbox IA": "dropbox",
    "Dropbox Explorer": "dropbox_explorer",
    **_build_erp_routes(),
    "Dashboard facturas receptor": "receptor_dashboard",
    "Validación RFC/Folio": "validation",
    "Descargas controladas": "downloads",
    "Historial": "history",
    "Configuración": "settings",
}

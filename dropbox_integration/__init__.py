"""Módulos de integración Dropbox + clasificación documental."""

from .lector_dropbox import detectar_ruta_dropbox, leer_dropbox_recursivo
from .clasificador_documentos import clasificar_documentos, exportar_mapeo
from .asignador_modulos import asignar_modulos_app, exportar_asignacion
from .tagging_engine import (
    asignar_etiquetas_automaticas,
    agregar_etiqueta_manual,
    eliminar_etiqueta_manual,
    editar_etiqueta_manual,
)
from .metrics import bytes_humanos, calcular_metricas
from .content_extractor import extraer_contenido_archivo
from .search_engine import SearchEngine, construir_estadisticas_busqueda
from .analytics_engine import analizar_archivo, analizar_documentos, construir_resumen_analitico
from .folder_tree import construir_arbol_virtual, aplicar_filtros_virtuales, opciones_filtros_virtuales, breadcrumbs_virtuales
from .report_generator import generar_paquete_reportes

__all__ = [
    "detectar_ruta_dropbox",
    "leer_dropbox_recursivo",
    "clasificar_documentos",
    "exportar_mapeo",
    "asignar_modulos_app",
    "exportar_asignacion",
    "asignar_etiquetas_automaticas",
    "agregar_etiqueta_manual",
    "eliminar_etiqueta_manual",
    "editar_etiqueta_manual",
    "calcular_metricas",
    "bytes_humanos",
    "extraer_contenido_archivo",
    "SearchEngine",
    "construir_estadisticas_busqueda",
    "analizar_archivo",
    "analizar_documentos",
    "construir_resumen_analitico",
    "construir_arbol_virtual",
    "aplicar_filtros_virtuales",
    "opciones_filtros_virtuales",
    "breadcrumbs_virtuales",
    "generar_paquete_reportes",
]

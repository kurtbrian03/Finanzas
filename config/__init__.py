"""Configuración global de la aplicación.

Este paquete centraliza constantes, valores por defecto y funciones de entorno
para mantener consistencia entre módulos.
"""

from .constants import CARPETAS_FORMATO, RFC_AUTORIZADOS, TIPOS_DESCARGA
from .environment import detectar_carpeta_facturacion
from .settings import APP_INFO, DEFAULT_CONFIG

__all__ = [
    "APP_INFO",
    "DEFAULT_CONFIG",
    "CARPETAS_FORMATO",
    "TIPOS_DESCARGA",
    "RFC_AUTORIZADOS",
    "detectar_carpeta_facturacion",
]

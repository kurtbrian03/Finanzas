"""Configuración global de la aplicación.

Este paquete centraliza constantes, valores por defecto y funciones de entorno
para mantener consistencia entre módulos.
"""

import importlib.util
from pathlib import Path


_root_config_path = Path(__file__).resolve().parents[1] / "config.py"
_root_config_spec = importlib.util.spec_from_file_location("_finanzas_root_config", _root_config_path)

if _root_config_spec and _root_config_spec.loader:
    _root_config = importlib.util.module_from_spec(_root_config_spec)
    _root_config_spec.loader.exec_module(_root_config)
    DEBUG_MODE = bool(getattr(_root_config, "DEBUG_MODE", True))
else:
    DEBUG_MODE = True

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
    "DEBUG_MODE",
]

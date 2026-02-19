"""Navegación lateral.

Responsabilidad:
- Renderizar sidebar y retornar selección del usuario.
"""

from __future__ import annotations

import streamlit as st

from config.constants import RUTAS_APP
from config.environment import detectar_carpeta_facturacion


def render_sidebar() -> tuple[str, str, str]:
    """Dibuja sidebar y retorna usuario, ruta y opción seleccionada."""
    st.sidebar.title("Navegación")
    usuario = st.sidebar.text_input("Usuario", value="Operador")
    ruta_default = detectar_carpeta_facturacion()
    ruta = st.sidebar.text_input("Ruta FACTURACION", value=str(ruta_default))
    selected = st.sidebar.radio("Módulo", list(RUTAS_APP.keys()))
    return usuario, ruta, selected

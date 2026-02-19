"""Tema y configuración visual.

Responsabilidad:
- Aplicar ajustes visuales globales sin alterar lógica de negocio.
"""

import streamlit as st


def apply_theme() -> None:
    """Aplica parámetros de estilo base del sistema."""
    st.markdown(
        """
        <style>
            .block-container {padding-top: 1rem;}
        </style>
        """,
        unsafe_allow_html=True,
    )

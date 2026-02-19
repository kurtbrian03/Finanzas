"""Mensajes y notificaciones comunes.

Responsabilidad:
- Centralizar mensajes informativos globales de UX.
"""

import streamlit as st


def show_global_notice() -> None:
    """Muestra aviso de control de lectura/descarga."""
    st.info("Vistas previas en modo solo lectura. Descargas únicamente por acción explícita en botón.")

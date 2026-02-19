from __future__ import annotations

import streamlit as st

from .installer import install_module, list_available_modules, uninstall_module, update_module


def render_marketplace() -> None:
    st.markdown("## Marketplace ERP")
    st.caption("Gestiona instalación, actualización y desinstalación de módulos ERP.")

    modules = list_available_modules()
    if not modules:
        st.warning("No hay módulos registrados en el marketplace.")
        return

    for module in modules:
        module_id = str(module.get("id", ""))
        name = str(module.get("name", module_id))
        description = str(module.get("description", ""))
        status = str(module.get("status", "No instalado"))
        can_update = bool(module.get("can_update", False))
        can_uninstall = bool(module.get("can_uninstall", False))

        with st.container(border=True):
            st.markdown(f"### {name}")
            st.code(module_id)
            st.write(description)
            st.write(f"Estado: {status}")

            col1, col2, col3 = st.columns(3)

            if col1.button("Instalar", key=f"install_{module_id}", disabled="No instalado" not in status):
                result = install_module(module_id)
                if result.get("ok"):
                    st.success(str(result.get("message")))
                else:
                    st.error(str(result.get("message")))

            if col2.button("Actualizar", key=f"update_{module_id}", disabled=not can_update):
                result = update_module(module_id)
                if result.get("ok"):
                    st.success(str(result.get("message")))
                else:
                    st.error(str(result.get("message")))

            if col3.button("Desinstalar", key=f"uninstall_{module_id}", disabled=not can_uninstall):
                result = uninstall_module(module_id)
                if result.get("ok"):
                    st.success(str(result.get("message")))
                else:
                    st.error(str(result.get("message")))

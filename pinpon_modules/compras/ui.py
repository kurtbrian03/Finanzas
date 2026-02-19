"""Interfaz Streamlit para el módulo ERP de Compras."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from .controller import ComprasController


def _render_result(result: dict[str, object]) -> None:
    if bool(result.get("ok", False)):
        st.success(str(result.get("message", "Operación ejecutada correctamente.")))
    else:
        errors = result.get("errors", [])
        if isinstance(errors, list) and errors:
            for error in errors:
                st.error(str(error))
        else:
            st.error("No fue posible completar la operación.")


def render_modulo_compras() -> None:
    controller = ComprasController()
    service = controller.service

    st.markdown("## Módulo de Compras (ERP)")
    st.caption("Gestión base de proveedores, órdenes de compra, recepciones y cuentas por pagar.")

    tab_proveedores, tab_oc, tab_recepciones, tab_cxp = st.tabs(
        ["Proveedores", "Órdenes de compra", "Recepciones", "Cuentas por pagar"]
    )

    with tab_proveedores:
        with st.form("form_proveedor"):
            st.markdown("### Alta de proveedor")
            nombre = st.text_input("Nombre")
            rfc = st.text_input("RFC")
            email = st.text_input("Email")
            telefono = st.text_input("Teléfono")
            activo = st.checkbox("Activo", value=True)
            submit = st.form_submit_button("Guardar proveedor", use_container_width=True)

        if submit:
            result = controller.crear_proveedor_desde_form(
                nombre=nombre,
                rfc=rfc,
                email=email,
                telefono=telefono,
                activo=activo,
            )
            _render_result(result)

        st.markdown("### Listado de proveedores")
        proveedores = service.listar_proveedores()
        if proveedores:
            st.dataframe(pd.DataFrame(proveedores), use_container_width=True)
        else:
            st.info("No hay proveedores registrados.")

    with tab_oc:
        with st.form("form_oc"):
            st.markdown("### Nueva orden de compra")
            proveedor_id = st.number_input("Proveedor ID", min_value=1, step=1)
            fecha = st.text_input("Fecha (YYYY-MM-DD)")
            estado = st.selectbox("Estado", options=["abierta", "recibida", "cerrada"], index=0)
            total = st.number_input("Total", min_value=0.0, step=0.01, format="%.2f")
            moneda = st.text_input("Moneda", value="MXN")
            uuid_xml = st.text_input("UUID XML (opcional)")
            submit_oc = st.form_submit_button("Guardar orden de compra", use_container_width=True)

        if submit_oc:
            result = controller.crear_oc_desde_form(
                proveedor_id=int(proveedor_id),
                fecha=fecha,
                estado=estado,
                total=float(total),
                moneda=moneda,
                uuid_xml=uuid_xml or None,
            )
            _render_result(result)

        st.markdown("### Listado de órdenes de compra")
        ordenes = service.listar_ordenes_compra()
        if ordenes:
            st.dataframe(pd.DataFrame(ordenes), use_container_width=True)
        else:
            st.info("No hay órdenes de compra registradas.")

        with st.form("form_vincular_xml"):
            st.markdown("### Vincular XML a OC")
            oc_id_xml = st.number_input("Orden ID", min_value=1, step=1, key="oc_id_xml")
            uuid_xml_link = st.text_input("UUID XML", key="uuid_xml_link")
            submit_link = st.form_submit_button("Vincular XML", use_container_width=True)

        if submit_link:
            try:
                result = service.vincular_xml_a_orden_compra(uuid_xml=uuid_xml_link, orden_id=int(oc_id_xml))
                st.success("XML vinculado correctamente.")
                st.json(result)
            except ValueError as error:
                st.error(str(error))

    with tab_recepciones:
        with st.form("form_recepcion"):
            st.markdown("### Registrar recepción")
            orden_compra_id = st.number_input("Orden de compra ID", min_value=1, step=1)
            fecha_recepcion = st.text_input("Fecha recepción (YYYY-MM-DD)")
            cantidad_recibida = st.number_input("Cantidad recibida", min_value=0.0, step=0.01, format="%.2f")
            referencia_xml = st.text_input("Referencia XML (opcional)")
            submit_recepcion = st.form_submit_button("Registrar recepción", use_container_width=True)

        if submit_recepcion:
            result = controller.registrar_recepcion_desde_form(
                orden_compra_id=int(orden_compra_id),
                fecha=fecha_recepcion,
                cantidad_recibida=float(cantidad_recibida),
                referencia_xml=referencia_xml or None,
            )
            _render_result(result)

        st.markdown("### Listado de recepciones")
        recepciones = service.listar_recepciones()
        if recepciones:
            st.dataframe(pd.DataFrame(recepciones), use_container_width=True)
        else:
            st.info("No hay recepciones registradas.")

    with tab_cxp:
        with st.form("form_cxp"):
            st.markdown("### Generar cuenta por pagar")
            oc_id_cxp = st.number_input("Orden de compra ID", min_value=1, step=1)
            fecha_vencimiento = st.text_input("Fecha vencimiento (YYYY-MM-DD)")
            monto = st.number_input("Monto (0 para usar total de OC)", min_value=0.0, step=0.01, format="%.2f")
            submit_cxp = st.form_submit_button("Generar CxP", use_container_width=True)

        if submit_cxp:
            monto_payload = None if float(monto) == 0 else float(monto)
            result = controller.generar_cxp_desde_oc(
                orden_compra_id=int(oc_id_cxp),
                fecha_vencimiento=fecha_vencimiento,
                monto=monto_payload,
            )
            _render_result(result)

        st.markdown("### Listado de cuentas por pagar")
        cuentas = service.listar_cuentas_por_pagar()
        if cuentas:
            st.dataframe(pd.DataFrame(cuentas), use_container_width=True)
        else:
            st.info("No hay cuentas por pagar registradas.")

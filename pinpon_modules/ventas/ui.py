"""Interfaz Streamlit para el módulo ERP de Ventas."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from .controller import VentasController


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


def render_modulo_ventas() -> None:
    controller = VentasController()
    service = controller.service

    st.markdown("## Módulo de Ventas (ERP)")
    st.caption("Gestión base de clientes, cotizaciones, pedidos, facturas emitidas y cobranza.")

    tab_clientes, tab_cotizaciones, tab_pedidos, tab_facturas, tab_cobranza = st.tabs(
        ["Clientes", "Cotizaciones", "Pedidos", "Facturas emitidas", "Cobranza"]
    )

    with tab_clientes:
        with st.form("form_cliente"):
            st.markdown("### Alta de cliente")
            nombre = st.text_input("Nombre")
            rfc = st.text_input("RFC")
            email = st.text_input("Email")
            telefono = st.text_input("Teléfono")
            activo = st.checkbox("Activo", value=True)
            submit = st.form_submit_button("Guardar cliente", use_container_width=True)

        if submit:
            result = controller.crear_cliente_desde_form(
                nombre=nombre,
                rfc=rfc,
                email=email,
                telefono=telefono,
                activo=activo,
            )
            _render_result(result)

        st.markdown("### Listado de clientes")
        clientes = service.listar_clientes()
        if clientes:
            st.dataframe(pd.DataFrame(clientes), use_container_width=True)
        else:
            st.info("No hay clientes registrados.")

    with tab_cotizaciones:
        with st.form("form_cotizacion"):
            st.markdown("### Nueva cotización")
            cliente_id = st.number_input("Cliente ID", min_value=1, step=1)
            fecha = st.text_input("Fecha (YYYY-MM-DD)")
            estado = st.selectbox("Estado", options=["abierta", "convertida", "cerrada"], index=0)
            total = st.number_input("Total", min_value=0.0, step=0.01, format="%.2f")
            moneda = st.text_input("Moneda", value="MXN")
            submit_cot = st.form_submit_button("Guardar cotización", use_container_width=True)

        if submit_cot:
            result = controller.crear_cotizacion_desde_form(
                cliente_id=int(cliente_id),
                fecha=fecha,
                estado=estado,
                total=float(total),
                moneda=moneda,
            )
            _render_result(result)

        st.markdown("### Listado de cotizaciones")
        cotizaciones = service.listar_cotizaciones()
        if cotizaciones:
            st.dataframe(pd.DataFrame(cotizaciones), use_container_width=True)
        else:
            st.info("No hay cotizaciones registradas.")

    with tab_pedidos:
        with st.form("form_pedido"):
            st.markdown("### Crear pedido desde cotización")
            cotizacion_id = st.number_input("Cotización ID", min_value=1, step=1)
            fecha_pedido = st.text_input("Fecha pedido (YYYY-MM-DD)")
            submit_pedido = st.form_submit_button("Generar pedido", use_container_width=True)

        if submit_pedido:
            result = controller.crear_pedido_desde_form(
                cotizacion_id=int(cotizacion_id),
                cliente_id=1,
                fecha=fecha_pedido,
                total=1,
            )
            _render_result(result)

        st.markdown("### Listado de pedidos")
        pedidos = service.listar_pedidos()
        if pedidos:
            st.dataframe(pd.DataFrame(pedidos), use_container_width=True)
        else:
            st.info("No hay pedidos registrados.")

    with tab_facturas:
        with st.form("form_factura_emitida"):
            st.markdown("### Registrar factura emitida")
            pedido_id = st.number_input("Pedido ID", min_value=1, step=1)
            cliente_id_factura = st.number_input("Cliente ID", min_value=1, step=1, key="cliente_id_factura")
            fecha_factura = st.text_input("Fecha factura (YYYY-MM-DD)")
            total_factura = st.number_input("Total factura", min_value=0.0, step=0.01, format="%.2f")
            moneda_factura = st.text_input("Moneda", value="MXN", key="moneda_factura")
            uuid_xml = st.text_input("UUID XML (opcional)")
            submit_factura = st.form_submit_button("Guardar factura", use_container_width=True)

        if submit_factura:
            result = controller.registrar_factura_desde_form(
                pedido_id=int(pedido_id),
                cliente_id=int(cliente_id_factura),
                fecha=fecha_factura,
                total=float(total_factura),
                moneda=moneda_factura,
                uuid_xml=uuid_xml or None,
            )
            _render_result(result)

        with st.form("form_vincular_xml_factura"):
            st.markdown("### Vincular XML a factura")
            factura_id_xml = st.number_input("Factura ID", min_value=1, step=1, key="factura_id_xml")
            uuid_xml_link = st.text_input("UUID XML", key="uuid_xml_factura")
            submit_vincular = st.form_submit_button("Vincular XML", use_container_width=True)

        if submit_vincular:
            try:
                response = service.vincular_xml_a_factura(uuid_xml=uuid_xml_link, factura_id=int(factura_id_xml))
                st.success("XML vinculado correctamente.")
                st.json(response)
            except ValueError as error:
                st.error(str(error))

        st.markdown("### Listado de facturas emitidas")
        facturas = service.listar_facturas_emitidas()
        if facturas:
            st.dataframe(pd.DataFrame(facturas), use_container_width=True)
        else:
            st.info("No hay facturas emitidas registradas.")

    with tab_cobranza:
        with st.form("form_cobranza"):
            st.markdown("### Registrar cobranza")
            factura_id = st.number_input("Factura ID", min_value=1, step=1)
            fecha_cobranza = st.text_input("Fecha cobranza (YYYY-MM-DD)")
            monto_cobranza = st.number_input("Monto", min_value=0.0, step=0.01, format="%.2f")
            metodo_pago = st.text_input("Método de pago")
            referencia = st.text_input("Referencia (opcional)")
            submit_cobranza = st.form_submit_button("Registrar cobranza", use_container_width=True)

        if submit_cobranza:
            result = controller.registrar_cobranza_desde_form(
                factura_id=int(factura_id),
                fecha=fecha_cobranza,
                monto=float(monto_cobranza),
                metodo_pago=metodo_pago,
                referencia=referencia or None,
            )
            _render_result(result)

        st.markdown("### Listado de cobranzas")
        cobranzas = service.listar_cobranzas()
        if cobranzas:
            st.dataframe(pd.DataFrame(cobranzas), use_container_width=True)
        else:
            st.info("No hay cobranzas registradas.")

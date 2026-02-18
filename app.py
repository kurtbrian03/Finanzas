import streamlit as st
import pandas as pd

st.set_page_config(page_title="Finanzas App", page_icon="💰", layout="centered")

st.title("💰 Finanzas")
st.write("Carga tu archivo de Excel para ver métricas y tablas.")

nombre = st.text_input("Escribe tu nombre")
if nombre:
    st.success(f"Hola, {nombre}.")

archivo = st.file_uploader("Sube un archivo Excel", type=["xlsx", "xls"])

if archivo is not None:
    try:
        df = pd.read_excel(archivo)
    except Exception as error:
        st.error(f"No se pudo leer el archivo: {error}")
        st.stop()

    st.subheader("Métricas")
    col1, col2, col3 = st.columns(3)
    col1.metric("Filas", f"{len(df):,}")
    col2.metric("Columnas", f"{len(df.columns):,}")

    columnas_numericas = df.select_dtypes(include="number").columns.tolist()
    if columnas_numericas:
        columna_objetivo = st.selectbox("Columna numérica para análisis", columnas_numericas)
        total = df[columna_objetivo].sum(skipna=True)
        promedio = df[columna_objetivo].mean(skipna=True)
        col3.metric("Total", f"{total:,.2f}")
        st.metric("Promedio", f"{promedio:,.2f}")
    else:
        col3.metric("Total", "N/A")
        st.info("No se detectaron columnas numéricas en el Excel.")

    st.subheader("Tabla")
    st.dataframe(df, use_container_width=True)
else:
    st.info("Sube un archivo de Excel para comenzar.")

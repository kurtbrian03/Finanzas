import pandas as pd
import streamlit as st

st.set_page_config(page_title="Lector de CSV y Excel", page_icon="📊")
st.title("📊 Lector de archivos CSV y Excel")

archivo = st.file_uploader("Sube un archivo CSV o Excel", type=["csv", "xls", "xlsx"])

if archivo is not None:
    try:
        nombre = archivo.name.lower()
        if nombre.endswith(".csv"):
            df = pd.read_csv(archivo)
        else:
            df = pd.read_excel(archivo)

        st.success(f"Archivo cargado correctamente: {archivo.name}")
        st.dataframe(df, use_container_width=True)
        st.caption(f"Filas: {len(df)} | Columnas: {len(df.columns)}")
    except Exception as error:
        st.error(
            f"No se pudo leer el archivo '{archivo.name}' "
            f"({type(error).__name__}): {error}"
        )

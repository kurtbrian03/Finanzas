import streamlit as st
import pandas as pd
from pathlib import Path
from zipfile import ZipFile
from streamlit_pdf_viewer import pdf_viewer

st.set_page_config(page_title="Finanzas App", page_icon="💰", layout="centered")

st.title("💰 Finanzas")
st.write("Explora documentos desde tu carpeta FACTURACION en Dropbox.")

CARPETAS_FORMATO = {
    "EXCEL": {".xlsx", ".xls"},
    "PDF": {".pdf"},
    "POWERSHELL": {".ps1"},
    "PYTHON": {".py"},
    "TEXTO": {".txt"},
    "ZIPPED": {".zip"},
}


def detectar_carpeta_facturacion() -> Path:
    home = Path.home()
    candidatos = [
        home / "Dropbox" / "FACTURACION",
        home / "Documents" / "Dropbox" / "FACTURACION",
        home / "OneDrive" / "Dropbox" / "FACTURACION",
    ]

    for carpeta in candidatos:
        if carpeta.exists() and carpeta.is_dir():
            return carpeta

    return candidatos[0]


def mostrar_preview(categoria: str, archivo: Path) -> None:
    if categoria == "EXCEL":
        try:
            df = pd.read_excel(archivo)
        except Exception as error:
            st.error(f"No se pudo leer el Excel: {error}")
            return

        excel_bytes = archivo.read_bytes()
        st.download_button(
            label="Descargar Excel",
            data=excel_bytes,
            file_name=archivo.name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        st.caption(f"Filas: {len(df):,} | Columnas: {len(df.columns):,}")
        st.dataframe(df.head(100), use_container_width=True)
        return

    if categoria == "TEXTO":
        try:
            contenido = archivo.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            contenido = archivo.read_text(encoding="latin-1", errors="replace")
        except Exception as error:
            st.error(f"No se pudo leer el TXT: {error}")
            return

        txt_bytes = archivo.read_bytes()
        st.download_button(
            label="Descargar TXT",
            data=txt_bytes,
            file_name=archivo.name,
            mime="text/plain",
        )
        st.text_area("Contenido", contenido, height=350)
        return

    if categoria in {"PYTHON", "POWERSHELL"}:
        lenguaje = "python" if categoria == "PYTHON" else "powershell"
        try:
            contenido = archivo.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            contenido = archivo.read_text(encoding="latin-1", errors="replace")
        except Exception as error:
            st.error(f"No se pudo leer el archivo de código: {error}")
            return

        codigo_bytes = archivo.read_bytes()
        st.download_button(
            label=f"Descargar {categoria}",
            data=codigo_bytes,
            file_name=archivo.name,
            mime="text/plain",
        )
        st.code(contenido, language=lenguaje)
        return

    if categoria == "PDF":
        try:
            pdf_bytes = archivo.read_bytes()
        except Exception as error:
            st.error(f"No se pudo abrir el PDF: {error}")
            return

        st.download_button(
            label="Descargar PDF",
            data=pdf_bytes,
            file_name=archivo.name,
            mime="application/pdf",
        )
        pdf_viewer(
            input=pdf_bytes,
            width="100%",
            render_text=True,
            pages_vertical_spacing=2,
        )
        return

    if categoria == "ZIPPED":
        try:
            zip_bytes = archivo.read_bytes()
        except Exception as error:
            st.error(f"No se pudo abrir el ZIP: {error}")
            return

        st.download_button(
            label="Descargar ZIP",
            data=zip_bytes,
            file_name=archivo.name,
            mime="application/zip",
        )

        try:
            with ZipFile(archivo, "r") as zip_file:
                contenido_zip = zip_file.namelist()
        except Exception as error:
            st.error(f"No se pudo leer el contenido del ZIP: {error}")
            return

        if contenido_zip:
            st.write("Contenido del ZIP:")
            st.dataframe(pd.DataFrame({"archivo": contenido_zip}), use_container_width=True)
        else:
            st.info("El archivo ZIP está vacío.")


nombre = st.text_input("Escribe tu nombre")
if nombre:
    st.success(f"Hola, {nombre}.")

st.subheader("Carpeta de documentos")
carpeta_por_defecto = detectar_carpeta_facturacion()
ruta_ingresada = st.text_input("Ruta de FACTURACION", value=str(carpeta_por_defecto))
carpeta = Path(ruta_ingresada)

if not carpeta.exists() or not carpeta.is_dir():
    st.error("La carpeta indicada no existe o no es válida.")
    st.stop()

st.success(f"Carpeta activa: {carpeta}")

archivos_por_categoria = {categoria: [] for categoria in CARPETAS_FORMATO}
for categoria, extensiones in CARPETAS_FORMATO.items():
    carpeta_categoria = carpeta / categoria
    if not carpeta_categoria.exists() or not carpeta_categoria.is_dir():
        continue

    archivos_categoria = sorted(
        [
            p
            for p in carpeta_categoria.rglob("*")
            if p.is_file() and p.suffix.lower() in extensiones
        ],
        key=lambda x: x.name.lower(),
    )
    archivos_por_categoria[categoria] = archivos_categoria

total_permitidos = sum(len(lista) for lista in archivos_por_categoria.values())
st.metric("Archivos detectados", f"{total_permitidos:,}")

tabs = st.tabs(list(CARPETAS_FORMATO.keys()))
for tab, categoria in zip(tabs, CARPETAS_FORMATO.keys()):
    with tab:
        lista_archivos = archivos_por_categoria[categoria]
        if not lista_archivos:
            st.info(f"No hay archivos válidos en FACTURACION/{categoria}.")
            continue

        opciones = {str(a.relative_to(carpeta)): a for a in lista_archivos}
        seleccionado = st.selectbox(
            f"Selecciona un archivo {categoria}",
            list(opciones.keys()),
            key=f"select_{categoria}",
        )
        archivo_actual = opciones[seleccionado]

        st.caption(f"Archivo: {archivo_actual}")
        mostrar_preview(categoria, archivo_actual)

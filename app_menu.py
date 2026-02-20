import subprocess
from pathlib import Path

import streamlit as st


st.set_page_config(page_title="PINPON Orquestador Total", page_icon="🧭", layout="wide")


def run_script(script_relative_path: str) -> str:
    script_path = Path(script_relative_path)
    if not script_path.exists():
        return f"ERROR: No existe el script: {script_relative_path}"

    result = subprocess.run(
        ["pwsh", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    stdout = result.stdout or ""
    stderr = result.stderr or ""
    return f"EXIT CODE: {result.returncode}\n\nSTDOUT:\n{stdout}\n\nSTDERR:\n{stderr}"


st.title("🧭 ORQUESTADOR TOTAL - PINPON")
st.caption("Panel seguro: valida y genera comandos. No instala ni ejecuta automáticamente.")

st.markdown(
    """
    <style>
    .stButton > button {
        width: 100%;
        border-radius: 10px;
        border: 1px solid #d0d7de;
        padding: 0.5rem 0.75rem;
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

buttons = [
    (
        "Prerequisitos",
        "scripts/download_prerequisites.ps1",
        "Valida Python, Node, Git y Poppler. No instala nada. Modo seguro.",
    ),
    (
        "Setup",
        "scripts/setup_environment.ps1",
        "Valida Python, pip, venv y estructura del repo. No ejecuta instalaciones.",
    ),
    (
        "FixReq",
        "scripts/fix_requirements.ps1",
        "Valida requirements.txt, detecta duplicados/conflictos y genera versión limpia.",
    ),
    (
        "Instalar",
        "scripts/install_dependencies.ps1",
        "Genera comandos pip para instalar dependencias. No ejecuta instalaciones.",
    ),
    (
        "PINPON",
        "scripts/init_pinpon.ps1",
        "Valida node/npm y estructura declarativa del agente PINPON.",
    ),
    (
        "Run",
        "scripts/run_project.ps1",
        "Valida entradas y genera el comando final para ejecutar Streamlit.",
    ),
    (
        "RunAll",
        "scripts/run_all.ps1",
        "Orquesta validación completa y muestra flujo integral de comandos.",
    ),
]

st.sidebar.header("⚙️ Acciones")

output_placeholder = st.empty()

for label, script_path, tooltip in buttons:
    if st.sidebar.button(label, help=tooltip, use_container_width=True):
        st.subheader(f"Resultado: {label}")
        output = run_script(script_path)
        output_placeholder.code(output)

st.markdown("---")
st.write("Selecciona una acción en la barra lateral para ejecutar su validación.")

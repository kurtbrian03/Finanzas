# Finanzas

## Configuración del agente declarativo PINPON

El agente **PINPON** es un agente declarativo de soporte financiero que automatiza la configuración del entorno de desarrollo local y asiste en la validación de datos financieros.

### ¿Qué hace el agente?

- Verifica e instala Node.js si no está presente en el sistema.
- Crea los archivos de configuración `agent.yaml` y `agent.local.settings.json` si no existen.
- Crea/verifica las carpetas `knowledge/` y `actions/` necesarias para el agente.
- Provee instrucciones y contexto para tareas financieras (CSV/Excel).

### Scripts disponibles

| Script | Descripción |
|---|---|
| `scripts/unblock_and_setup_agent.ps1` | Desbloquea el instalador de Windows (msiexec/msiserver), luego llama a `setup_agent_environment.ps1` y valida Node/npm. **Requiere permisos de administrador.** |
| `scripts/setup_agent_environment.ps1` | Detecta Node/npm, sugiere instalación si falta, crea archivos de configuración del agente y muestra un resumen del entorno. |

### Cómo ejecutar la tarea de VS Code

1. Abre este repositorio en **VS Code**.
2. Abre la paleta de comandos: `Ctrl+Shift+P` → **Tasks: Run Task**.
3. Selecciona: **Pinpon: Unblock Installer and Setup Agent**.

Esta tarea lanza PowerShell con permisos de administrador y ejecuta `scripts/unblock_and_setup_agent.ps1`.

### Qué esperar tras la ejecución

- Verificación o instalación de Node.js (si falta, se muestra el comando `winget` a ejecutar manualmente).
- Creación de `agent.yaml` con la configuración base del agente.
- Creación de `agent.local.settings.json` con parámetros locales del entorno.
- Creación/verificación de las carpetas `knowledge/` y `actions/`.
- Resumen final con rutas y versiones detectadas.

> **Nota:** La instalación de Node.js requiere ejecutar manualmente el comando sugerido con privilegios de administrador. El agente no instala dependencias por sí solo.

### Estructura del agente

```text
Finanzas/
├── agent.yaml                    # Configuración declarativa del agente PINPON
├── agent.local.settings.json     # Configuración local del entorno
├── knowledge/
│   └── instructions.md           # Instrucciones y alcance del agente
├── actions/                      # Acciones personalizadas (vacío por defecto)
└── scripts/
    ├── unblock_and_setup_agent.ps1
    └── setup_agent_environment.ps1
```

---

## Submódulo PINPON (pinpon-support-ui)

Este repositorio también integra el submódulo Git en la ruta `./pinpon`.

- Repositorio fuente: **`kurtbrian03/pinpon-support-ui`**
- URL HTTPS: `https://github.com/kurtbrian03/pinpon-support-ui.git`

```powershell
# Inicializar y actualizar submódulos
git submodule update --init --recursive

# Clonado inicial con submódulos
git clone --recurse-submodules <URL_DE_FINANZAS>
```

> Nota: no se incluyen ni exponen credenciales reales en este repositorio.

## App Streamlit: lector de CSV y Excel

### Instalación

```powershell
pip install -r requirements.txt
```

### Ejecución

```powershell
streamlit run streamlit_app.py
```

# Finanzas

[![Portal documental](https://img.shields.io/badge/Portal-Documentaci%C3%B3n-0A66C2?style=for-the-badge)](docs/INDEX_DOCUMENTACION.md)
[![Versión estable](https://img.shields.io/badge/Versi%C3%B3n-v3-2EA043?style=for-the-badge)](docs/versions/LATEST_VERSION.txt)
[![Automatización](https://img.shields.io/badge/Automatizaci%C3%B3n-Docs%20Script-6F42C1?style=for-the-badge)](docs/scripts/regenerar_documentacion.py)
[![Changelog](https://img.shields.io/badge/Changelog-Documentaci%C3%B3n-F59E0B?style=for-the-badge)](docs/CHANGELOG_DOCUMENTACION.md)
[![Licencia](https://img.shields.io/badge/Licencia-Pendiente-9CA3AF?style=for-the-badge)](docs/INDEX_DOCUMENTACION.md#-7-pr%C3%B3ximos-pasos-sugeridos)

Plataforma modular para análisis documental (PDF/Excel), validación fiscal, descargas controladas y trazabilidad operativa.

## 1. Introducción

Este repositorio implementa una arquitectura multiarchivo orientada a mantenibilidad, separación de responsabilidades y evolución incremental. Incluye integración con submódulo `PINPON` para flujo operativo complementario.

## 2. Arquitectura del sistema

Capas principales:

- **UI**: layout, navegación, componentes y mensajes.
- **Core**: router, estado, ciclo de vida y bus de eventos.
- **Analysis**: análisis de PDF/Excel, extracción de tablas y entidades.
- **Validation**: RFC, folios, reglas SAT y homoclave.
- **Downloads**: generación de descargas manuales y empaquetado.
- **History**: auditoría y persistencia de acciones.
- **Config**: constantes, entorno y parámetros globales.
- **Utils**: utilidades compartidas para archivos, errores y formato.

## 3. Características principales

- Arquitectura modular orientada a dominio.
- Flujo de datos controlado por `router` y `state_manager`.
- Descargas exclusivamente manuales.
- Documentación maestra multi-formato centralizada en `docs/`.
- Integración de submódulo `PINPON` sin duplicar código.

## 4. Portal documental

- Índice principal: [docs/INDEX_DOCUMENTACION.md](docs/INDEX_DOCUMENTACION.md)
- Prompt maestro total: [docs/PROMPT_MAESTRO_TOTAL_SISTEMA_DOCUMENTAL.txt](docs/PROMPT_MAESTRO_TOTAL_SISTEMA_DOCUMENTAL.txt)

## 5. Estructura del proyecto

```text
app.py
analysis/
config/
core/
docs/
downloads/
history/
ui/
utils/
validation/
pinpon/ (submódulo)
```

## 6. Cómo iniciar el proyecto

### Requisitos

- Python 3.11+
- Entorno virtual activo (`.venv`)

### Ejecución

```powershell
& "./.venv/Scripts/python.exe" -m streamlit run app.py
```

## 7. Cómo contribuir

1. Crear cambios en rama de trabajo.
2. Mantener consistencia de arquitectura y documentación.
3. Si cambias el sistema documental, actualiza:
	- [docs/INDEX_DOCUMENTACION.md](docs/INDEX_DOCUMENTACION.md)
	- [docs/CHANGELOG_DOCUMENTACION.md](docs/CHANGELOG_DOCUMENTACION.md)
4. Abrir PR con descripción de alcance e impacto.

### Integración de submódulo PINPON

```powershell
# Inicializar/actualizar submódulos
git submodule update --init --recursive

# Ejecutar scripts de PINPON desde Finanzas
pwsh ./pinpon/<script>.ps1
```

## 8. Configuración del agente declarativo PINPON

El agente declarativo PINPON permite a GitHub Copilot Chat operar con contexto específico de este repositorio: análisis documental, validación fiscal y automatización operativa.

### Archivos clave del agente

| Archivo / Directorio | Rol |
|---|---|
| `agent.yaml` | Configuración principal del agente (nombre, instrucciones, knowledge, actions) |
| `agent.local.settings.json` | Ajustes locales del entorno (logLevel, rutas) |
| `knowledge/instructions.md` | Prompt de sistema del agente (alcance y directrices) |
| `knowledge/` | Archivos de contexto que el agente puede consultar |
| `actions/` | Definiciones de acciones externas (OpenAPI, si aplica) |
| `scripts/unblock_and_setup_agent.ps1` | Desbloquea Windows Installer y lanza el setup del agente |
| `scripts/setup_agent_environment.ps1` | Detecta/instala Node.js y verifica los archivos base del agente |

### Scripts de setup

- **`scripts/unblock_and_setup_agent.ps1`** — ejecutar con privilegios de administrador. Hace cinco pasos en orden:
  1. Detiene procesos `msiexec` bloqueantes.
  2. Reinicia el servicio `msiserver`.
  3. Verifica que Windows Installer esté libre.
  4. Llama a `scripts/setup_agent_environment.ps1`.
  5. Valida la presencia de `node` y `npm`.

- **`scripts/setup_agent_environment.ps1`** — configura el entorno del agente:
  - Detecta `node`/`npm`; intenta instalar Node.js LTS vía `winget` si falta.
  - Crea `agent.yaml`, `agent.local.settings.json`, `knowledge/` y `actions/` si no existen.
  - Muestra un resumen final del entorno.

### Cómo ejecutar desde VS Code

En VS Code abre la paleta de tareas (`Ctrl+Shift+P` → **Tasks: Run Task**) y selecciona:

```
Pinpon: Unblock Installer and Setup Agent
```

La tarea lanza `scripts/unblock_and_setup_agent.ps1` con privilegios elevados (`Start-Process pwsh -Verb RunAs`).

### Qué esperar al finalizar

- `node` y `npm` detectados (o instrucciones para instalarlos manualmente).
- `agent.yaml`, `agent.local.settings.json`, `knowledge/` y `actions/` presentes en la raíz del repo.
- Salida de consola con estado `OK` para cada componente.

> **Nota:** Si `node` no está instalado y `winget` no está disponible, descarga Node.js LTS manualmente desde <https://nodejs.org> e instálalo como administrador. Luego vuelve a ejecutar la tarea.

## 9. Licencia

Pendiente de definición formal (`MIT` o `Privada`, según lineamiento del proyecto).

## 10. Auditoría en CI/CD

Ejecución recomendada de auditoría automática en pipeline:

```powershell
# 1) Generar auditoría + profiling en corrida actual
& "./.venv/Scripts/python.exe" integrar_dropbox.py --audit-search --profiling --verbose

# 2) Comparar snapshot anterior vs actual y fallar si hay degradación
& "./.venv/Scripts/python.exe" -m dropbox_integration.audit_ci `
	--snapshot-a "docs/versions/latest/dropbox/analytics/dropbox_search_audit_snapshot_prev.json" `
	--snapshot-b "docs/versions/latest/dropbox/analytics/dropbox_search_audit_snapshot.json" `
	--name-a "prev" --name-b "current" `
	--out-dir "docs/reportes" `
	--max-down-pct 35 `
	--max-negative-delta-score 0.02
```

El script `dropbox_integration/audit_ci.py` retorna `exit 0` si la política pasa y `exit 1` si detecta degradación por encima de umbral.

## 11. Contacto o equipo

Equipo de mantenimiento del repositorio `Finanzas` (owner y maintainers del proyecto).

---

Para lineamientos técnicos detallados, revisar también:

- [docs/MANUAL_TECNICO.md](docs/MANUAL_TECNICO.md)
- [docs/ROADMAP.md](docs/ROADMAP.md)
- [docs/ARCHITECTURE_DIAGRAM.md](docs/ARCHITECTURE_DIAGRAM.md)

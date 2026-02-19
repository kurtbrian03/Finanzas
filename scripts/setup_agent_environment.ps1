# scripts/setup_agent_environment.ps1
# Detecta Node/npm, crea archivos base del agente PINPON y verifica carpetas.
# Llamado por unblock_and_setup_agent.ps1 (no requiere elevación directa).

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Raíz del repositorio (un nivel arriba de /scripts)
$repoRoot = Split-Path $PSScriptRoot -Parent

Write-Host "=== PINPON: Detectando Node y npm ===" -ForegroundColor Cyan

# ── 1) Detectar node/npm ──────────────────────────────────────────────────────
$nodeCmd = Get-Command node -ErrorAction SilentlyContinue
$npmCmd  = Get-Command npm  -ErrorAction SilentlyContinue

if (-not $nodeCmd) {
    Write-Warning "node no encontrado en PATH."
    Write-Host "Para instalar Node.js con winget, ejecuta como administrador:" -ForegroundColor Yellow
    Write-Host '    winget install --id OpenJS.NodeJS.LTS --source winget' -ForegroundColor Yellow
    Write-Host "Luego cierra y vuelve a abrir la terminal para que el PATH se actualice." -ForegroundColor Yellow
} else {
    $nodeVersion = node --version
    Write-Host "node: $nodeVersion  ($($nodeCmd.Source))" -ForegroundColor Green
}

if (-not $npmCmd) {
    Write-Warning "npm no encontrado en PATH. Normalmente se instala junto con Node."
} else {
    $npmVersion = npm --version
    Write-Host "npm:  $npmVersion  ($($npmCmd.Source))" -ForegroundColor Green
}

# ── 2) Crear/verificar agent.yaml ─────────────────────────────────────────────
$agentYaml = Join-Path $repoRoot 'agent.yaml'
if (-not (Test-Path $agentYaml)) {
    Write-Host "`nCreando agent.yaml..." -ForegroundColor Yellow
    @'
name: pinpon-agent
instructions: knowledge/instructions.md
knowledge:
  - knowledge/
actions:
  - actions/
'@ | Set-Content -Path $agentYaml -Encoding UTF8
    Write-Host "agent.yaml creado." -ForegroundColor Green
} else {
    Write-Host "`nagent.yaml ya existe. Sin cambios." -ForegroundColor Green
}

# ── 3) Crear/verificar agent.local.settings.json ──────────────────────────────
$agentSettings = Join-Path $repoRoot 'agent.local.settings.json'
if (-not (Test-Path $agentSettings)) {
    Write-Host "Creando agent.local.settings.json..." -ForegroundColor Yellow
    @'
{
  "agentName": "pinpon-agent",
  "environment": "local",
  "knowledgeDir": "knowledge",
  "actionsDir": "actions",
  "logLevel": "info"
}
'@ | Set-Content -Path $agentSettings -Encoding UTF8
    Write-Host "agent.local.settings.json creado." -ForegroundColor Green
} else {
    Write-Host "agent.local.settings.json ya existe. Sin cambios." -ForegroundColor Green
}

# ── 4) Crear/verificar knowledge/ ─────────────────────────────────────────────
$knowledgeDir = Join-Path $repoRoot 'knowledge'
if (-not (Test-Path $knowledgeDir)) {
    New-Item -ItemType Directory -Path $knowledgeDir | Out-Null
    Write-Host "Carpeta knowledge/ creada." -ForegroundColor Green
} else {
    Write-Host "Carpeta knowledge/ ya existe." -ForegroundColor Green
}

$instructionsFile = Join-Path $knowledgeDir 'instructions.md'
if (-not (Test-Path $instructionsFile)) {
    Write-Host "Creando knowledge/instructions.md..." -ForegroundColor Yellow
    @'
# Instrucciones del agente PINPON

## Descripcion
PINPON es un agente declarativo de soporte financiero integrado en el repositorio Finanzas.
Su objetivo es asistir en la validacion, automatizacion y gestion de datos financieros.

## Alcance
- Finanzas: lectura y validacion de archivos CSV/Excel con datos financieros.
- Automatizacion: configuracion del entorno local de desarrollo.
- Soporte: orientacion sobre el uso de scripts y tareas de VS Code en este repositorio.

## Limitaciones
- El agente no ejecuta scripts por si mismo; depende de la interaccion del usuario.
- La instalacion de dependencias (Node, winget, etc.) requiere accion manual del usuario.
- No almacena ni expone credenciales; todo procesamiento es local.
'@ | Set-Content -Path $instructionsFile -Encoding UTF8
    Write-Host "knowledge/instructions.md creado." -ForegroundColor Green
} else {
    Write-Host "knowledge/instructions.md ya existe." -ForegroundColor Green
}

# ── 5) Crear/verificar actions/ ───────────────────────────────────────────────
$actionsDir = Join-Path $repoRoot 'actions'
if (-not (Test-Path $actionsDir)) {
    New-Item -ItemType Directory -Path $actionsDir | Out-Null
    Write-Host "Carpeta actions/ creada." -ForegroundColor Green
} else {
    Write-Host "Carpeta actions/ ya existe." -ForegroundColor Green
}

# ── 6) Resumen final ──────────────────────────────────────────────────────────
Write-Host "`n=== PINPON: Resumen del entorno ===" -ForegroundColor Cyan
Write-Host "Raiz del repositorio : $repoRoot"
Write-Host "agent.yaml           : $agentYaml"
Write-Host "agent.local.settings : $agentSettings"
Write-Host "knowledge/           : $knowledgeDir"
Write-Host "actions/             : $actionsDir"
if ($nodeCmd) {
    Write-Host "Node.js              : $(node --version)"
} else {
    Write-Host "Node.js              : NO INSTALADO" -ForegroundColor Red
}

exit 0

param(
    [string]$AgentYamlPath = "agent.yaml",
    [string]$AgentLocalSettingsPath = "agent.local.settings.json"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Info([string]$m) { Write-Host "[INFO] $m" -ForegroundColor Cyan }
function Write-Warn([string]$m) { Write-Host "[WARN] $m" -ForegroundColor Yellow }
function Write-Err([string]$m)  { Write-Host "[ERR ] $m" -ForegroundColor Red }
function Write-Ok([string]$m)   { Write-Host "[ OK ] $m" -ForegroundColor Green }

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\")).Path
$agentYaml = Join-Path $repoRoot $AgentYamlPath
$agentLocal = Join-Path $repoRoot $AgentLocalSettingsPath
$knowledgeDir = Join-Path $repoRoot "knowledge"
$actionsDir = Join-Path $repoRoot "actions"

Write-Host "=== ORQUESTADOR: INIT PINPON (MODO GUIADO) ===" -ForegroundColor Magenta
Write-Host "Este script NO instala nada. Solo valida y genera instrucciones/plantillas." -ForegroundColor DarkYellow

$nodeCmd = Get-Command node -ErrorAction SilentlyContinue
$npmCmd = Get-Command npm -ErrorAction SilentlyContinue
if ($nodeCmd) { Write-Ok "Node detectado: $(& node --version)" }
else {
    Write-Warn "Node NO detectado"
    Write-Host "Descarga: https://nodejs.org/en/download"
    Write-Host "Comando: winget install -e --id OpenJS.NodeJS.LTS"
}
if ($npmCmd) { Write-Ok "npm detectado: $(& npm --version)" }
else { Write-Warn "npm NO detectado" }

Write-Host "`n=== ARCHIVOS/CARPETAS PINPON ===" -ForegroundColor Cyan

if (Test-Path $agentYaml) {
    Write-Ok "Existe: $AgentYamlPath"
} else {
    Write-Warn "Falta: $AgentYamlPath"
    Write-Host "Plantilla sugerida:"
    Write-Host "name: pinpon-agent"
    Write-Host "description: Agente declarativo PINPON"
    Write-Host "version: \"1.0.0\""
    Write-Host "instructions: knowledge/instructions.md"
    Write-Host "knowledge:"
    Write-Host "  - knowledge"
    Write-Host "actions:"
    Write-Host "  - actions"
}

if (Test-Path $agentLocal) {
    Write-Ok "Existe: $AgentLocalSettingsPath"
} else {
    Write-Warn "Falta: $AgentLocalSettingsPath"
    Write-Host "Plantilla sugerida:"
    Write-Host "{\"agentName\":\"pinpon-agent\",\"environment\":\"local\",\"knowledgeDir\":\"knowledge\",\"actionsDir\":\"actions\",\"logLevel\":\"info\"}"
}

if (Test-Path $knowledgeDir) { Write-Ok "Existe: knowledge/" } else { Write-Warn "Falta: knowledge/ (crear: New-Item -ItemType Directory -Path knowledge)" }
if (Test-Path $actionsDir) { Write-Ok "Existe: actions/" } else { Write-Warn "Falta: actions/ (crear: New-Item -ItemType Directory -Path actions)" }

Write-Info "init_pinpon finalizado en modo seguro."

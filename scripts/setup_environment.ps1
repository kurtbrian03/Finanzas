param(
    [string]$PythonExe = "python",
    [string]$VenvPath = ".venv"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Info([string]$m) { Write-Host "[INFO] $m" -ForegroundColor Cyan }
function Write-Warn([string]$m) { Write-Host "[WARN] $m" -ForegroundColor Yellow }
function Write-Err([string]$m)  { Write-Host "[ERR ] $m" -ForegroundColor Red }
function Write-Ok([string]$m)   { Write-Host "[ OK ] $m" -ForegroundColor Green }

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\")).Path
Set-Location $repoRoot

Write-Host "=== ORQUESTADOR: SETUP ENTORNO (MODO INSTRUCCIONES) ===" -ForegroundColor Magenta
Write-Host "Este script NO crea ni instala nada. Solo valida y propone comandos." -ForegroundColor DarkYellow

$pyCmd = Get-Command $PythonExe -ErrorAction SilentlyContinue
if (-not $pyCmd) {
    Write-Err "Python no detectado en PATH"
    Write-Host "Descarga: https://www.python.org/downloads/windows/"
    Write-Host "Comando: winget install -e --id Python.Python.3.11"
    exit 1
}

Write-Ok "Python detectado: $(& $PythonExe --version)"

try {
    $pipVersion = & $PythonExe -m pip --version
    Write-Ok "pip detectado: $pipVersion"
} catch {
    Write-Err "pip no detectado"
    Write-Host "Comando sugerido: $PythonExe -m ensurepip --upgrade"
}

$venvFullPath = Join-Path $repoRoot $VenvPath
if (Test-Path $venvFullPath) {
    Write-Ok "Entorno virtual detectado: $venvFullPath"
} else {
    Write-Warn "No existe entorno virtual: $venvFullPath"
    Write-Host "Comando sugerido para crearlo (NO ejecutado):"
    Write-Host "  $PythonExe -m venv $VenvPath"
}

Write-Host "`n=== VALIDACIÓN ESTRUCTURA REPO ===" -ForegroundColor Cyan
$required = @(
    "requirements.txt",
    "app.py",
    "scripts/fix_requirements.ps1",
    "scripts/install_dependencies.ps1",
    "scripts/run_project.ps1",
    "agent.yaml",
    "agent.local.settings.json",
    "knowledge",
    "actions"
)
foreach ($item in $required) {
    if (Test-Path (Join-Path $repoRoot $item)) { Write-Ok "OK: $item" }
    else { Write-Warn "FALTA: $item" }
}

Write-Info "Fin de setup_environment en modo seguro."

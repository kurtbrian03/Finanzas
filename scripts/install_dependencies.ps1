param(
    [string]$VenvPath = ".venv",
    [string]$RequirementsPath = "requirements.txt"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Info([string]$m) { Write-Host "[INFO] $m" -ForegroundColor Cyan }
function Write-Warn([string]$m) { Write-Host "[WARN] $m" -ForegroundColor Yellow }
function Write-Err([string]$m)  { Write-Host "[ERR ] $m" -ForegroundColor Red }
function Write-Ok([string]$m)   { Write-Host "[ OK ] $m" -ForegroundColor Green }

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\")).Path
$reqFile = Join-Path $repoRoot $RequirementsPath
$pythonExe = Join-Path $repoRoot "$VenvPath\Scripts\python.exe"

Write-Host "=== ORQUESTADOR: INSTALL DEPENDENCIES (SOLO COMANDOS) ===" -ForegroundColor Magenta
Write-Host "Este script NO instala nada. Solo imprime comandos exactos." -ForegroundColor DarkYellow

if (-not (Test-Path $reqFile)) {
    Write-Err "No existe requirements: $RequirementsPath"
    exit 1
}

if (Test-Path $pythonExe) {
    Write-Ok "Python de venv detectado: $pythonExe"
} else {
    Write-Warn "No existe venv o python.exe de venv"
}

Write-Host "`n=== COMANDOS SUGERIDOS (NO EJECUTADOS) ===" -ForegroundColor Cyan
Write-Host "1) python -m pip install --upgrade pip setuptools wheel"
Write-Host "2) python -m pip install -r $RequirementsPath"
Write-Host "3) python -m pip check"
Write-Host "4) python -m pip list"

Write-Info "install_dependencies finalizado en modo seguro."

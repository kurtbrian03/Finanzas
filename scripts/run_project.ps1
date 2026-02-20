param(
    [string]$VenvPath = ".venv",
    [string]$EntryFile = "app.py"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Info([string]$m) { Write-Host "[INFO] $m" -ForegroundColor Cyan }
function Write-Warn([string]$m) { Write-Host "[WARN] $m" -ForegroundColor Yellow }
function Write-Err([string]$m)  { Write-Host "[ERR ] $m" -ForegroundColor Red }
function Write-Ok([string]$m)   { Write-Host "[ OK ] $m" -ForegroundColor Green }

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\")).Path
$venvPython = Join-Path $repoRoot "$VenvPath\Scripts\python.exe"
$entry = Join-Path $repoRoot $EntryFile

Write-Host "=== ORQUESTADOR: RUN PROJECT (SOLO COMANDO) ===" -ForegroundColor Magenta
Write-Host "Este script NO ejecuta Streamlit. Solo valida y muestra comando." -ForegroundColor DarkYellow

if (Test-Path $venvPython) { Write-Ok "Python venv detectado" } else { Write-Warn "No existe $VenvPath" }
if (Test-Path $entry) { Write-Ok "Archivo entrada detectado: $EntryFile" } else { Write-Err "No existe $EntryFile" }

Write-Host "`n=== COMANDO FINAL (NO EJECUTADO) ===" -ForegroundColor Cyan
Write-Host "$venvPython -m streamlit run $EntryFile"

Write-Info "run_project finalizado en modo seguro."

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Step([string]$m) { Write-Host "`n=== $m ===" -ForegroundColor Green }

$repoRoot = (Resolve-Path $PSScriptRoot).Path
$scriptsDir = Join-Path $repoRoot "scripts"

$downloadPrereq = Join-Path $scriptsDir "download_prerequisites.ps1"
$setupEnv = Join-Path $scriptsDir "setup_environment.ps1"
$fixReq = Join-Path $scriptsDir "fix_requirements.ps1"
$installDeps = Join-Path $scriptsDir "install_dependencies.ps1"
$initPinpon = Join-Path $scriptsDir "init_pinpon.ps1"
$runProject = Join-Path $scriptsDir "run_project.ps1"

Write-Host "=== ORQUESTADOR TOTAL (NO EJECUTA INSTALACIONES) ===" -ForegroundColor Magenta
Write-Host "Este script solo imprime el flujo y lanza scripts en modo seguro." -ForegroundColor DarkYellow

Write-Step "1) Validar prerequisitos"
& pwsh -NoProfile -ExecutionPolicy Bypass -File $downloadPrereq

Write-Step "2) Validar entorno"
& pwsh -NoProfile -ExecutionPolicy Bypass -File $setupEnv

Write-Step "3) Validar y limpiar requirements"
& pwsh -NoProfile -ExecutionPolicy Bypass -File $fixReq

Write-Step "4) Generar comandos de instalación"
& pwsh -NoProfile -ExecutionPolicy Bypass -File $installDeps

Write-Step "5) Validar/init PINPON"
& pwsh -NoProfile -ExecutionPolicy Bypass -File $initPinpon

Write-Step "6) Generar comando final de ejecución"
& pwsh -NoProfile -ExecutionPolicy Bypass -File $runProject

Write-Host "`nORQUESTADOR TOTAL finalizado (sin instalaciones, sin ejecución de app)." -ForegroundColor Green

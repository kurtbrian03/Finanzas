# scripts/unblock_and_setup_agent.ps1
# Desbloquea el instalador de Windows y configura el entorno del agente PINPON.
# Debe ejecutarse como administrador (Start-Process pwsh -Verb RunAs).

#Requires -RunAsAdministrator

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Write-Host "=== PINPON: Desbloqueo del instalador ===" -ForegroundColor Cyan

# 1) Detener msiexec si está en ejecución
$msiProcesses = Get-Process -Name msiexec -ErrorAction SilentlyContinue
if ($msiProcesses) {
    Write-Host "Deteniendo procesos msiexec en ejecución..." -ForegroundColor Yellow
    $msiProcesses | Stop-Process -Force
    Start-Sleep -Seconds 2
} else {
    Write-Host "No hay procesos msiexec activos." -ForegroundColor Green
}

# 2) Reiniciar el servicio msiserver
Write-Host "Reiniciando servicio msiserver..." -ForegroundColor Yellow
try {
    Restart-Service -Name msiserver -Force -ErrorAction Stop
    Write-Host "Servicio msiserver reiniciado correctamente." -ForegroundColor Green
} catch {
    Write-Warning "No se pudo reiniciar msiserver: $_"
}

# 3) Verificar si el instalador sigue ocupado (código de error 2)
$msiExec = Get-Process -Name msiexec -ErrorAction SilentlyContinue
if ($msiExec) {
    Write-Error "El instalador sigue ocupado después del intento de desbloqueo."
    exit 2
}
Write-Host "Instalador libre. Continuando con la configuración del entorno..." -ForegroundColor Green

# 4) Llamar al script de configuración del entorno del agente
$setupScript = Join-Path $PSScriptRoot 'setup_agent_environment.ps1'
if (-not (Test-Path $setupScript)) {
    Write-Error "No se encontró el script de configuración: $setupScript"
    exit 3
}

Write-Host "`n=== PINPON: Configuración del entorno del agente ===" -ForegroundColor Cyan
try {
    & $setupScript
    $setupExitCode = $LASTEXITCODE
} catch {
    Write-Error "Error al ejecutar setup_agent_environment.ps1: $_"
    exit 4
}

if ($setupExitCode -eq 3) {
    Write-Error "setup_agent_environment.ps1 reportó un error crítico (código 3)."
    exit 3
} elseif ($setupExitCode -eq 4) {
    Write-Error "setup_agent_environment.ps1 reportó un error de configuración (código 4)."
    exit 4
} elseif ($setupExitCode -ne 0) {
    Write-Warning "setup_agent_environment.ps1 terminó con código inesperado: $setupExitCode"
}

# 5) Validar Node y npm al final
Write-Host "`n=== PINPON: Validacion de Node/npm ===" -ForegroundColor Cyan
$nodeCmd = Get-Command node -ErrorAction SilentlyContinue
$npmCmd  = Get-Command npm  -ErrorAction SilentlyContinue

if ($nodeCmd) {
    $nodeVersion = node --version
    Write-Host "node encontrado: $nodeVersion  ($($nodeCmd.Source))" -ForegroundColor Green
} else {
    Write-Warning "node no encontrado en PATH. Ejecuta setup_agent_environment.ps1 para instalarlo."
}

if ($npmCmd) {
    $npmVersion = npm --version
    Write-Host "npm  encontrado: $npmVersion  ($($npmCmd.Source))" -ForegroundColor Green
} else {
    Write-Warning "npm no encontrado en PATH."
}

Write-Host "`n=== PINPON: Proceso completado ===" -ForegroundColor Cyan
exit 0

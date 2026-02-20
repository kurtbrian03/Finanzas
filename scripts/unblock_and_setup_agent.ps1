# scripts/unblock_and_setup_agent.ps1
param(
    [switch]$AllowServiceRestart,
    [switch]$SkipNodeCheck
)

Write-Host "=== PINPON: Precheck de Windows Installer + setup del agente ===" -ForegroundColor Cyan

# 1. Diagnóstico de msiexec (sin detener procesos por defecto)
Write-Host "`n[1/3] Revisando estado de Windows Installer (msiexec)..." -ForegroundColor Yellow
$msiProcesses = Get-Process msiexec -ErrorAction SilentlyContinue
if ($msiProcesses) {
    Write-Host "Se detectó Windows Installer activo ($($msiProcesses.Count) proceso(s))." -ForegroundColor DarkYellow
    Write-Host "No se realizará ninguna acción destructiva automáticamente." -ForegroundColor DarkYellow
    if ($AllowServiceRestart) {
        Write-Host "Intentando reiniciar msiserver por solicitud explícita (-AllowServiceRestart)..." -ForegroundColor Yellow
        try {
            Stop-Service msiserver -Force -ErrorAction Stop
            Start-Service msiserver -ErrorAction Stop
            Write-Host "msiserver reiniciado correctamente." -ForegroundColor Green
        } catch {
            Write-Host "No fue posible reiniciar msiserver sin privilegios suficientes: $_" -ForegroundColor Red
            exit 2
        }
    }
} else {
    Write-Host "Windows Installer no está ocupado." -ForegroundColor Green
}

# 2. Ejecutar setup del agente
Write-Host "`n[2/3] Ejecutando setup del agente (scripts/setup_agent_environment.ps1)..." -ForegroundColor Cyan
$setupScript = Join-Path -Path $PSScriptRoot -ChildPath "setup_agent_environment.ps1"
if (-not (Test-Path $setupScript)) {
    Write-Host "No se encontró setup_agent_environment.ps1: $setupScript" -ForegroundColor Red
    exit 3
}

try {
    pwsh -NoProfile -ExecutionPolicy Bypass -File $setupScript
} catch {
    Write-Host "Error al ejecutar setup_agent_environment.ps1: $_" -ForegroundColor Red
    exit 4
}

# 3. Validación opcional de Node/npm
Write-Host "`n[3/3] Verificando herramientas Node/npm..." -ForegroundColor Yellow
if ($SkipNodeCheck) {
    Write-Host "Validación de Node/npm omitida por -SkipNodeCheck." -ForegroundColor DarkGray
} else {
    try {
        $node = & node --version 2>$null
        $npm = & npm --version 2>$null
        if ($node) { Write-Host "node version: $node" -ForegroundColor Green } else { Write-Host "node no detectado" -ForegroundColor DarkYellow }
        if ($npm)  { Write-Host "npm version: $npm" -ForegroundColor Green } else { Write-Host "npm no detectado" -ForegroundColor DarkYellow }
    } catch {
        Write-Host "No se pudo validar node/npm: $_" -ForegroundColor DarkYellow
    }
}

Write-Host "`n=== PINPON: Proceso completado (modo seguro) ===" -ForegroundColor Cyan

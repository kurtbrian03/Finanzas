# scripts/unblock_and_setup_agent.ps1
Write-Host "=== PINPON: Desbloqueo de Windows Installer y ejecución de setup del agente ===" -ForegroundColor Cyan

# 1. Detener procesos msiexec si existen
Write-Host "`n[1/5] Buscando y deteniendo procesos msiexec..." -ForegroundColor Yellow
Get-Process msiexec -ErrorAction SilentlyContinue | ForEach-Object {
    Write-Host "Deteniendo proceso MSI bloqueante: $($_.Id) $($_.ProcessName)" -ForegroundColor Red
    Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
}

# 2. Reiniciar servicio Windows Installer
Write-Host "`n[2/5] Reiniciando servicio msiserver..." -ForegroundColor Yellow
Try {
    Stop-Service msiserver -Force -ErrorAction Stop
} Catch {
    Write-Host "No se pudo detener msiserver o ya estaba detenido: $_" -ForegroundColor DarkYellow
}
Start-Service msiserver -ErrorAction SilentlyContinue
Write-Host "Servicio msiserver reiniciado o ya activo." -ForegroundColor Green

# 3. Comprobar si Windows Installer sigue ocupado
Write-Host "`n[3/5] Verificando si Windows Installer sigue ocupado..." -ForegroundColor Yellow
$installerBusy = $false
Try {
    $msiProcesses = Get-Process msiexec -ErrorAction SilentlyContinue
    if ($msiProcesses) { $installerBusy = $true }
} Catch {
    $installerBusy = $true
}

if ($installerBusy) {
    Write-Host "Windows Installer sigue ocupado. Reinicia Windows y vuelve a ejecutar este script." -ForegroundColor Red
    exit 2
} else {
    Write-Host "Windows Installer está libre." -ForegroundColor Green
}

# 4. Ejecutar setup del agente (ruta relativa al repo)
Write-Host "`n[4/5] Ejecutando setup del agente (scripts/setup_agent_environment.ps1)..." -ForegroundColor Cyan
$setupScript = Join-Path -Path (Get-Location) -ChildPath "scripts/setup_agent_environment.ps1"
if (-Not (Test-Path $setupScript)) {
    Write-Host "No se encontró scripts/setup_agent_environment.ps1 en el directorio actual: $setupScript" -ForegroundColor Red
    exit 3
}

Try {
    pwsh -NoProfile -ExecutionPolicy Bypass -File $setupScript
} Catch {
    Write-Host "Error al ejecutar setup_agent_environment.ps1: $_" -ForegroundColor Red
    exit 4
}

# 5. Validación final de Node/npm
Write-Host "`n[5/5] Validando instalación de Node/npm..." -ForegroundColor Yellow
Try {
    $node = & node --version 2>$null
    $npm = & npm --version 2>$null
    if ($node) { Write-Host "node version: $node" -ForegroundColor Green } else { Write-Host "node no detectado" -ForegroundColor Red }
    if ($npm)  { Write-Host "npm version: $npm" -ForegroundColor Green } else { Write-Host "npm no detectado" -ForegroundColor Red }
} Catch {
    Write-Host "No se pudo validar node/npm: $_" -ForegroundColor Red
}

Write-Host "`n=== PINPON: Proceso completado ===" -ForegroundColor Cyan

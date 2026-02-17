# pinpon.profile.ps1
# Perfil de PowerShell para el proyecto PINPON. No contiene secretos.
# Hace: activa .venv si existe, define rutas y funciones utilitarias.

$PinponRoot = Split-Path -Parent (Split-Path $MyInvocation.MyCommand.Path)
$PinponVenv = Join-Path $PinponRoot ".venv"
$PinponActivate = Join-Path $PinponVenv "Scripts/Activate.ps1"

$env:PINPON_ROOT = $PinponRoot
$env:PINPON_DATA = Join-Path $PinponRoot "datos"
$env:PINPON_CONFIG = Join-Path $PinponRoot "config"

function pinpon-activate {
    if(Test-Path $PinponActivate){ . $PinponActivate; Write-Host "[PINPON] .venv activado" -ForegroundColor Cyan }
    else { Write-Host "[PINPON] No se encontro .venv" -ForegroundColor Yellow }
}

function pinpon-status {
    Write-Host "[PINPON] root: $PinponRoot"
    Write-Host "[PINPON] venv: $(if($env:VIRTUAL_ENV){$env:VIRTUAL_ENV}else{"no activo"})"
    Write-Host "[PINPON] python: $(Get-Command python -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source)" 
}

function pinpon-paths {
    Write-Host "config => $env:PINPON_CONFIG"
    Write-Host "datos  => $env:PINPON_DATA"
    Write-Host "ops    => $(Join-Path $PinponRoot 'ops')"
    Write-Host "logs   => $(Join-Path $PinponRoot 'logs')"
}

# Activacion automatica si existe .venv
if(Test-Path $PinponActivate){ pinpon-activate }

Write-Host "PINPON listo" -ForegroundColor Green
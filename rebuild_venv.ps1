# rebuild_venv.ps1
# Recrea el entorno virtual .venv desde cero con confirmacion, instala dependencias y valida python/pip.

param(
    [switch]$yes,
    [string]$root = (Get-Location).Path
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Info($m){ Write-Host "[INFO] $m" -ForegroundColor Cyan }
function Write-Warn($m){ Write-Host "[WARN] $m" -ForegroundColor Yellow }
function Write-Err ($m){ Write-Host "[ERR ] $m" -ForegroundColor Red }

$logFile = Join-Path $root "rebuild_venv.log"
function Log($m){ $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"; "$ts $m" | Out-File -FilePath $logFile -Encoding utf8 -Append }

function Confirm-Action($msg){ if($yes){ return $true } $r = Read-Host "$msg (y/N)"; return $r -match '^(y|Y|s|S)$' }

$venvPath = Join-Path $root ".venv"
$activate = Join-Path $venvPath "Scripts/Activate.ps1"
$requirements = Join-Path $root "requirements.txt"

try {
    Write-Info "Root: $root"
    Log "start root=$root"

    # Desactivar entorno si hay uno activo
    if($env:VIRTUAL_ENV){
        Write-Info "Desactivando entorno activo: $env:VIRTUAL_ENV"
        Log "found active $env:VIRTUAL_ENV"
        if(Get-Command deactivate -ErrorAction SilentlyContinue){ deactivate }
    }

    # Eliminar .venv con confirmacion
    if(Test-Path $venvPath){
        if(Confirm-Action "Eliminar .venv existente en $venvPath?"){
            Remove-Item -LiteralPath $venvPath -Recurse -Force
            Write-Info ".venv eliminado"
            Log "removed $venvPath"
        } else {
            Write-Warn "Cancelado por usuario. No se toco .venv"
            Log "cancel remove"
            exit 0
        }
    }

    # Crear nuevo entorno
    Write-Info "Creando nuevo .venv"
    Log "python -m venv .venv"
    python -m venv $venvPath

    # Activar
    if(Test-Path $activate){
        Write-Info "Activando .venv"
        Log "activate $activate"
        . $activate
    } else {
        Write-Err "No se encontro $activate"
        Log "missing activate"
        exit 1
    }

    # Instalar requirements si existe
    if(Test-Path $requirements){
        try{
            Write-Info "Instalando dependencias de requirements.txt"
            Log "pip install -r requirements.txt"
            & python -m pip install -r $requirements
        } catch {
            Write-Err "Error instalando dependencias: $_"
            Log "error pip $_"
            exit 1
        }
    } else {
        Write-Warn "No existe requirements.txt, omitiendo instalacion"
        Log "no requirements"
    }

    # Validacion rapida
    try{
        $pyv = & python --version
        $pipv = & python -m pip --version
        Write-Info "Python: $pyv"
        Write-Info "Pip: $pipv"
        Log "python=$pyv"
        Log "pip=$pipv"
    } catch {
        Write-Err "Validacion python/pip fallo: $_"
        Log "error validate $_"
        exit 1
    }

    Write-Info "Entorno recreado"
    Log "done"
    exit 0
} catch {
    Write-Err "Fallo general: $_"
    Log "fatal $_"
    exit 1
}
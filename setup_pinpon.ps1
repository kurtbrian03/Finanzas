# setup_pinpon.ps1
# Orquestador para regenerar y validar el entorno PINPON. No se ejecuta nada sin confirmacion.

param(
    [switch]$yes,
    [string]$root = (Get-Location).Path
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Info($m){ Write-Host "[INFO] $m" -ForegroundColor Cyan }
function Write-Warn($m){ Write-Host "[WARN] $m" -ForegroundColor Yellow }
function Write-Err ($m){ Write-Host "[ERR ] $m" -ForegroundColor Red }

$logFile = Join-Path $root "setup_pinpon.log"
function Log($m){ $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"; "$ts $m" | Out-File -FilePath $logFile -Encoding utf8 -Append }
function Confirm-Action($msg){ if($yes){ return $true } $r = Read-Host "$msg (y/N)"; return $r -match '^(y|Y|s|S)$' }

$steps = @(
    @{ name="build_requirements"; script="build_requirements.ps1" },
    @{ name="rebuild_venv"; script="rebuild_venv.ps1" },
    @{ name="validate_python"; script="validate_python.ps1" },
    @{ name="validate_gmail_api"; script="validate_gmail_api.ps1" },
    @{ name="validate_credentials"; script="validate_credentials.ps1" }
)

Write-Info "Root: $root"
Log "start root=$root"

if(-not (Confirm-Action "Ejecutar setup completo?")){
    Write-Warn "Cancelado por el usuario"
    Log "cancel"
    return
}

$success = @()
$fail = @()

foreach($s in $steps){
    $path = Join-Path $root $s.script
    if(-not (Test-Path $path)){
        Write-Err "No se encontro $($s.script)"
        Log "missing $path"
        $fail += $s.name
        continue
    }
    try{
        Write-Info "Ejecutando $($s.script)"
        Log "run $path"
        & $path -root $root -yes:$yes
        $success += $s.name
    } catch {
        Write-Err "Fallo $($s.script): $_"
        Log "error $path $_"
        $fail += $s.name
    }
}

Write-Host "--- Resumen ---" -ForegroundColor Cyan
Write-Host "OK : $($success -join ', ')"
Write-Host "BAD: $($fail -join ', ')"
Log "success: $($success -join ',')"
Log "fail: $($fail -join ',')"

Write-Info "Fin de setup"
Log "done"
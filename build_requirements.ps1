# build_requirements.ps1
# Regenera requirements.txt usando pip freeze y crea respaldo si existe. No toca datos sensibles.

param(
    [string]$root = (Get-Location).Path
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Info($m){ Write-Host "[INFO] $m" -ForegroundColor Cyan }
function Write-Warn($m){ Write-Host "[WARN] $m" -ForegroundColor Yellow }
function Write-Err ($m){ Write-Host "[ERR ] $m" -ForegroundColor Red }

$logFile = Join-Path $root "build_requirements.log"
function Log($m){ $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"; "$ts $m" | Out-File -FilePath $logFile -Encoding utf8 -Append }

$req = Join-Path $root "requirements.txt"
$python = Join-Path $root ".venv/\Scripts/python.exe"
if(-not (Test-Path $python)){ $python = "python" }

Write-Info "Usando root: $root"
Log "start root=$root"

if(Test-Path $req){
    $backup = Join-Path $root ("requirements_backup_{0}.txt" -f (Get-Date -Format "yyyyMMdd_HHmmss"))
    Copy-Item -LiteralPath $req -Destination $backup -Force
    Write-Info "Respaldo creado: $backup"
    Log "backup $req -> $backup"
}

try{
    $cmd = "`"$python`" -m pip freeze"
    Write-Info "Generando requirements.txt"
    Log "run $cmd"
    & $python -m pip freeze | Out-File -FilePath $req -Encoding utf8
    Write-Info "requirements.txt actualizado"
    Log "wrote $req"
} catch {
    Write-Err "Error al generar requirements.txt: $_"
    Log "error $_"
    throw
}

Write-Info "Listo. Revisa $logFile"
Log "done"
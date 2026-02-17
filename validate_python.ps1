# validate_python.ps1
# Verifica python y pip disponibles en el entorno actual y ejecuta una prueba simple.

param(
    [string]$root = (Get-Location).Path
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Info($m){ Write-Host "[INFO] $m" -ForegroundColor Cyan }
function Write-Err ($m){ Write-Host "[ERR ] $m" -ForegroundColor Red }

$logFile = Join-Path $root "validate_python.log"
function Log($m){ $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"; "$ts $m" | Out-File -FilePath $logFile -Encoding utf8 -Append }

Log "start"

try{
    $pyv = & python --version
    Write-Info "Python: $pyv"
    Log "python $pyv"
} catch {
    Write-Err "python --version fallo: $_"
    Log "error python $_"
    throw
}

try{
    $pipv = & python -m pip --version
    Write-Info "Pip: $pipv"
    Log "pip $pipv"
} catch {
    Write-Err "pip --version fallo: $_"
    Log "error pip $_"
    throw
}

try{
    $test = @"
print("PINPON OK")
"@
    $out = & python -c $test
    Write-Info "Prueba: $out"
    Log "probe $out"
} catch {
    Write-Err "Prueba python fallo: $_"
    Log "error probe $_"
    exit 1
}

Write-Info "Validacion python completada"
Log "done"
exit 0
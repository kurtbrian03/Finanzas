param(
    [string]$Root = (Get-Location).Path
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "color_utils.ps1")

try {
    $venvPython = Join-Path $Root ".venv/Scripts/python.exe"
    if (-not (Test-Path $venvPython)) {
        Write-Err "No existe entorno virtual en .venv"
        exit 1
    }

    Write-Info "Entorno virtual detectado en .venv"
    exit 0
}
catch {
    Write-Err "Error en check_venv.ps1: $_"
    exit 1
}

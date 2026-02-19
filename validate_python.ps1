param(
    [string]$Root = (Get-Location).Path,
    [string]$MinVersion = "3.11"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "color_utils.ps1")

try {
    & (Join-Path $Root "check_python_version.ps1") -Root $Root -MinVersion $MinVersion
    if ($LASTEXITCODE -ne 0) { exit 1 }

    & (Join-Path $Root "check_pip.ps1") -Root $Root
    if ($LASTEXITCODE -ne 0) { exit 1 }

    Write-Info "Validación de Python completada"
    exit 0
}
catch {
    Write-Err "Error en validate_python.ps1: $_"
    exit 1
}

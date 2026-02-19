param(
    [string]$Root = (Get-Location).Path,
    [string]$MinVersion = "3.11"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "color_utils.ps1")

try {
    $ver = & python -c "import sys; print('.'.join(map(str, sys.version_info[:3])))"
    if (-not $ver) {
        Write-Err "No fue posible determinar versión de Python"
        exit 1
    }

    if ([Version]$ver -lt [Version]$MinVersion) {
        Write-Err "Python $ver no cumple mínimo $MinVersion"
        exit 1
    }

    Write-Info "Versión Python OK: $ver"
    exit 0
}
catch {
    Write-Err "Error en check_python_version.ps1: $_"
    exit 1
}

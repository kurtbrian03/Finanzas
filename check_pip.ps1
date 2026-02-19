param(
    [string]$Root = (Get-Location).Path
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "color_utils.ps1")

try {
    $pipVersion = & python -m pip --version
    if (-not $pipVersion) {
        Write-Err "pip no está disponible"
        exit 1
    }

    Write-Info "pip OK: $pipVersion"
    exit 0
}
catch {
    Write-Err "Error en check_pip.ps1: $_"
    exit 1
}

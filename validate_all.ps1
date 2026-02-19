param(
    [string]$Root = (Get-Location).Path
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "color_utils.ps1")

try {
    & (Join-Path $Root "scripts/run_all_validators.ps1") -Root $Root
    exit $LASTEXITCODE
}
catch {
    Write-Err "Error al ejecutar validate_all.ps1: $_"
    exit 1
}

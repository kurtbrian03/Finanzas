param(
    [string]$Path = "config/pinpon_credentials.json",
    [string]$Root = (Get-Location).Path
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "color_utils.ps1")

try {
    $full = Join-Path $Root $Path
    if (-not (Test-Path $full)) {
        Write-Err "No existe archivo: $Path"
        exit 1
    }

    $obj = Get-Content -LiteralPath $full -Raw | ConvertFrom-Json
    $keys = $obj | Get-Member -MemberType NoteProperty | Select-Object -ExpandProperty Name

    Write-Info "Claves en $Path"
    $keys | ForEach-Object { Write-Host " - $_" }
    exit 0
}
catch {
    Write-Err "Error al mostrar claves JSON: $_"
    exit 1
}

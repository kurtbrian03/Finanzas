param(
    [string]$Root = (Get-Location).Path
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "color_utils.ps1")

try {
    $file = Join-Path $Root "config/pinpon_credentials.json"
    if (-not (Test-Path $file)) {
        Write-Err "No existe config/pinpon_credentials.json"
        exit 1
    }

    $obj = Get-Content -LiteralPath $file -Raw | ConvertFrom-Json
    $required = @(
        "efirma_cer_path",
        "efirma_key_path",
        "efirma_password",
        "gmail_address",
        "gmail_app_password",
        "sat_password",
        "sat_rfc"
    )

    $keys = $obj | Get-Member -MemberType NoteProperty | Select-Object -ExpandProperty Name
    $missing = $required | Where-Object { $_ -notin $keys }

    if ($missing.Count -gt 0) {
        Write-Err "Faltan claves de credenciales: $($missing -join ', ')"
        exit 1
    }

    Write-Info "Credenciales validadas"
    exit 0
}
catch {
    Write-Err "Error en validate_credentials.ps1: $_"
    exit 1
}

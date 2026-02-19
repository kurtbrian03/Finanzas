param(
    [string]$Root = (Get-Location).Path
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "color_utils.ps1")

try {
    $gmailFile = Join-Path $Root "config/gmail_pinpon.json"
    if (-not (Test-Path $gmailFile)) {
        Write-Err "No existe config/gmail_pinpon.json"
        exit 1
    }

    $obj = Get-Content -LiteralPath $gmailFile -Raw | ConvertFrom-Json
    $required = @("gmail_address", "gmail_app_password")
    $keys = $obj | Get-Member -MemberType NoteProperty | Select-Object -ExpandProperty Name
    $missing = $required | Where-Object { $_ -notin $keys }

    if ($missing.Count -gt 0) {
        Write-Err "Faltan claves Gmail API: $($missing -join ', ')"
        exit 1
    }

    Write-Info "Validación Gmail API completada"
    exit 0
}
catch {
    Write-Err "Error en validate_gmail_api.ps1: $_"
    exit 1
}

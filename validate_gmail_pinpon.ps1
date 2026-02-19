param(
    [string]$Root = (Get-Location).Path
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "color_utils.ps1")
. (Join-Path $PSScriptRoot "log_utils.ps1")

$logFile = New-LogFilePath -Root $Root -Name "validate_gmail_pinpon.log"
Write-Log -FilePath $logFile -Message "Inicio validación Gmail PINPON"

try {
    $gmailFile = Join-Path $Root "config/gmail_pinpon.json"

    if (-not (Test-Path $gmailFile)) {
        Write-Err "No existe config/gmail_pinpon.json"
        Write-Log -FilePath $logFile -Message "Falta gmail_pinpon.json"
        exit 1
    }

    $obj = Get-Content -LiteralPath $gmailFile -Raw | ConvertFrom-Json
    $required = @("gmail_address", "gmail_app_password")

    $keys = $obj | Get-Member -MemberType NoteProperty | Select-Object -ExpandProperty Name
    $missing = $required | Where-Object { $_ -notin $keys }

    if ($missing.Count -gt 0) {
        Write-Err "Faltan claves en Gmail PINPON: $($missing -join ', ')"
        Write-Log -FilePath $logFile -Message "Claves faltantes: $($missing -join ', ')"
        exit 1
    }

    Write-Info "Validación de Gmail PINPON completada"
    Write-Log -FilePath $logFile -Message "Validación Gmail PINPON OK"
    exit 0
}
catch {
    Write-Err "Error en validación Gmail PINPON: $_"
    Write-Log -FilePath $logFile -Message "Error: $_"
    exit 1
}

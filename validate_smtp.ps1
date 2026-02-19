param(
    [string]$Root = (Get-Location).Path
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "color_utils.ps1")
. (Join-Path $PSScriptRoot "log_utils.ps1")

$logFile = New-LogFilePath -Root $Root -Name "validate_smtp.log"
Write-Log -FilePath $logFile -Message "Inicio validación SMTP"

try {
    $smtpFile = Join-Path $Root "config/pinpon_smtp.json"
    if (-not (Test-Path $smtpFile)) {
        Write-Err "No existe config/pinpon_smtp.json"
        Write-Log -FilePath $logFile -Message "Falta pinpon_smtp.json"
        exit 1
    }

    $obj = Get-Content -LiteralPath $smtpFile -Raw | ConvertFrom-Json
    $required = @("gmail_address", "gmail_app_password")

    $keys = $obj | Get-Member -MemberType NoteProperty | Select-Object -ExpandProperty Name
    $missing = $required | Where-Object { $_ -notin $keys }

    if ($missing.Count -gt 0) {
        Write-Err "Faltan claves SMTP: $($missing -join ', ')"
        Write-Log -FilePath $logFile -Message "Claves faltantes: $($missing -join ', ')"
        exit 1
    }

    Write-Info "Validación SMTP completada"
    Write-Log -FilePath $logFile -Message "Validación SMTP OK"
    exit 0
}
catch {
    Write-Err "Error en validación SMTP: $_"
    Write-Log -FilePath $logFile -Message "Error: $_"
    exit 1
}

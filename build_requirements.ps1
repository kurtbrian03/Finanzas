param(
    [string]$Root = (Get-Location).Path,
    [switch]$NoBackup
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "color_utils.ps1")

try {
    $reqPath = Join-Path $Root "requirements.txt"

    if ((Test-Path $reqPath) -and (-not $NoBackup)) {
        $backupPath = Join-Path $Root ("requirements_backup_{0}.txt" -f (Get-Date -Format "yyyyMMdd_HHmmss"))
        Copy-Item -LiteralPath $reqPath -Destination $backupPath -Force
        Write-Info "Backup creado: $backupPath"
    }

    & python -m pip freeze | Out-File -FilePath $reqPath -Encoding UTF8

    Write-Info "requirements.txt actualizado"
    exit 0
}
catch {
    Write-Err "Error en build_requirements.ps1: $_"
    exit 1
}

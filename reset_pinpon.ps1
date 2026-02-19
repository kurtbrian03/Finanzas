param(
    [ValidateSet("dry-run", "clean")][string]$Mode = "dry-run",
    [string]$Root = (Get-Location).Path,
    [switch]$Yes
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "color_utils.ps1")

try {
    $targets = @(
        ".pytest_cache",
        "dist",
        "tmp",
        "logs",
        "reports",
        "salidas"
    )

    if ($Mode -eq "dry-run") {
        Write-Info "Modo dry-run. Se listarían estos objetivos:"
        $targets | ForEach-Object { Write-Host " - $_" }
        exit 0
    }

    if (-not $Yes) {
        $answer = Read-Host "¿Confirmas limpieza de carpetas temporales? (y/N)"
        if ($answer -notmatch '^(y|Y|s|S)$') {
            Write-Warn "Limpieza cancelada"
            exit 0
        }
    }

    foreach ($target in $targets) {
        $full = Join-Path $Root $target
        if (Test-Path $full) {
            Remove-Item -LiteralPath $full -Recurse -Force
        }
    }

    Write-Info "Reset PINPON completado"
    exit 0
}
catch {
    Write-Err "Error en reset_pinpon.ps1: $_"
    exit 1
}

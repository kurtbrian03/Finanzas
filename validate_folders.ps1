param(
    [string]$Root = (Get-Location).Path
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "color_utils.ps1")

try {
    $requiredDirs = @(
        "analysis",
        "config",
        "core",
        "docs",
        "downloads",
        "history",
        "pinpon_modules",
        "scripts",
        "tests",
        "ui",
        "utils",
        "validation"
    )

    $missing = @()
    foreach ($dir in $requiredDirs) {
        $full = Join-Path $Root $dir
        if (-not (Test-Path $full)) {
            $missing += $dir
        }
    }

    if ($missing.Count -gt 0) {
        Write-Err "Faltan carpetas requeridas: $($missing -join ', ')"
        exit 1
    }

    Write-Info "Estructura de carpetas validada"
    exit 0
}
catch {
    Write-Err "Error en validate_folders.ps1: $_"
    exit 1
}

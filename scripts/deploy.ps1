param(
    [string]$Root = (Get-Location).Path,
    [switch]$SkipValidation,
    [switch]$Rollback
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

. (Join-Path $Root "color_utils.ps1")

try {
    if ($Rollback) {
        Write-Warn "Rollback básico ejecutado (placeholder)"
        Write-Warn "Aquí se restauraría el último artefacto estable"
        exit 0
    }

    if (-not $SkipValidation) {
        & (Join-Path $Root "scripts/run_all_validators.ps1") -Root $Root
        if ($LASTEXITCODE -ne 0) {
            Write-Err "No se puede desplegar: validadores fallaron"
            exit 1
        }

        & (Join-Path $Root "scripts/run_tests.ps1") -Root $Root
        if ($LASTEXITCODE -ne 0) {
            Write-Err "No se puede desplegar: pruebas fallaron"
            exit 1
        }
    }

    Write-Info "Deploy placeholder ejecutado"
    Write-Info "Hook futuro: despliegue en servidor/contenedor/API"
    exit 0
}
catch {
    Write-Err "Error en deploy.ps1: $_"
    exit 1
}

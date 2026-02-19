param(
    [string]$Root = (Get-Location).Path,
    [switch]$Yes
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "color_utils.ps1")

$steps = @(
    @{ Name = "init_project_structure"; Script = "init_project_structure.ps1"; Args = @() },
    @{ Name = "check_python_version"; Script = "check_python_version.ps1"; Args = @() },
    @{ Name = "check_pip"; Script = "check_pip.ps1"; Args = @() },
    @{ Name = "rebuild_venv"; Script = "rebuild_venv.ps1"; Args = @("-Yes:$Yes") },
    @{ Name = "validate_python"; Script = "validate_python.ps1"; Args = @() },
    @{ Name = "validate_folders"; Script = "validate_folders.ps1"; Args = @() },
    @{ Name = "validate_config"; Script = "validate_config.ps1"; Args = @() },
    @{ Name = "validate_all"; Script = "validate_all.ps1"; Args = @() }
)

try {
    foreach ($step in $steps) {
        $scriptPath = Join-Path $Root $step.Script
        if (-not (Test-Path $scriptPath)) {
            Write-Err "No existe script requerido: $($step.Script)"
            exit 1
        }

        Write-Info "Ejecutando: $($step.Name)"
        & $scriptPath -Root $Root

        if ($LASTEXITCODE -ne 0) {
            Write-Err "Falló paso: $($step.Name)"
            exit 1
        }
    }

    Write-Info "Setup PINPON completado"
    exit 0
}
catch {
    Write-Err "Error en setup_pinpon.ps1: $_"
    exit 1
}

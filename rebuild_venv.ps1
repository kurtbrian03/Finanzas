param(
    [string]$Root = (Get-Location).Path,
    [switch]$Yes
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "color_utils.ps1")

try {
    $venvPath = Join-Path $Root ".venv"
    $requirements = Join-Path $Root "requirements.txt"

    if (Test-Path $venvPath) {
        if (-not $Yes) {
            $answer = Read-Host "Eliminar .venv existente y reconstruir? (y/N)"
            if ($answer -notmatch '^(y|Y|s|S)$') {
                Write-Warn "Reconstrucción cancelada"
                exit 0
            }
        }

        Remove-Item -LiteralPath $venvPath -Recurse -Force
    }

    & python -m venv $venvPath

    $venvPython = Join-Path $venvPath "Scripts/python.exe"
    & $venvPython -m pip install --upgrade pip

    if (Test-Path $requirements) {
        & $venvPython -m pip install -r $requirements
    }

    Write-Info "Entorno virtual reconstruido"
    exit 0
}
catch {
    Write-Err "Error en rebuild_venv.ps1: $_"
    exit 1
}

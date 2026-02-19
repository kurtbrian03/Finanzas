param(
    [string]$Root = (Get-Location).Path,
    [string]$PackageDir = "pinpon_modulo_compras"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Info($Message) { Write-Host "[INFO] $Message" -ForegroundColor Cyan }
function Write-Warn($Message) { Write-Host "[WARN] $Message" -ForegroundColor Yellow }
function Write-Err($Message) { Write-Host "[ERR ] $Message" -ForegroundColor Red }

try {
    $targetDir = Join-Path $Root $PackageDir
    $pyproject = Join-Path $targetDir "pyproject.toml"

    if (-not (Test-Path $pyproject)) {
        Write-Err "No existe pyproject.toml en $targetDir"
        exit 1
    }

    $pypiToken = $env:PYPI_TOKEN
    if (-not $pypiToken) {
        Write-Err "PYPI_TOKEN no está definido en el entorno."
        exit 1
    }

    Set-Location $targetDir

    & python -m pip install --upgrade build twine
    if ($LASTEXITCODE -ne 0) {
        Write-Err "No fue posible instalar build/twine"
        exit 1
    }

    & python -m build
    if ($LASTEXITCODE -ne 0) {
        Write-Err "Falló la construcción del paquete"
        exit 1
    }

    $twineOutput = & python -m twine upload dist/* -u __token__ -p $pypiToken 2>&1
    if ($LASTEXITCODE -ne 0) {
        $twineText = ($twineOutput | Out-String)
        if ($twineText -match "File already exists" -or $twineText -match "already been taken") {
            Write-Warn "La versión del paquete ya existe en PyPI. Se considera estado idempotente."
            Write-Info "URL estimada: https://pypi.org/project/pinpon-modulo-compras/"
            exit 0
        }

        Write-Err "Error al publicar en PyPI. Posible credencial inválida o error de red."
        Write-Err $twineText
        exit 1
    }

    Write-Info "Paquete publicado correctamente en PyPI."
    Write-Info "URL estimada: https://pypi.org/project/pinpon-modulo-compras/"
    exit 0
}
catch {
    Write-Err "Error en publish_pip_compras.ps1: $($_.Exception.Message)"
    exit 1
}

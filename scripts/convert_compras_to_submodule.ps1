param(
    [string]$Root = (Get-Location).Path,
    [string]$GithubUser = "kurtbrian03",
    [string]$RepoName = "pinpon-modulo-compras"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Info($Message) { Write-Host "[INFO] $Message" -ForegroundColor Cyan }
function Write-Warn($Message) { Write-Host "[WARN] $Message" -ForegroundColor Yellow }
function Write-Err($Message) { Write-Host "[ERR ] $Message" -ForegroundColor Red }

try {
    Set-Location $Root

    $repoUrl = "https://github.com/$GithubUser/$RepoName.git"
    $submodulePath = Join-Path $Root "pinpon_modules/compras"
    $gitmodulesPath = Join-Path $Root ".gitmodules"

    if (Test-Path $gitmodulesPath) {
        $gitmodulesContent = Get-Content -LiteralPath $gitmodulesPath -Raw
        if ($gitmodulesContent -match '\[submodule "pinpon_modules/compras"\]') {
            Write-Info "pinpon_modules/compras ya está registrado como submódulo."
            git submodule update --init --recursive pinpon_modules/compras
            exit 0
        }
    }

    $remoteCheck = git ls-remote $repoUrl 2>$null
    if ($LASTEXITCODE -ne 0 -or -not $remoteCheck) {
        Write-Warn "El repositorio remoto aún no existe. Ejecute create_remote_repo.ps1 primero."
        exit 0
    }

    if (-not (Test-Path $submodulePath)) {
        Write-Err "No existe pinpon_modules/compras"
        exit 1
    }

    $tempPath = Join-Path $Root ".tmp_compras_submodule"
    if (Test-Path $tempPath) {
        Remove-Item -LiteralPath $tempPath -Recurse -Force
    }
    New-Item -ItemType Directory -Path $tempPath -Force | Out-Null

    Write-Info "Respaldando contenido actual de Compras en temporal"
    Copy-Item -Path (Join-Path $submodulePath "*") -Destination $tempPath -Recurse -Force

    if (Test-Path $submodulePath) {
        Remove-Item -LiteralPath $submodulePath -Recurse -Force
    }

    git submodule add $repoUrl pinpon_modules/compras
    if ($LASTEXITCODE -ne 0) {
        Write-Err "No se pudo agregar el submódulo."
        exit 1
    }

    Copy-Item -Path (Join-Path $tempPath "*") -Destination $submodulePath -Recurse -Force
    Remove-Item -LiteralPath $tempPath -Recurse -Force

    git -C $submodulePath add .
    git -C $submodulePath commit -m "Initial commit: Pinpon ERP module - Compras" --allow-empty

    git add .gitmodules pinpon_modules/compras
    git commit -m "Convert Compras module into Git submodule" --allow-empty

    git submodule update --init --recursive

    Write-Info "Submódulo agregado en pinpon_modules/compras"
    exit 0
}
catch {
    Write-Err "Error en convert_compras_to_submodule.ps1: $_"
    exit 1
}

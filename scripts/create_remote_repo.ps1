param(
    [string]$RepoName = "pinpon-modulo-compras",
    [string]$Description = "Módulo ERP de Compras para Pinpon",
    [bool]$Private = $false
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Info($Message) { Write-Host "[INFO] $Message" -ForegroundColor Cyan }
function Write-Warn($Message) { Write-Host "[WARN] $Message" -ForegroundColor Yellow }
function Write-Err($Message) { Write-Host "[ERR ] $Message" -ForegroundColor Red }

try {
    $token = $env:GITHUB_TOKEN
    if (-not $token) {
        Write-Err "GITHUB_TOKEN no está definido en el entorno."
        exit 1
    }

    $headers = @{
        Authorization = "Bearer $token"
        Accept = "application/vnd.github+json"
        "X-GitHub-Api-Version" = "2022-11-28"
    }

    $userResp = Invoke-RestMethod -Method Get -Uri "https://api.github.com/user" -Headers $headers
    $owner = $userResp.login

    $existingCheckUri = "https://api.github.com/repos/$owner/$RepoName"

    try {
        $existing = Invoke-RestMethod -Method Get -Uri $existingCheckUri -Headers $headers
        if ($existing -and $existing.html_url) {
            Write-Warn "El repositorio ya existe."
            Write-Info "URL: $($existing.html_url)"
            exit 0
        }
    }
    catch {
        # Si no existe, continuar con creación
    }

    $body = @{
        name = $RepoName
        description = $Description
        private = $Private
    } | ConvertTo-Json

    $createResp = Invoke-RestMethod -Method Post -Uri "https://api.github.com/user/repos" -Headers $headers -Body $body

    if ($createResp -and $createResp.html_url) {
        Write-Info "Repositorio creado correctamente."
        Write-Info "URL: $($createResp.html_url)"
        exit 0
    }

    Write-Err "No se pudo confirmar la creación del repositorio."
    exit 1
}
catch {
    $msg = $_.Exception.Message
    if ($msg -match "name already exists" -or $msg -match "422") {
        Write-Warn "El repositorio ya existe o el nombre está en uso."
        exit 0
    }

    Write-Err "Error en create_remote_repo.ps1: $msg"
    exit 1
}

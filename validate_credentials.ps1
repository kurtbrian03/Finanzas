# validate_credentials.ps1
# Verifica existencia y campos esperados en archivos de credenciales sin mostrar valores sensibles.

param(
    [string]$root = (Get-Location).Path
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Info($m){ Write-Host "[INFO] $m" -ForegroundColor Cyan }
function Write-Warn($m){ Write-Host "[WARN] $m" -ForegroundColor Yellow }
function Write-Err ($m){ Write-Host "[ERR ] $m" -ForegroundColor Red }

$logFile = Join-Path $root "validate_credentials.log"
function Log($m){ $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"; "$ts $m" | Out-File -FilePath $logFile -Encoding utf8 -Append }

$files = @(
    "config/gmail_pinpon.json",
    "config/pinpon_credentials.json",
    "config/pinpon_smtp.json"
)
$required = @("client_id","client_secret","refresh_token","email")

function Validate-File($path){
    $full = Join-Path $root $path
    if(-not (Test-Path $full)){
        Write-Err "Falta archivo: ${path}"
        Log "missing ${path}"
        return $false
    }
    $raw = Get-Content -LiteralPath $full -Raw
    if(-not $raw){ Write-Warn "Archivo vacio: ${path}"; Log "empty ${path}" }
    try{ $obj = $raw | ConvertFrom-Json }
    catch{ Write-Err "JSON invalido: ${path}"; Log "invalid ${path}"; return $false }
    $keys = ($obj | Get-Member -MemberType NoteProperty | Select-Object -ExpandProperty Name)
    $missing = $required | Where-Object { $_ -notin $keys }
    if($missing){
        Write-Warn "Faltan campos en ${path}: $($missing -join ', ')"
        Log "missing keys ${path}: $($missing -join ',')"
        return $false
    }
    Write-Info "Campos requeridos presentes en ${path}"
    Log "ok ${path}"
    return $true
}

Log "start"
$okAll = $true
foreach($f in $files){ if(-not (Validate-File $f)){ $okAll = $false } }

if($okAll){ Write-Info "Credenciales validadas"; Log "done ok"; exit 0 }
else { Write-Warn "Validacion con advertencias"; Log "done warn"; exit 1 }
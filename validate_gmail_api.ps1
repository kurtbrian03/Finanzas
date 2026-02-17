# validate_gmail_api.ps1
# Verifica archivos de configuracion Gmail y estructura minima sin mostrar valores sensibles.

param(
    [string]$root = (Get-Location).Path
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Info($m){ Write-Host "[INFO] $m" -ForegroundColor Cyan }
function Write-Warn($m){ Write-Host "[WARN] $m" -ForegroundColor Yellow }
function Write-Err ($m){ Write-Host "[ERR ] $m" -ForegroundColor Red }

$logFile = Join-Path $root "validate_gmail_api.log"
function Log($m){ $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"; "$ts $m" | Out-File -FilePath $logFile -Encoding utf8 -Append }

$files = @(
    "config/gmail_pinpon.json",
    "config/pinpon_credentials.json",
    "config/pinpon_smtp.json"
)

function Check-Json($path){
    $full = Join-Path $root $path
    if(-not (Test-Path $full)){
        Write-Err "Falta archivo: ${path}"
        Log "missing ${path}"
        return $false
    }
    $content = Get-Content -LiteralPath $full -Raw
    if(-not $content){ Write-Warn "Archivo vacio: ${path}"; Log "empty ${path}" }
    try{
        $obj = $content | ConvertFrom-Json
    } catch {
        Write-Err "JSON invalido: ${path}"
        Log "invalid ${path}"
        return $false
    }
    $keys = ($obj | Get-Member -MemberType NoteProperty | Select-Object -ExpandProperty Name)
    if(-not $keys){ Write-Warn "Sin claves en ${path}"; Log "nokeys ${path}" }
    $required = @("client_id","client_secret","refresh_token","email")
    $missing = $required | Where-Object { $_ -notin $keys }
    if($missing){
        Write-Warn "Faltan claves en ${path}: $($missing -join ', ')"
        Log "missing keys ${path}: $($missing -join ',')"
    } else {
        Write-Info "Claves minimas presentes en ${path}"
        Log "keys ok ${path}"
    }
    return $true
}

Log "start"
$allOk = $true
foreach($f in $files){
    $ok = Check-Json $f
    if(-not $ok){ $allOk = $false }
}

if($allOk){ Write-Info "Validacion Gmail API completada"; Log "done ok"; exit 0 }
else { Write-Warn "Validacion con advertencias"; Log "done warn"; exit 1 }
# show_json_keys.ps1
# Muestra solo los nombres de las claves (propiedades) de un archivo JSON dado.
# Uso: .\show_json_keys.ps1 -Path ruta/al/archivo.json

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [string]$Path
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Info($m){ Write-Host $m -ForegroundColor Cyan }
function Write-Err ($m){ Write-Host $m -ForegroundColor Red }

try {
    if(-not (Test-Path -LiteralPath $Path)){
        Write-Err ("[ERR ] No se encontró el archivo: {0}" -f $Path)
        exit 1
    }

    $content = Get-Content -LiteralPath $Path -Raw
    if(-not $content){
        Write-Err ("[ERR ] El archivo está vacío: {0}" -f $Path)
        exit 1
    }

    try {
        $json = $content | ConvertFrom-Json
    } catch {
        Write-Err ("[ERR ] JSON inválido: {0}" -f $_)
        exit 1
    }

    Write-Info ("[INFO] Claves encontradas en {0}" -f $Path)
    $keys = ($json | Get-Member -MemberType NoteProperty).Name
    $keys | ForEach-Object { Write-Host $_ }
    exit 0
} catch {
    Write-Err ("[ERR ] Error inesperado: {0}" -f $_)
    exit 1
}
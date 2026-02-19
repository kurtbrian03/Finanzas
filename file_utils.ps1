Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Ensure-Directory {
    param([Parameter(Mandatory = $true)][string]$Path)

    if (-not (Test-Path $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

function Ensure-JsonFile {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][hashtable]$Template
    )

    if (-not (Test-Path $Path)) {
        $Template | ConvertTo-Json -Depth 10 | Set-Content -Path $Path -Encoding UTF8
    }
}

function Read-JsonFile {
    param([Parameter(Mandatory = $true)][string]$Path)

    if (-not (Test-Path $Path)) {
        throw "No existe archivo JSON: $Path"
    }

    $raw = Get-Content -LiteralPath $Path -Raw
    if (-not $raw) {
        throw "Archivo JSON vacío: $Path"
    }

    return ($raw | ConvertFrom-Json)
}

param(
    [switch]$ShowCommandsOnly = $true
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Info([string]$m) { Write-Host "[INFO] $m" -ForegroundColor Cyan }
function Write-Warn([string]$m) { Write-Host "[WARN] $m" -ForegroundColor Yellow }
function Write-Ok([string]$m)   { Write-Host "[ OK ] $m" -ForegroundColor Green }

Write-Host "=== ORQUESTADOR: PREREQUISITOS (MODO SEGURO / DRY-RUN) ===" -ForegroundColor Magenta
Write-Host "Este script NO instala nada. Solo detecta y muestra comandos oficiales." -ForegroundColor DarkYellow

$checks = @(
    @{ Name = "Python"; Cmd = "python"; Url = "https://www.python.org/downloads/windows/"; Winget = "winget install -e --id Python.Python.3.11"; Admin = "Recomendado" },
    @{ Name = "Node.js LTS"; Cmd = "node"; Url = "https://nodejs.org/en/download"; Winget = "winget install -e --id OpenJS.NodeJS.LTS"; Admin = "Recomendado" },
    @{ Name = "Git"; Cmd = "git"; Url = "https://git-scm.com/download/win"; Winget = "winget install -e --id Git.Git"; Admin = "No" },
    @{ Name = "Poppler (pdf2image)"; Cmd = "pdfinfo"; Url = "https://github.com/oschwartz10612/poppler-windows/releases"; Winget = "winget install -e --id oschwartz10612.poppler"; Admin = "Sí" }
)

foreach ($item in $checks) {
    $exists = Get-Command $item.Cmd -ErrorAction SilentlyContinue
    if ($exists) {
        Write-Ok "$($item.Name) detectado en PATH"
    } else {
        Write-Warn "$($item.Name) NO detectado"
        Write-Host "  Descarga oficial : $($item.Url)"
        Write-Host "  Comando winget   : $($item.Winget)"
        Write-Host "  ¿Administrador?  : $($item.Admin)"
    }
}

Write-Host "`n=== COMANDOS SUGERIDOS (NO EJECUTADOS) ===" -ForegroundColor Cyan
foreach ($item in $checks) {
    Write-Host "- $($item.Winget)"
}

if ($ShowCommandsOnly) {
    Write-Info "Finalizado en modo seguro. Ninguna instalación fue ejecutada."
}

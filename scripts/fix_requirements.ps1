param(
    [string]$RequirementsPath = "requirements.txt",
    [string]$OutputPath = "requirements.generated.txt"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Info([string]$m) { Write-Host "[INFO] $m" -ForegroundColor Cyan }
function Write-Warn([string]$m) { Write-Host "[WARN] $m" -ForegroundColor Yellow }
function Write-Err([string]$m)  { Write-Host "[ERR ] $m" -ForegroundColor Red }
function Write-Ok([string]$m)   { Write-Host "[ OK ] $m" -ForegroundColor Green }

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\")).Path
$reqFile = Join-Path $repoRoot $RequirementsPath
$outFile = Join-Path $repoRoot $OutputPath

Write-Host "=== ORQUESTADOR: FIX REQUIREMENTS (SIN INSTALAR) ===" -ForegroundColor Magenta
Write-Host "Este script valida y genera archivo limpio; NO instala paquetes." -ForegroundColor DarkYellow

if (-not (Test-Path $reqFile)) {
    Write-Err "No existe $RequirementsPath"
    exit 1
}

$raw = Get-Content -LiteralPath $reqFile -Encoding UTF8

$hasConflict = $false
if ($raw -match '^<<<<<<<\s|^=======\s*$|^>>>>>>>\s') {
    $hasConflict = $true
    Write-Err "Se detectaron conflictos Git en requirements.txt"
}

$seen = @{}
$clean = New-Object System.Collections.Generic.List[string]
$invalidLines = New-Object System.Collections.Generic.List[string]
$dupLines = New-Object System.Collections.Generic.List[string]

foreach ($line in $raw) {
    $trimmed = $line.Trim()
    if ([string]::IsNullOrWhiteSpace($trimmed)) { continue }
    if ($trimmed.StartsWith("#")) { continue }

    if ($trimmed -match '^(--index-url|--extra-index-url|git\+|https?://)') {
        $invalidLines.Add($trimmed)
        continue
    }

    if ($trimmed -notmatch '^[A-Za-z0-9_.-]+\s*(==|>=|<=|>|<|~=).+$' -and $trimmed -notmatch '^[A-Za-z0-9_.-]+$') {
        $invalidLines.Add($trimmed)
        continue
    }

    $pkgName = ($trimmed -split '(==|>=|<=|>|<|~=)', 2)[0].Trim().ToLowerInvariant()
    if ($seen.ContainsKey($pkgName)) {
        $dupLines.Add($trimmed)
        continue
    }

    $seen[$pkgName] = $true
    $clean.Add($trimmed)
}

foreach ($bad in $invalidLines) { Write-Warn "Línea inválida o no permitida: $bad" }
foreach ($dup in $dupLines) { Write-Warn "Duplicado removido: $dup" }

Write-Host "`n=== VALIDACIÓN DE VERSIONES PyPI (solo pines ==) ===" -ForegroundColor Cyan
foreach ($dep in $clean) {
    if ($dep -match '^(?<name>[A-Za-z0-9_.-]+)==(?<ver>.+)$') {
        $name = $matches['name']
        $ver = $matches['ver']
        try {
            $url = "https://pypi.org/pypi/$name/json"
            $meta = Invoke-RestMethod -Uri $url -Method Get -ErrorAction Stop
            if ($meta.releases.PSObject.Properties.Name -contains $ver) {
                Write-Ok "$name==$ver existe en PyPI"
            } else {
                Write-Warn "$name==$ver NO encontrado en PyPI"
            }
        } catch {
            Write-Warn "No se pudo validar $name contra PyPI (red/permisos)."
        }
    }
}

$header = @(
    "# requirements limpio generado automáticamente",
    "# origen: $RequirementsPath",
    ""
)

($header + $clean) | Set-Content -LiteralPath $outFile -Encoding UTF8
Write-Info "Archivo generado: $OutputPath"

if ($hasConflict) {
    Write-Warn "Debes resolver conflictos Git antes de usar este requirements."
}

Write-Info "fix_requirements finalizado."

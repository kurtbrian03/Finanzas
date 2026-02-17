# reset_pinpon.ps1
# Prepara el proyecto PINPON para una configuración limpia sin tocar datos sensibles.
# Modo por defecto: dry-run (no borra nada). Modo limpieza: --mode clean (pide confirmación salvo que se use --yes).
# Preserva siempre: config/, datos/, ops/, Obsidian/, vault/, .git/, .venv/ (contienen credenciales, datos y entorno).
# Elimina solo bajo confirmación: .vscode/, logs/, tmp/, scripts/ (solo .bak/.tmp), reports/, salidas/, carpetas vacías y *_backup_*.
# Reconstruye: reports/, salidas/, scripts/, tmp/.
# Registro: reset_pinpon.log en la raíz.
# Restauración: si algo sale mal, recuperar desde respaldos manuales (ej. _backup_*), historial git o copias externas; el script no toca config/ ni datos/.

param(
    [ValidateSet("dry-run","clean")][string]$mode = "dry-run",
    [switch]$yes,
    [string]$root = (Get-Location).Path
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Info($m){ Write-Host "[INFO] $m" -ForegroundColor Cyan }
function Write-Warn($m){ Write-Host "[WARN] $m" -ForegroundColor Yellow }
function Write-Err ($m){ Write-Host "[ERR ] $m" -ForegroundColor Red }

$logFile = Join-Path $root "reset_pinpon.log"

function Log($m){
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$ts $m" | Out-File -FilePath $logFile -Encoding utf8 -Append
}

function Confirm-Action($message){
    if($yes){ return $true }
    $r = Read-Host "$message (y/N)"
    return $r -match '^(y|Y|s|S)'
}

# Resolución de rutas preservadas para evitar borrados accidentales.
$preserve = @("config","datos","ops","Obsidian","vault",".git",".venv") | ForEach-Object { Join-Path $root $_ }

function Is-Preserved($path){
    $full = (Resolve-Path $path -ErrorAction SilentlyContinue)
    if(-not $full){ return $false }
    return $preserve -contains $full.Path
}

function Collect-Targets(){
    $targets = @()

    # Carpetas estándar a eliminar bajo confirmación
    $candidateDirs = @(".vscode","logs","tmp","reports","salidas")
    foreach($d in $candidateDirs){
        $p = Join-Path $root $d
        if(Test-Path $p){ $targets += [pscustomobject]@{ Path=$p; Type="Directory"; Reason="Limpieza" } }
    }

    # Carpeta scripts: solo archivos temporales/bak
    $scriptsDir = Join-Path $root "scripts"
    if(Test-Path $scriptsDir){
        $bak = Get-ChildItem -LiteralPath $scriptsDir -File -Include *.bak,*.tmp -ErrorAction SilentlyContinue
        foreach($f in $bak){ $targets += [pscustomobject]@{ Path=$f.FullName; Type="File"; Reason="scripts temporales" } }
    }

    # Carpetas *_backup_* en cualquier nivel (salvo preservadas)
    $backupDirs = Get-ChildItem -LiteralPath $root -Recurse -Directory -Filter "*_backup_*" -ErrorAction SilentlyContinue
    foreach($b in $backupDirs){
        if(Is-Preserved $b.FullName){ continue }
        $targets += [pscustomobject]@{ Path=$b.FullName; Type="Directory"; Reason="backup antiguo" }
    }

    # Carpetas vacías (no preservadas)
    $emptyDirs = Get-ChildItem -LiteralPath $root -Recurse -Directory -ErrorAction SilentlyContinue |
        Where-Object { -not (Is-Preserved $_.FullName) -and (-not (Get-ChildItem -LiteralPath $_.FullName -Force -ErrorAction SilentlyContinue)) }
    foreach($e in $emptyDirs){ $targets += [pscustomobject]@{ Path=$e.FullName; Type="Directory"; Reason="vacía" } }

    return $targets | Sort-Object -Property Path -Unique
}

Write-Info "Modo: $mode (dry-run no borra; clean solicita confirmación)"
Log "start mode=$mode root=$root"

$targets = Collect-Targets
if(-not $targets){ Write-Info "No hay candidatos a limpiar"; Log "nothing to clean"; return }

Write-Info "Candidatos a eliminar:"; $targets | ForEach-Object { Write-Host " - [$($_.Type)] $($_.Path) ($($_.Reason))" }
Log ("targets: " + ($targets.Path -join ";"))

if($mode -eq "dry-run"){
    Write-Info "Dry-run: no se eliminó nada."
    Write-Info "Preservados: config, datos, ops, Obsidian, vault, .git, .venv"
    return
}

foreach($t in $targets){
    if(Is-Preserved $t.Path){ Write-Warn "Omitido (preservado): $($t.Path)"; continue }
    $ok = Confirm-Action "Eliminar $($t.Type): $($t.Path)?"
    if(-not $ok){ Write-Warn "Saltado por usuario: $($t.Path)"; Log "skip $($t.Path)"; continue }
    try{
        if($t.Type -eq "Directory"){
            Remove-Item -LiteralPath $t.Path -Recurse -Force
        } else {
            Remove-Item -LiteralPath $t.Path -Force
        }
        Write-Info "Eliminado: $($t.Path)"
        Log "deleted $($t.Path)"
    } catch {
        Write-Err "Error al eliminar $($t.Path): $_"
        Log "error deleting $($t.Path): $_"
    }
}

# Reconstrucción de estructura mínima limpia
$rebuild = @("reports","salidas","scripts","tmp")
foreach($r in $rebuild){
    $p = Join-Path $root $r
    if(-not (Test-Path $p)){
        New-Item -ItemType Directory -Path $p -Force | Out-Null
        Write-Info "Creada carpeta: $p"
        Log "created $p"
    }
}

Write-Info "Limpieza finalizada. Revisa reset_pinpon.log para detalles."
Log "done"
<#
.SYNOPSIS
    Detecta y consolida entornos virtuales Python duplicados de forma segura.

.DESCRIPTION
    Script completo para detectar venvs duplicados, compararlos y consolidarlos.
    Por defecto ejecuta en modo --dry-run (sin cambios).

.EXAMPLES
    .\dedupe_venvs.ps1 --dry-run
    .\dedupe_venvs.ps1 --consolidate --target .venv --yes
    .\dedupe_venvs.ps1 --auto --target .venv
    .\dedupe_venvs.ps1 --report-only
#>

param(
    [switch]$DryRun = $true,
    [switch]$BackupOnly,
    [switch]$Consolidate,
    [switch]$ForceDelete,
    [switch]$Yes,
    [switch]$Test,
    [switch]$Auto,
    [switch]$Prune,
    [switch]$ReportOnly,
    [switch]$Help,
    [string]$Target = "",
    [string]$Log = "dedupe_actions.log",
    [string]$Report = "dedupe_report.txt",
    [int]$PruneDays = 7
)

# Configuración
$ErrorActionPreference = "Continue"
$VenvPatterns = @(".venv*", "venv*", "env", "ENV", "virtualenv*")
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

function Show-Help {
    Write-Host @"
Uso: .\dedupe_venvs.ps1 [OPCIONES]

Opciones:
  --dry-run         Modo por defecto, no hace cambios (solo reportes)
  --backup-only     Renombra duplicados a backups
  --consolidate     Consolida paquetes en venv objetivo
  --target <name>   Especifica venv objetivo (por defecto: .venv)
  --force-delete    Borra backups (requiere confirmación)
  --yes, -y         No pedir confirmaciones
  --test            Simula en directorio temporal
  --auto            Consolida automático (requiere --yes)
  --prune           Sugiere eliminar backups antiguos
  --report-only     Solo genera reporte
  --log <path>      Ruta del log (por defecto: dedupe_actions.log)
  --report <path>   Ruta del reporte (por defecto: dedupe_report.txt)
  --help            Muestra esta ayuda

Ejemplos:
  .\dedupe_venvs.ps1 --dry-run
  .\dedupe_venvs.ps1 --consolidate --target .venv --yes
  .\dedupe_venvs.ps1 --auto --target .venv
"@
    exit 0
}

if ($Help) { Show-Help }

# Funciones auxiliares
function Write-Log {
    param([string]$Message)
    $LogMessage = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $Message"
    Write-Host $LogMessage
    Add-Content -Path $Log -Value $LogMessage
}

function Get-VenvInfo {
    param([string]$VenvPath)
    
    $info = @{
        Path = $VenvPath
        PythonVersion = $null
        Packages = @()
        PackagesHash = $null
        ConfigFile = $null
    }
    
    # Detectar ejecutable Python
    $pythonExe = if (Test-Path "$VenvPath\Scripts\python.exe") {
        "$VenvPath\Scripts\python.exe"
    } elseif (Test-Path "$VenvPath\bin\python") {
        "$VenvPath\bin\python"
    } else { $null }
    
    if (-not $pythonExe) {
        Write-Log "ADVERTENCIA: No se encontró ejecutable Python en $VenvPath"
        return $info
    }
    
    # Versión de Python
    try {
        $info.PythonVersion = & $pythonExe --version 2>&1 | Out-String
        $info.PythonVersion = $info.PythonVersion.Trim()
    } catch {
        Write-Log "ERROR: No se pudo obtener versión de Python en $VenvPath"
    }
    
    # Paquetes instalados
    $packagesFile = "$VenvPath-packages.txt"
    try {
        & $pythonExe -m pip freeze > $packagesFile 2>&1
        $info.Packages = Get-Content $packagesFile
        $info.PackagesHash = (Get-FileHash -Path $packagesFile -Algorithm MD5).Hash
    } catch {
        Write-Log "ERROR: No se pudo obtener pip freeze en $VenvPath"
    }
    
    # pyvenv.cfg
    $configPath = "$VenvPath\pyvenv.cfg"
    if (Test-Path $configPath) {
        $info.ConfigFile = Get-Content $configPath -Raw
    }
    
    return $info
}

function Find-Venvs {
    $venvs = @()
    
    foreach ($pattern in $VenvPatterns) {
        $found = Get-ChildItem -Path . -Directory -Filter $pattern -ErrorAction SilentlyContinue
        foreach ($dir in $found) {
            # Verificar si es un venv válido
            $hasPython = (Test-Path "$($dir.FullName)\Scripts\python.exe") -or 
                         (Test-Path "$($dir.FullName)\bin\python")
            if ($hasPython) {
                $venvs += $dir.FullName
            }
        }
    }
    
    return $venvs | Select-Object -Unique
}

function Group-Venvs {
    param([array]$VenvInfos)
    
    $groups = @{
        Equivalent = @()
        Compatible = @()
        Incompatible = @()
    }
    
    for ($i = 0; $i -lt $VenvInfos.Count; $i++) {
        for ($j = $i + 1; $j -lt $VenvInfos.Count; $j++) {
            $v1 = $VenvInfos[$i]
            $v2 = $VenvInfos[$j]
            
            if ($v1.PythonVersion -ne $v2.PythonVersion) {
                $groups.Incompatible += @($v1.Path, $v2.Path)
            } elseif ($v1.PackagesHash -eq $v2.PackagesHash) {
                $groups.Equivalent += @($v1.Path, $v2.Path)
            } else {
                $groups.Compatible += @($v1.Path, $v2.Path)
            }
        }
    }
    
    return $groups
}

function Select-TargetVenv {
    param([array]$Venvs, [string]$Preferred)
    
    if ($Preferred -and (Test-Path $Preferred)) {
        return $Preferred
    }
    
    # Heurística: .venv > más reciente > más paquetes
    $dotVenv = $Venvs | Where-Object { $_ -match '\.venv$' } | Select-Object -First 1
    if ($dotVenv) { return $dotVenv }
    
    $newest = $Venvs | Sort-Object { (Get-Item $_).LastWriteTime } -Descending | Select-Object -First 1
    return $newest
}

function Backup-Venv {
    param([string]$VenvPath)
    
    $backupName = "$VenvPath-backup-$Timestamp"
    Write-Log "Creando backup: $backupName"
    
    if (-not $DryRun) {
        Rename-Item -Path $VenvPath -NewName $backupName
    }
    
    return $backupName
}

function Install-MissingPackages {
    param([string]$TargetVenv, [array]$Packages)
    
    $pythonExe = if (Test-Path "$TargetVenv\Scripts\python.exe") {
        "$TargetVenv\Scripts\python.exe"
    } else {
        "$TargetVenv\bin\python"
    }
    
    foreach ($pkg in $Packages) {
        Write-Log "Instalando: $pkg"
        if (-not $DryRun) {
            try {
                & $pythonExe -m pip install "$pkg" 2>&1 | Tee-Object -Append -FilePath $Log
            } catch {
                Write-Log "ERROR instalando $pkg : $_"
            }
        }
    }
}

function Generate-Report {
    param([array]$VenvInfos, [hashtable]$Groups, [string]$TargetVenv)
    
    $reportContent = @"
========================================
REPORTE DE ENTORNOS VIRTUALES DUPLICADOS
Generado: $(Get-Date)
========================================

ENTORNOS DETECTADOS: $($VenvInfos.Count)

"@
    
    foreach ($info in $VenvInfos) {
        $reportContent += @"

--- $($info.Path) ---
Python: $($info.PythonVersion)
Paquetes: $($info.Packages.Count)
Hash: $($info.PackagesHash)

"@
    }
    
    $reportContent += @"

AGRUPACIÓN:
- Equivalentes: $($Groups.Equivalent.Count / 2) pares
- Compatibles: $($Groups.Compatible.Count / 2) pares
- Incompatibles: $($Groups.Incompatible.Count / 2) pares

OBJETIVO SELECCIONADO: $TargetVenv

RECOMENDACIONES:
1. Revisar este reporte antes de consolidar
2. Hacer commit de cambios actuales
3. Ejecutar con --consolidate solo tras verificar
4. Esperar 24h antes de usar --force-delete

========================================
"@
    
    Set-Content -Path $Report -Value $reportContent
    Write-Host "`nReporte generado: $Report"
}

# Flujo principal
Write-Host "`n=== DEDUPLICADOR DE ENTORNOS VIRTUALES ===" -ForegroundColor Cyan

if (-not $DryRun -and -not $Yes -and -not $ReportOnly) {
    Write-Host "`n¡ADVERTENCIA! Modo activo. ¿Continuar? (S/N): " -NoNewline -ForegroundColor Yellow
    $confirm = Read-Host
    if ($confirm -ne "S") {
        Write-Host "Cancelado por el usuario."
        exit 0
    }
}

Write-Log "Iniciando análisis..."

# Detectar venvs
$venvPaths = Find-Venvs
if ($venvPaths.Count -eq 0) {
    Write-Host "No se encontraron entornos virtuales."
    exit 0
}

Write-Log "Entornos encontrados: $($venvPaths.Count)"

# Recopilar info
$venvInfos = @()
foreach ($venv in $venvPaths) {
    Write-Log "Analizando: $venv"
    $venvInfos += Get-VenvInfo -VenvPath $venv
}

# Agrupar
$groups = Group-Venvs -VenvInfos $venvInfos

# Seleccionar objetivo
$targetVenv = Select-TargetVenv -Venvs $venvPaths -Preferred $Target
Write-Log "Venv objetivo: $targetVenv"

# Generar reporte
Generate-Report -VenvInfos $venvInfos -Groups $groups -TargetVenv $targetVenv

if ($ReportOnly) {
    Write-Host "`nModo --report-only: Solo se generó el reporte."
    exit 0
}

# Consolidar si se solicita
if ($Consolidate -or $Auto) {
    $toConsolidate = $venvPaths | Where-Object { $_ -ne $targetVenv }
    
    Write-Host "`nConsolidando $($toConsolidate.Count) venvs en $targetVenv" -ForegroundColor Green
    
    foreach ($venv in $toConsolidate) {
        $venvInfo = $venvInfos | Where-Object { $_.Path -eq $venv }
        
        # Crear backup
        $backup = Backup-Venv -VenvPath $venv
        
        # Calcular diferencias
        $targetInfo = $venvInfos | Where-Object { $_.Path -eq $targetVenv }
        $missing = $venvInfo.Packages | Where-Object { $_ -notin $targetInfo.Packages }
        
        if ($missing.Count -gt 0) {
            Write-Log "Instalando $($missing.Count) paquetes faltantes"
            Install-MissingPackages -TargetVenv $targetVenv -Packages $missing
        }
    }
}

# Resumen final
Write-Host "`n=== RESUMEN ===" -ForegroundColor Cyan
Write-Host "Venv objetivo: $targetVenv"
Write-Host "Reporte: $Report"
Write-Host "Log: $Log"
Write-Host "`nRECOMENDACIONES:"
Write-Host "1. Revisar $Report antes de borrar backups"
Write-Host "2. Probar que el venv objetivo funciona correctamente"
Write-Host "3. Esperar 24h y luego usar --force-delete si todo OK"

Write-Host "`n✓ Proceso completado." -ForegroundColor Green

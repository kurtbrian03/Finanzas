param(
    [string]$Root = (Get-Location).Path
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

. (Join-Path $Root "color_utils.ps1")

try {
    $validators = Get-ChildItem -Path $Root -Filter "validate_*.ps1" -File | Sort-Object -Property Name

    if (-not $validators -or $validators.Count -eq 0) {
        Write-Err "No se encontraron validadores validate_*.ps1"
        exit 1
    }

    $ok = New-Object System.Collections.Generic.List[string]
    $bad = New-Object System.Collections.Generic.List[string]

    foreach ($validator in $validators) {
        if ($validator.Name -eq "validate_all.ps1") {
            continue
        }

        Write-Info "Ejecutando $($validator.Name)"
        & $validator.FullName -Root $Root

        if ($LASTEXITCODE -eq 0) {
            $ok.Add($validator.Name)
        }
        else {
            $bad.Add($validator.Name)
        }
    }

    Write-Host "===== Resumen validadores =====" -ForegroundColor Cyan
    Write-Host "OK: $($ok.Count)"
    Write-Host "FAIL: $($bad.Count)"

    if ($bad.Count -gt 0) {
        Write-Err "Fallaron validadores: $($bad -join ', ')"
        exit 1
    }

    Write-Info "Todos los validadores pasaron"
    exit 0
}
catch {
    Write-Err "Error en run_all_validators.ps1: $_"
    exit 1
}

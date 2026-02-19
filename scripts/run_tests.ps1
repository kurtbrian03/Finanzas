param(
    [string]$Root = (Get-Location).Path,
    [string[]]$TestPaths = @()
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

. (Join-Path $Root "color_utils.ps1")

try {
    Set-Location $Root
    Write-Info "Ejecutando pytest"

    $pythonCmd = "python"
    $venvPython = Join-Path $Root ".venv/Scripts/python.exe"
    if (Test-Path $venvPython) {
        $pythonCmd = $venvPython
    }

    $resolvedTests = New-Object System.Collections.Generic.List[string]

    if ($TestPaths.Count -gt 0) {
        foreach ($t in $TestPaths) {
            $resolvedTests.Add($t)
        }
    }
    else {
        $resolvedTests.Add("tests")

        $gitmodulesPath = Join-Path $Root ".gitmodules"
        $comprasTests = "pinpon_modules/compras/tests"
        $ventasTests = "pinpon_modules/ventas/tests"

        $comprasIsSubmodule = $false
        if (Test-Path $gitmodulesPath) {
            $gm = Get-Content -LiteralPath $gitmodulesPath -Raw
            if ($gm -match '\[submodule "pinpon_modules/compras"\]') {
                $comprasIsSubmodule = $true
            }
        }

        if (Test-Path (Join-Path $Root $comprasTests)) {
            if ($comprasIsSubmodule) {
                Write-Info "Detectado Compras como submódulo Git: se incluyen tests del submódulo"
            }
            else {
                Write-Info "Detectado Compras local: se incluyen tests locales"
            }
            $resolvedTests.Add($comprasTests)
        }

        if (Test-Path (Join-Path $Root $ventasTests)) {
            $resolvedTests.Add($ventasTests)
        }
    }

    & $pythonCmd -m pytest --import-mode=importlib -q @resolvedTests

    if ($LASTEXITCODE -ne 0) {
        Write-Err "Pruebas fallidas"
        exit 1
    }

    Write-Info "Pruebas completadas"
    exit 0
}
catch {
    Write-Err "Error en run_tests.ps1: $_"
    exit 1
}

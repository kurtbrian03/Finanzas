param(
    [string]$Root = (Get-Location).Path
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

. (Join-Path $Root "color_utils.ps1")

try {
    $distPath = Join-Path $Root "dist"
    if (-not (Test-Path $distPath)) {
        New-Item -ItemType Directory -Path $distPath -Force | Out-Null
    }

    $zipPath = Join-Path $distPath ("pinpon_build_{0}.zip" -f (Get-Date -Format "yyyyMMdd_HHmmss"))
    $items = Get-ChildItem -Path $Root -Force | Where-Object { $_.Name -notin @('.git', '.venv', '.pytest_cache', '__pycache__', 'dist') }

    Compress-Archive -Path $items.FullName -DestinationPath $zipPath -CompressionLevel Optimal

    Write-Info "Build generado: $zipPath"
    exit 0
}
catch {
    Write-Err "Error en build.ps1: $_"
    exit 1
}

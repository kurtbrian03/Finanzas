param(
    [string]$PrBody,
    [string]$PrTitle,
    [string]$EventPath = $env:GITHUB_EVENT_PATH
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Info($Message) { Write-Host "[INFO] $Message" -ForegroundColor Cyan }
function Write-Warn($Message) { Write-Host "[WARN] $Message" -ForegroundColor Yellow }

try {
    if ([string]::IsNullOrWhiteSpace($PrBody) -and (Test-Path $EventPath)) {
        $payload = Get-Content -LiteralPath $EventPath -Raw | ConvertFrom-Json
        if ($payload.pull_request) {
            $PrBody = [string]$payload.pull_request.body
            if ([string]::IsNullOrWhiteSpace($PrTitle)) {
                $PrTitle = [string]$payload.pull_request.title
            }
        }
    }

    if ([string]::IsNullOrWhiteSpace($PrBody)) {
        Write-Warn "No se detectó cuerpo de PR. Validación checklist omitida."
        exit 0
    }

    $unchecked = [regex]::Matches($PrBody, "(?m)^\s*-\s*\[\s\]\s+.+$")
    $checked = [regex]::Matches($PrBody, "(?m)^\s*-\s*\[[xX]\]\s+.+$")

    Write-Info "Checklist detectado: marcadas=$($checked.Count), sin_marcar=$($unchecked.Count)"

    if ($unchecked.Count -gt 0) {
        Write-Warn "Hay casillas sin marcar en el checklist (informativo, no bloqueante)."
        $preview = $unchecked | Select-Object -First 8
        foreach ($item in $preview) {
            Write-Warn ("Pendiente: " + $item.Value.Trim())
        }
        if ($unchecked.Count -gt 8) {
            Write-Warn "... y $($unchecked.Count - 8) pendientes adicionales"
        }
    }

    if (-not [string]::IsNullOrWhiteSpace($PrTitle)) {
        $title = $PrTitle.ToLowerInvariant()
        $suggested = "general"
        if ($title.Contains("ci")) { $suggested = "ci_cd" }
        elseif ($title.Contains("marketplace")) { $suggested = "marketplace" }
        elseif ($title.Contains("loader")) { $suggested = "loader" }
        elseif ($title.Contains("submodule")) { $suggested = "submodule" }
        elseif ($title.Contains("pip")) { $suggested = "pip_module" }
        elseif ($title.Contains("erp")) { $suggested = "erp_module" }

        Write-Info "Plantilla sugerida por título: $suggested"
    }

    exit 0
}
catch {
    Write-Warn "validate_checklist.ps1 encontró una excepción no bloqueante: $($_.Exception.Message)"
    exit 0
}

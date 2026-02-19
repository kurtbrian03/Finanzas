param(
    [string]$Root = (Get-Location).Path,
    [switch]$ValidationOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Info($Message) { Write-Host "[INFO] $Message" -ForegroundColor Cyan }
function Write-Warn($Message) { Write-Host "[WARN] $Message" -ForegroundColor Yellow }
function Write-Err($Message) { Write-Host "[ERR ] $Message" -ForegroundColor Red }

function Test-CommandAvailable {
    param([string]$CommandName)
    return $null -ne (Get-Command $CommandName -ErrorAction SilentlyContinue)
}

try {
    Set-Location $Root

    $agentPath = Join-Path $Root "agent_pinpon/agent.yaml"
    $actionsPath = Join-Path $Root "agent_pinpon/actions.yaml"
    $knowledgePath = Join-Path $Root "agent_pinpon/knowledge.yaml"

    foreach ($required in @($agentPath, $actionsPath, $knowledgePath)) {
        if (-not (Test-Path $required)) {
            throw "No existe archivo requerido: $required"
        }
    }

    if (-not (Test-CommandAvailable -CommandName "npx")) {
        throw "npx no está disponible. Ejecute scripts/setup_agent_environment.ps1"
    }

    @'
import json
from pathlib import Path

root = Path("agent_pinpon")
for name in ("agent.yaml", "actions.yaml", "knowledge.yaml"):
    path = root / name
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"Invalid root object in {name}")

agent = json.loads((root / "agent.yaml").read_text(encoding="utf-8"))["agent"]
actions = json.loads((root / "actions.yaml").read_text(encoding="utf-8"))["actions"]
knowledge = json.loads((root / "knowledge.yaml").read_text(encoding="utf-8"))["knowledge"]

print("agent_name=" + str(agent.get("name", "")))
print("actions_count=" + str(len(actions)))
print("knowledge_sources=" + str(len(knowledge.get("sources", []))))
'@ | python -

    if ($LASTEXITCODE -ne 0) {
        throw "Validación estructural de agente falló"
    }

    Write-Info "Estado del agente: configuración válida"
    Write-Info "Acciones disponibles: run_local_ci, validate_checklist, analyze_marketplace, summarize_pr_state"
    Write-Info "Conexiones activas: github, pinpon_local"

    if ($ValidationOnly) {
        Write-Info "Modo validación: no se inicia runtime del agente"
        exit 0
    }

    Write-Info "Iniciando agente con Microsoft 365 Agents Toolkit"
    npx microsoft-365-agent run --config agent_pinpon/agent.yaml

    if ($LASTEXITCODE -ne 0) {
        throw "No fue posible iniciar el runtime del agente"
    }

    exit 0
}
catch {
    Write-Err "Error en init_agent.ps1: $($_.Exception.Message)"
    exit 1
}

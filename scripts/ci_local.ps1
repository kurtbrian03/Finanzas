param(
    [string]$Root = (Get-Location).Path,
    [switch]$AutoChecklistKeep,
    [int]$PrNumber = 0,
    [switch]$RunRouterTitleTest,
    [switch]$RunAgentValidation
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Info($Message) { Write-Host "[INFO] $Message" -ForegroundColor Cyan }
function Write-Warn($Message) { Write-Host "[WARN] $Message" -ForegroundColor Yellow }
function Write-Err($Message) { Write-Host "[ERR ] $Message" -ForegroundColor Red }

function Invoke-Step {
    param(
        [Parameter(Mandatory=$true)][string]$Name,
        [Parameter(Mandatory=$true)][scriptblock]$Action
    )

    try {
        $stepOutput = & $Action 2>&1 | Out-String
        if ($LASTEXITCODE -ne 0) {
            return @{ ok = $false; output = "exit_code=$LASTEXITCODE; $stepOutput" }
        }
        return @{ ok = $true; output = $stepOutput.Trim() }
    }
    catch {
        return @{ ok = $false; output = $_.Exception.Message }
    }
}

try {
    Set-Location $Root

    $repoRemote = "skipped"
    $pipPackage = "skipped"
    $submoduleStatus = "not-run"
    $submoduleValidationStatus = "not-run"
    $marketplaceStatus = "not-run"
    $loaderStatus = "not-run"
    $testsStatus = "not-run"
    $routerTitleTestStatus = "not-run"
    $agentEnvironmentStatus = "not-run"
    $agentConfigStatus = "not-run"
    $agentActionsStatus = "not-run"
    $agentKnowledgeStatus = "not-run"
    $autoKeepStatus = "skipped"
    $autoKeepMarked = 0
    $autoKeepPending = 0
    $autoKeepIgnored = 0

    $hasGithub = -not [string]::IsNullOrWhiteSpace($env:GITHUB_TOKEN)
    $hasPypi = -not [string]::IsNullOrWhiteSpace($env:PYPI_TOKEN)

    Write-Info "Token status => GITHUB_TOKEN=$hasGithub ; PYPI_TOKEN=$hasPypi"

    if ($hasGithub) {
        Write-Info "Ejecutando create_remote_repo.ps1"
        $r = Invoke-Step -Name "create_remote_repo" -Action { pwsh ./scripts/create_remote_repo.ps1 }
        $repoRemote = if ($r.ok) { "ok_or_exists" } else { "failed: $($r.output)" }
    }

    if ($hasPypi) {
        Write-Info "Ejecutando publish_pip_compras.ps1"
        $r = Invoke-Step -Name "publish_pip" -Action { pwsh ./scripts/publish_pip_compras.ps1 -Root $Root }
        $pipPackage = if ($r.ok) { "published_or_exists" } else { "failed: $($r.output)" }
    }

    Write-Info "Ejecutando convert_compras_to_submodule.ps1"
    $rSub = Invoke-Step -Name "convert_submodule" -Action { pwsh ./scripts/convert_compras_to_submodule.ps1 -Root $Root }
    $submoduleStatus = if ($rSub.ok) { "ok_or_skipped" } else { "failed: $($rSub.output)" }

    Write-Info "Validando estado de submódulos"
    if (Test-Path (Join-Path $Root ".gitmodules")) {
        $submoduleLines = git submodule status --recursive 2>&1 | Out-String
        if ($LASTEXITCODE -eq 0) {
            $submoduleValidationStatus = "ok"
            if ($submoduleLines.Trim()) {
                Write-Info "submodule_status_raw => $($submoduleLines.Trim())"
            }
            else {
                Write-Info "Submódulos declarados sin entradas activas"
            }
        }
        else {
            $submoduleValidationStatus = "failed"
        }
    }
    else {
        $submoduleValidationStatus = "no-gitmodules"
    }

    Write-Info "Validando marketplace"
    $pythonCmd = "python"
    $venvPython = Join-Path $Root ".venv/Scripts/python.exe"
    if (Test-Path $venvPython) {
        $pythonCmd = $venvPython
    }

    @'
from pinpon_marketplace.installer import list_available_modules

mods = list_available_modules()
required = {"erp_compras", "erp_ventas", "erp_inventarios"}
ids = {m.get("id") for m in mods}
modes = {m.get("installation_mode") for m in mods}

if not required.issubset(ids):
    missing = sorted(required - ids)
    raise SystemExit(f"missing_registry={missing}")

recognized_modes = {"none", "local", "submodule", "pip"}
if not modes.issubset(recognized_modes):
    bad = sorted(modes - recognized_modes)
    raise SystemExit(f"invalid_modes={bad}")

has_three = {"local", "pip", "submodule"}.issubset(modes)
if has_three:
    print("marketplace_all_modes")
else:
    print("marketplace_partial_modes=" + ",".join(sorted(modes)))
'@ | & $pythonCmd -
    if ($LASTEXITCODE -eq 0) {
        $marketplaceStatus = "ok"
    }
    else {
        $marketplaceStatus = "failed"
    }

    Write-Info "Validando loader dinámico"
    @'
from pinpon_marketplace.installer import list_available_modules
from pinpon_modules import load_module

failures = []
for module in list_available_modules():
    if module.get("installation_mode") == "none":
        continue
    module_id = module["id"]
    try:
        load_module(module_id)
    except Exception as exc:
        failures.append((module_id, str(exc)))

if failures:
    raise SystemExit(f"loader_failures={failures}")

print("loader_ok")
'@ | & $pythonCmd -
    if ($LASTEXITCODE -eq 0) {
        $loaderStatus = "ok"
    }
    else {
        $loaderStatus = "failed"
    }

    Write-Info "Ejecutando run_tests.ps1"
    $rTests = Invoke-Step -Name "run_tests" -Action { pwsh ./scripts/run_tests.ps1 -Root $Root }
    $testsStatus = if ($rTests.ok) { "passed" } else { "failed: $($rTests.output)" }

    if ($RunRouterTitleTest) {
        Write-Info "Ejecutando test opcional de router por título"
        try {
            & $pythonCmd -m pytest --import-mode=importlib -q tests/test_router_title.py | Out-Null
            if ($LASTEXITCODE -eq 0) {
                $routerTitleTestStatus = "passed_optional"
            }
            else {
                $routerTitleTestStatus = "failed_optional"
            }
        }
        catch {
            $routerTitleTestStatus = "failed_optional"
        }
    }

    if ($RunAgentValidation) {
        Write-Info "Ejecutando validación opcional de entorno de agente"
        $rAgentEnv = Invoke-Step -Name "setup_agent_environment" -Action {
            pwsh ./scripts/setup_agent_environment.ps1 -Root $Root
        }
        $agentEnvironmentStatus = if ($rAgentEnv.ok) { "ok_optional" } else { "failed_optional" }

        Write-Info "Ejecutando validación opcional de configuración de agente"
        $rAgentInit = Invoke-Step -Name "init_agent_validation" -Action {
            pwsh ./scripts/init_agent.ps1 -Root $Root -ValidationOnly
        }

        if ($rAgentInit.ok) {
            $agentConfigStatus = "ok_optional"
            $agentActionsStatus = "ok_optional"
            $agentKnowledgeStatus = "ok_optional"
        }
        else {
            $agentConfigStatus = "failed_optional"
            $agentActionsStatus = "failed_optional"
            $agentKnowledgeStatus = "failed_optional"
        }
    }

    if ($AutoChecklistKeep) {
        if (-not $hasGithub) {
            Write-Warn "AutoChecklistKeep solicitado pero GITHUB_TOKEN no está disponible."
            $autoKeepStatus = "skipped_no_token"
        }
        else {
            Write-Info "Ejecutando auto_checklist_keep.ps1"
            $summaryPath = Join-Path $Root ".auto_keep_summary.json"

            if (Test-Path $summaryPath) {
                Remove-Item -LiteralPath $summaryPath -Force
            }

            if ($PrNumber -gt 0) {
                $rKeep = Invoke-Step -Name "auto_keep" -Action {
                    pwsh ./scripts/auto_checklist_keep.ps1 -PrNumber $PrNumber -SummaryPath $summaryPath
                }
            }
            else {
                $rKeep = Invoke-Step -Name "auto_keep" -Action {
                    pwsh ./scripts/auto_checklist_keep.ps1 -SummaryPath $summaryPath
                }
            }

            if ($rKeep.ok) {
                $autoKeepStatus = "ok"
            }
            else {
                $autoKeepStatus = "failed: $($rKeep.output)"
            }

            if (Test-Path $summaryPath) {
                try {
                    $sum = Get-Content -LiteralPath $summaryPath -Raw | ConvertFrom-Json
                    $autoKeepMarked = [int]$sum.marked_count
                    $autoKeepIgnored = [int]$sum.ignored_count
                    $autoKeepPending = [int]$sum.not_applicable_count
                }
                catch {
                    Write-Warn "No se pudo parsear resumen de auto-keep"
                }
                finally {
                    Remove-Item -LiteralPath $summaryPath -Force -ErrorAction SilentlyContinue
                }
            }
        }
    }

    Write-Host ""
    Write-Host "===== PINPON CI LOCAL SUMMARY =====" -ForegroundColor Green
    Write-Host "repo_remote=$repoRemote"
    Write-Host "pip_package=$pipPackage"
    Write-Host "submodule_status=$submoduleStatus"
    Write-Host "submodule_validation_status=$submoduleValidationStatus"
    Write-Host "marketplace_status=$marketplaceStatus"
    Write-Host "loader_status=$loaderStatus"
    Write-Host "tests_status=$testsStatus"
    Write-Host "router_title_test_status=$routerTitleTestStatus"
    Write-Host "agent_environment_status=$agentEnvironmentStatus"
    Write-Host "agent_config_status=$agentConfigStatus"
    Write-Host "agent_actions_status=$agentActionsStatus"
    Write-Host "agent_knowledge_status=$agentKnowledgeStatus"
    Write-Host "auto_keep_status=$autoKeepStatus"
    Write-Host "auto_keep_marked=$autoKeepMarked"
    Write-Host "auto_keep_pending=$autoKeepPending"
    Write-Host "auto_keep_ignored=$autoKeepIgnored"

    if ($testsStatus -like "failed*" -or $loaderStatus -eq "failed" -or $marketplaceStatus -eq "failed" -or $submoduleValidationStatus -eq "failed") {
        exit 1
    }

    exit 0
}
catch {
    Write-Err "Error en ci_local.ps1: $($_.Exception.Message)"
    exit 1
}

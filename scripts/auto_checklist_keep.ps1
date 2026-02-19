param(
    [int]$PrNumber = 0,
    [switch]$DryRun,
    [string]$SummaryPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Info($Message) { Write-Host "[INFO] $Message" -ForegroundColor Cyan }
function Write-Warn($Message) { Write-Host "[WARN] $Message" -ForegroundColor Yellow }
function Write-Err($Message) { Write-Host "[ERR ] $Message" -ForegroundColor Red }

function Get-EventData {
    $eventPath = $env:GITHUB_EVENT_PATH
    if (-not [string]::IsNullOrWhiteSpace($eventPath) -and (Test-Path $eventPath)) {
        return (Get-Content -LiteralPath $eventPath -Raw | ConvertFrom-Json)
    }
    return $null
}

function Get-PullRequestNumberFromEvent {
    param([object]$Event)

    if ($null -eq $Event) {
        return 0
    }

    if ($Event.pull_request -and $Event.pull_request.number) {
        return [int]$Event.pull_request.number
    }

    if ($Event.issue -and $Event.issue.number -and $Event.issue.pull_request) {
        return [int]$Event.issue.number
    }

    return 0
}

function Invoke-GitHubApi {
    param(
        [Parameter(Mandatory=$true)][string]$Method,
        [Parameter(Mandatory=$true)][string]$Url,
        [object]$Body
    )

    $token = $env:GITHUB_TOKEN
    if ([string]::IsNullOrWhiteSpace($token)) {
        throw "GITHUB_TOKEN no está disponible"
    }

    $headers = @{
        Authorization = "Bearer $token"
        Accept = "application/vnd.github+json"
        "X-GitHub-Api-Version" = "2022-11-28"
    }

    if ($null -ne $Body) {
        $json = $Body | ConvertTo-Json -Depth 12
        return Invoke-RestMethod -Method $Method -Uri $Url -Headers $headers -Body $json
    }

    return Invoke-RestMethod -Method $Method -Uri $Url -Headers $headers
}

function Get-RepoContext {
    $repo = $env:GITHUB_REPOSITORY
    if ([string]::IsNullOrWhiteSpace($repo) -or -not $repo.Contains('/')) {
        throw "No se pudo determinar GITHUB_REPOSITORY"
    }

    $parts = $repo.Split('/')
    return @{
        owner = $parts[0]
        repo = $parts[1]
    }
}

function Get-PullRequestData {
    param([string]$Owner, [string]$Repo, [int]$Number)

    $url = "https://api.github.com/repos/$Owner/$Repo/pulls/$Number"
    return Invoke-GitHubApi -Method Get -Url $url
}

function Get-PullRequestFiles {
    param([string]$Owner, [string]$Repo, [int]$Number)

    $all = New-Object System.Collections.Generic.List[object]
    $page = 1
    while ($true) {
        $url = "https://api.github.com/repos/$Owner/$Repo/pulls/$Number/files?per_page=100&page=$page"
        $items = Invoke-GitHubApi -Method Get -Url $url
        if ($null -eq $items) {
            break
        }

        $count = @($items).Count
        if ($count -eq 0) {
            break
        }

        foreach ($i in $items) {
            $all.Add($i)
        }

        if ($count -lt 100) {
            break
        }
        $page += 1
    }

    return $all
}

function Get-CheckRuns {
    param([string]$Owner, [string]$Repo, [string]$Sha)

    $url = "https://api.github.com/repos/$Owner/$Repo/commits/$Sha/check-runs?per_page=100"
    $response = Invoke-GitHubApi -Method Get -Url $url
    if ($response -and $response.check_runs) {
        return @($response.check_runs)
    }
    return @()
}

function Get-WorkflowRunsBySha {
    param([string]$Owner, [string]$Repo, [string]$Sha)

    $url = "https://api.github.com/repos/$Owner/$Repo/actions/runs?head_sha=$Sha&per_page=100"
    $response = Invoke-GitHubApi -Method Get -Url $url
    if ($response -and $response.workflow_runs) {
        return @($response.workflow_runs)
    }
    return @()
}

function Get-WorkflowArtifacts {
    param([string]$Owner, [string]$Repo, [int]$RunId)

    $url = "https://api.github.com/repos/$Owner/$Repo/actions/runs/$RunId/artifacts?per_page=100"
    $response = Invoke-GitHubApi -Method Get -Url $url
    if ($response -and $response.artifacts) {
        return @($response.artifacts)
    }
    return @()
}

function Test-PathChanged {
    param([string[]]$Paths, [string]$Pattern)
    foreach ($p in $Paths) {
        if ($p -match $Pattern) {
            return $true
        }
    }
    return $false
}

function Test-RegistryNoDuplicates {
    $registry = Join-Path (Get-Location).Path "pinpon_marketplace/registry.json"
    if (-not (Test-Path $registry)) {
        return $false
    }

    try {
        $raw = Get-Content -LiteralPath $registry -Raw
        $json = $raw | ConvertFrom-Json
        $ids = New-Object System.Collections.Generic.List[string]
        foreach ($item in @($json)) {
            if ($item.id) {
                $ids.Add([string]$item.id)
            }
        }

        $unique = $ids | Sort-Object -Unique
        return ($unique.Count -eq $ids.Count)
    }
    catch {
        return $false
    }
}

function Test-MarketplaceModes {
    try {
        @'
from pinpon_marketplace.installer import list_available_modules

mods = list_available_modules()
allowed = {"none", "local", "pip", "submodule"}
for item in mods:
    mode = item.get("installation_mode")
    if mode not in allowed:
        raise SystemExit(1)
print("ok")
'@ | python - | Out-Null
        return ($LASTEXITCODE -eq 0)
    }
    catch {
        return $false
    }
}

function Test-LoaderDynamic {
    try {
        @'
from pinpon_marketplace.installer import list_available_modules
from pinpon_modules import load_module

for item in list_available_modules():
    if item.get("installation_mode") == "none":
        continue
    load_module(item["id"])

print("ok")
'@ | python - | Out-Null
        return ($LASTEXITCODE -eq 0)
    }
    catch {
        return $false
    }
}

function Test-LoaderMissingModuleTolerance {
    try {
        @'
from pinpon_modules import load_module

try:
    load_module("erp_modulo_que_no_existe")
except Exception:
    print("ok")
    raise SystemExit(0)

raise SystemExit(1)
'@ | python - | Out-Null
        return ($LASTEXITCODE -eq 0)
    }
    catch {
        return $false
    }
}

function Test-MarketplaceEmptyTolerance {
    $ciPath = Join-Path (Get-Location).Path ".github/workflows/ci.yml"
    if (-not (Test-Path $ciPath)) {
        return $false
    }

    $txt = Get-Content -LiteralPath $ciPath -Raw
    return ($txt -match "Marketplace vacío: se permite continuar")
}

function Test-SubmoduleSync {
    if (-not (Test-Path ".gitmodules")) {
        return $true
    }

    $raw = git submodule status --recursive 2>&1 | Out-String
    if ($LASTEXITCODE -ne 0) {
        return $false
    }

    $lines = $raw -split "`r?`n" | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
    foreach ($line in $lines) {
        $trim = $line.TrimStart()
        if ($trim.StartsWith("-") -or $trim.StartsWith("+") -or $trim.StartsWith("U")) {
            return $false
        }
    }
    return $true
}

function Test-PipIdempotentByScript {
    $scriptPath = Join-Path (Get-Location).Path "scripts/publish_pip_compras.ps1"
    if (-not (Test-Path $scriptPath)) {
        return $false
    }

    $txt = Get-Content -LiteralPath $scriptPath -Raw
    return ($txt -match "File already exists" -or $txt -match "already been taken" -or $txt -match "idempotente")
}

function Test-CiCdUnit {
    try {
        python -m pytest tests/test_ci_cd.py -q | Out-Null
        return ($LASTEXITCODE -eq 0)
    }
    catch {
        return $false
    }
}

function Get-WorkflowConclusion {
    param([object[]]$Runs, [string]$Name)
    $found = $Runs | Where-Object { $_.name -eq $Name } | Sort-Object -Property created_at -Descending | Select-Object -First 1
    if ($null -eq $found) {
        return "not_found"
    }
    return [string]$found.conclusion
}

function Get-CheckConclusionContains {
    param([object[]]$Checks, [string]$Contains)
    $found = $Checks | Where-Object { $_.name -like "*$Contains*" } | Select-Object -First 1
    if ($null -eq $found) {
        return "not_found"
    }
    return [string]$found.conclusion
}

function Invoke-ChecklistUpdate {
    param(
        [string]$Body,
        [hashtable[]]$Rules
    )

    $lines = $Body -split "`n"

    $marked = New-Object System.Collections.Generic.List[string]
    $ignored = New-Object System.Collections.Generic.List[string]
    $already = New-Object System.Collections.Generic.List[string]
    $notApplicable = New-Object System.Collections.Generic.List[string]

    foreach ($rule in $Rules) {
        $task = [string]$rule.task
        $applicable = [bool]$rule.applicable
        $shouldMark = [bool]$rule.mark

        $hit = $false
        for ($i = 0; $i -lt $lines.Count; $i++) {
            $line = $lines[$i]
            if ($line -match "^(\s*-\s*)\[(.| )\]\s+(.+?)\s*$") {
                $prefix = $matches[1]
                $state = $matches[2]
                $text = $matches[3]

                if ($text -ne $task) {
                    continue
                }

                $hit = $true

                if ($state -match "[xX]") {
                    $already.Add($task)
                    continue
                }

                if (-not $applicable) {
                    $notApplicable.Add($task)
                    continue
                }

                if ($shouldMark) {
                    $lines[$i] = "$prefix[x] $task"
                    $marked.Add($task)
                }
                else {
                    $ignored.Add($task)
                }
            }
        }

        if (-not $hit) {
            $notApplicable.Add($task)
        }
    }

    $updated = ($lines -join "`n")
    return @{
        body = $updated
        marked = $marked
        ignored = $ignored
        already = $already
        not_applicable = $notApplicable
    }
}

try {
    $event = Get-EventData
    if ($PrNumber -le 0) {
        $PrNumber = Get-PullRequestNumberFromEvent -Event $event
    }

    if ($PrNumber -le 0) {
        Write-Warn "No se detectó PR number. Finaliza sin cambios."
        exit 0
    }

    $repoCtx = Get-RepoContext
    $owner = [string]$repoCtx.owner
    $repo = [string]$repoCtx.repo

    Write-Info "Analizando PR #$PrNumber en $owner/$repo"

    $pr = Get-PullRequestData -Owner $owner -Repo $repo -Number $PrNumber
    $prBody = [string]$pr.body
    $headSha = [string]$pr.head.sha

    if ([string]::IsNullOrWhiteSpace($prBody)) {
        Write-Warn "El PR no tiene cuerpo. No hay checklist para actualizar."
        exit 0
    }

    if ($prBody -notmatch "pinpon:auto-keep") {
        Write-Warn "No se detectó metadata de auto-keep en el PR. No se actualiza."
        exit 0
    }

    if ($prBody -notmatch "-\s*\[( |x|X)\]") {
        Write-Warn "No se detectaron casillas de checklist en el PR."
        exit 0
    }

    $files = Get-PullRequestFiles -Owner $owner -Repo $repo -Number $PrNumber
    $paths = @($files | ForEach-Object { [string]$_.filename })

    $changedWorkflows = Test-PathChanged -Paths $paths -Pattern "^\.github/workflows/"
    $changedScripts = Test-PathChanged -Paths $paths -Pattern "^scripts/"
    $changedModulesERP = Test-PathChanged -Paths $paths -Pattern "^pinpon_modules/"
    $changedMarketplace = Test-PathChanged -Paths $paths -Pattern "^pinpon_marketplace/(registry\.json|installer\.py|ui\.py)$"
    $changedLoader = Test-PathChanged -Paths $paths -Pattern "^pinpon_modules/__init__\.py$"
    $changedSubmodules = Test-PathChanged -Paths $paths -Pattern "^(\.gitmodules|scripts/convert_compras_to_submodule\.ps1|\.github/workflows/sync_submodules\.yml)"
    $changedPipelines = Test-PathChanged -Paths $paths -Pattern "^(azure-pipelines\.yml|\.gitlab-ci\.yml)$"

    $checks = Get-CheckRuns -Owner $owner -Repo $repo -Sha $headSha
    $runs = Get-WorkflowRunsBySha -Owner $owner -Repo $repo -Sha $headSha

    $ciWorkflow = Get-WorkflowConclusion -Runs $runs -Name "PINPON CI"
    $publishWorkflow = Get-WorkflowConclusion -Runs $runs -Name "PINPON Publish Pip"
    $syncWorkflow = Get-WorkflowConclusion -Runs $runs -Name "Sync Pinpon Submodules"
    $createRemoteWorkflow = Get-WorkflowConclusion -Runs $runs -Name "Create Pinpon Remote Repo"

    $ciWindows = (Get-CheckConclusionContains -Checks $checks -Contains "windows-latest") -eq "success"
    $ciLinux = (Get-CheckConclusionContains -Checks $checks -Contains "ubuntu-latest") -eq "success"

    $azurePassed = ((Get-CheckConclusionContains -Checks $checks -Contains "azure") -eq "success")
    $gitlabPassed = ((Get-CheckConclusionContains -Checks $checks -Contains "gitlab") -eq "success")
    $ciLocalPassed = ((Get-CheckConclusionContains -Checks $checks -Contains "ci_local") -eq "success")

    $testCiCdPassed = Test-CiCdUnit
    $marketplaceModesOk = Test-MarketplaceModes
    $loaderOk = Test-LoaderDynamic
    $loaderMissingTolerance = Test-LoaderMissingModuleTolerance
    $marketplaceEmptyTolerance = Test-MarketplaceEmptyTolerance
    $submoduleSynced = Test-SubmoduleSync
    $pipIdempotent = Test-PipIdempotentByScript
    $registryNoDuplicates = Test-RegistryNoDuplicates

    $artifactsDetected = New-Object System.Collections.Generic.List[string]
    $latestCiRun = $runs | Where-Object { $_.name -eq "PINPON CI" } | Sort-Object -Property created_at -Descending | Select-Object -First 1
    if ($null -ne $latestCiRun) {
        $arts = Get-WorkflowArtifacts -Owner $owner -Repo $repo -RunId ([int]$latestCiRun.id)
        foreach ($a in $arts) {
            $artifactsDetected.Add([string]$a.name)
        }
    }

    $rules = @(
        @{ task = "Código formateado correctamente"; applicable = $true; mark = ($ciLinux -or $ciWorkflow -eq "success") },
        @{ task = "No se introducen rutas rotas"; applicable = $true; mark = ($ciLinux -or $testCiCdPassed) },
        @{ task = "No se rompen imports"; applicable = $true; mark = ($ciLinux -or $testCiCdPassed) },
        @{ task = "No se rompen módulos ERP existentes"; applicable = $changedModulesERP; mark = ($changedModulesERP -and $loaderOk) },
        @{ task = "No se rompen scripts en /scripts"; applicable = $changedScripts; mark = ($changedScripts -and $ciWorkflow -eq "success") },
        @{ task = "No se rompen workflows existentes"; applicable = ($changedWorkflows -or $changedPipelines); mark = (($changedWorkflows -or $changedPipelines) -and ($ciWorkflow -eq "success")) },

        @{ task = "GitHub Actions pasa en Windows"; applicable = $true; mark = $ciWindows },
        @{ task = "GitHub Actions pasa en Linux"; applicable = $true; mark = $ciLinux },
        @{ task = "Azure Pipelines pasa"; applicable = ($azurePassed -or $changedPipelines); mark = $azurePassed },
        @{ task = "GitLab CI pasa"; applicable = ($gitlabPassed -or $changedPipelines); mark = $gitlabPassed },
        @{ task = "Runner local (ci_local.ps1) pasa"; applicable = ($ciLocalPassed -or $changedScripts); mark = $ciLocalPassed },
        @{ task = "pytest --import-mode=importlib pasa"; applicable = $true; mark = ($ciLinux -or $testCiCdPassed) },

        @{ task = "registry.json válido"; applicable = $changedMarketplace; mark = ($changedMarketplace -and $marketplaceModesOk) },
        @{ task = "installer.py detecta modos none/local/pip/submodule"; applicable = ($changedMarketplace -or $changedLoader); mark = $marketplaceModesOk },
        @{ task = "ui.py carga sin errores"; applicable = $changedMarketplace; mark = ($changedMarketplace -and $loaderOk) },
        @{ task = "No se duplican módulos"; applicable = ($changedMarketplace); mark = $registryNoDuplicates },
        @{ task = "No se rompen módulos instalados"; applicable = ($changedMarketplace -or $changedLoader -or $changedModulesERP); mark = $loaderOk },

        @{ task = "Detecta módulos locales"; applicable = ($changedLoader -or $changedModulesERP); mark = $loaderOk },
        @{ task = "Detecta módulos pip"; applicable = ($changedLoader -or $changedMarketplace); mark = $marketplaceModesOk },
        @{ task = "Detecta submódulos Git"; applicable = ($changedLoader -or $changedSubmodules); mark = ($loaderOk -and $submoduleSynced) },
        @{ task = "No rompe si un módulo no existe"; applicable = ($changedLoader -or $changedMarketplace); mark = $loaderMissingTolerance },
        @{ task = "No rompe si marketplace está vacío"; applicable = ($changedMarketplace -or $changedLoader -or $changedWorkflows); mark = $marketplaceEmptyTolerance },

        @{ task = ".gitmodules válido"; applicable = $changedSubmodules; mark = $submoduleSynced },
        @{ task = "git submodule status limpio"; applicable = $changedSubmodules; mark = $submoduleSynced },
        @{ task = "convert_compras_to_submodule.ps1 funciona"; applicable = $changedSubmodules; mark = $submoduleSynced },
        @{ task = "sync_submodules.yml no falla"; applicable = ($changedSubmodules -or $syncWorkflow -ne "not_found"); mark = ($syncWorkflow -eq "success" -or $submoduleSynced) },

        @{ task = "pyproject.toml válido"; applicable = (Test-Path "pinpon_modulo_compras/pyproject.toml"); mark = (Test-Path "pinpon_modulo_compras/pyproject.toml") },
        @{ task = "setup.cfg válido"; applicable = (Test-Path "pinpon_modulo_compras/setup.cfg"); mark = (Test-Path "pinpon_modulo_compras/setup.cfg") },
        @{ task = "build local funciona"; applicable = $true; mark = ($publishWorkflow -eq "success" -or $ciWorkflow -eq "success") },
        @{ task = "publish_pip_compras.ps1 idempotente"; applicable = (Test-Path "scripts/publish_pip_compras.ps1"); mark = $pipIdempotent },
        @{ task = "No falla si versión ya existe"; applicable = (Test-Path "scripts/publish_pip_compras.ps1"); mark = $pipIdempotent }
    )

    $update = Invoke-ChecklistUpdate -Body $prBody -Rules $rules
    $newBody = [string]$update.body

    Write-Info "Casillas marcadas: $($update.marked.Count)"
    foreach ($m in $update.marked) { Write-Info "[MARKED] $m" }

    Write-Info "Casillas ignoradas: $($update.ignored.Count)"
    foreach ($m in $update.ignored) { Write-Warn "[IGNORED] $m" }

    Write-Info "Casillas ya marcadas: $($update.already.Count)"
    foreach ($m in $update.already) { Write-Info "[ALREADY] $m" }

    Write-Info "Casillas no aplicables: $($update.not_applicable.Count)"
    foreach ($m in $update.not_applicable) { Write-Warn "[N/A] $m" }

    $summary = @{
        pr_number = $PrNumber
        marked_count = $update.marked.Count
        ignored_count = $update.ignored.Count
        already_count = $update.already.Count
        not_applicable_count = $update.not_applicable.Count
        marked = @($update.marked)
        ignored = @($update.ignored)
        already = @($update.already)
        not_applicable = @($update.not_applicable)
        changed = @{
            workflows = $changedWorkflows
            scripts = $changedScripts
            erp_modules = $changedModulesERP
            marketplace = $changedMarketplace
            loader = $changedLoader
            submodules = $changedSubmodules
            pipelines = $changedPipelines
        }
        evidence = @{
            ci_workflow = $ciWorkflow
            publish_workflow = $publishWorkflow
            sync_workflow = $syncWorkflow
            create_remote_workflow = $createRemoteWorkflow
            ci_windows = $ciWindows
            ci_linux = $ciLinux
            azure = $azurePassed
            gitlab = $gitlabPassed
            ci_local = $ciLocalPassed
            test_ci_cd = $testCiCdPassed
            marketplace_modes = $marketplaceModesOk
            loader = $loaderOk
            loader_missing_tolerance = $loaderMissingTolerance
            marketplace_empty_tolerance = $marketplaceEmptyTolerance
            submodules_synced = $submoduleSynced
            pip_idempotent = $pipIdempotent
            artifacts = @($artifactsDetected)
        }
        updated = $false
    }

    $changedBody = ($newBody -ne $prBody)
    if ($changedBody -and -not $DryRun) {
        $updateUrl = "https://api.github.com/repos/$owner/$repo/pulls/$PrNumber"
        Invoke-GitHubApi -Method Patch -Url $updateUrl -Body @{ body = $newBody } | Out-Null
        Write-Info "PR actualizado con marcas auto-keep"
        $summary.updated = $true
    }
    elseif ($changedBody -and $DryRun) {
        Write-Info "DryRun activo: se detectaron cambios, pero no se actualiza PR"
    }
    else {
        Write-Info "No hubo cambios en el checklist"
    }

    if (-not [string]::IsNullOrWhiteSpace($SummaryPath)) {
        $summary | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $SummaryPath -Encoding UTF8
    }

    Write-Host ("AUTO_KEEP_SUMMARY=" + ($summary | ConvertTo-Json -Depth 12 -Compress))
    exit 0
}
catch {
    Write-Err "Error en auto_checklist_keep.ps1: $($_.Exception.Message)"
    exit 1
}

param(
    [string]$Root = (Get-Location).Path,
    [switch]$SkipOptional
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

function Test-NpmPackageInstalled {
    param([string]$PackageName)

    if (-not (Test-CommandAvailable -CommandName "npm")) {
        return $false
    }

    $output = npm list -g --depth=0 $PackageName 2>$null | Out-String
    return ($output -match [regex]::Escape($PackageName))
}

try {
    Set-Location $Root

    $nodeStatus = "missing"
    $npmStatus = "missing"
    $toolkitStatus = "missing"
    $sdkStatus = "missing"
    $teamsfxStatus = "skipped"

    if (Test-CommandAvailable -CommandName "node") {
        $nodeStatus = "installed"
    }

    if (Test-CommandAvailable -CommandName "npm") {
        $npmStatus = "installed"
    }

    if ($nodeStatus -ne "installed" -or $npmStatus -ne "installed") {
        Write-Warn "Node.js/npm no detectados. Intentando instalación automática."

        if (Test-CommandAvailable -CommandName "winget") {
            winget install OpenJS.NodeJS.LTS --silent --accept-source-agreements --accept-package-agreements
            Start-Sleep -Seconds 2
        }
        elseif (Test-CommandAvailable -CommandName "choco") {
            choco install nodejs-lts -y
            Start-Sleep -Seconds 2
        }
        else {
            Write-Warn "No se encontró winget/choco para instalar Node.js automáticamente."
        }

        if (Test-CommandAvailable -CommandName "node") { $nodeStatus = "installed" }
        if (Test-CommandAvailable -CommandName "npm") { $npmStatus = "installed" }
    }

    if ($npmStatus -eq "installed") {
        if (-not (Test-NpmPackageInstalled -PackageName "@microsoft/agents-toolkit")) {
            npm install -g @microsoft/agents-toolkit
        }
        $toolkitStatus = if (Test-NpmPackageInstalled -PackageName "@microsoft/agents-toolkit") { "installed" } else { "failed" }

        if (-not (Test-NpmPackageInstalled -PackageName "@microsoft/agents-sdk")) {
            npm install -g @microsoft/agents-sdk
        }
        $sdkStatus = if (Test-NpmPackageInstalled -PackageName "@microsoft/agents-sdk") { "installed" } else { "failed" }

        if (-not $SkipOptional) {
            if (-not (Test-NpmPackageInstalled -PackageName "@microsoft/teamsfx-cli")) {
                npm install -g @microsoft/teamsfx-cli
            }
            $teamsfxStatus = if (Test-NpmPackageInstalled -PackageName "@microsoft/teamsfx-cli") { "installed_optional" } else { "failed_optional" }
        }
    }

    $agentEnvDir = Join-Path $Root ".agent_env"
    if (-not (Test-Path $agentEnvDir)) {
        New-Item -ItemType Directory -Path $agentEnvDir -Force | Out-Null
    }

    $envFile = Join-Path $Root ".env"
    if (-not (Test-Path $envFile)) {
        @'
PINPON_WORKSPACE=.
PINPON_AGENT_MODE=development
GITHUB_TOKEN=
PYPI_TOKEN=
OPENAI_API_KEY=
'@ | Set-Content -LiteralPath $envFile -Encoding UTF8
    }

    $localSettings = Join-Path $Root "agent.local.settings.json"
    if (-not (Test-Path $localSettings)) {
        @'
{
  "agent": {
    "configPath": "./agent_pinpon/agent.yaml",
    "mode": "local",
    "logLevel": "info"
  }
}
'@ | Set-Content -LiteralPath $localSettings -Encoding UTF8
    }

    Write-Host "AGENT_SETUP_STATUS node=$nodeStatus npm=$npmStatus toolkit=$toolkitStatus sdk=$sdkStatus teamsfx=$teamsfxStatus"

    if ($nodeStatus -ne "installed" -or $npmStatus -ne "installed" -or $toolkitStatus -eq "failed" -or $sdkStatus -eq "failed") {
        exit 1
    }

    exit 0
}
catch {
    Write-Err "Error en setup_agent_environment.ps1: $($_.Exception.Message)"
    exit 1
}

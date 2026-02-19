param(
    [Parameter(Mandatory = $true)][string]$ProjectPath,
    [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Info($Message) { Write-Host "[INFO] $Message" -ForegroundColor Cyan }
function Write-Warn($Message) { Write-Host "[WARN] $Message" -ForegroundColor Yellow }
function Write-Err($Message) { Write-Host "[ERR ] $Message" -ForegroundColor Red }

function Ensure-Dir {
    param([string]$Path)
    if (-not (Test-Path $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

function Write-TemplateFile {
    param(
        [string]$Path,
        [string]$Content,
        [switch]$Overwrite
    )

    if ((Test-Path $Path) -and (-not $Overwrite)) {
        return
    }

    $parent = Split-Path -Path $Path -Parent
    Ensure-Dir -Path $parent
    Set-Content -Path $Path -Value $Content -Encoding UTF8
}

$psTemplate = @'
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Info($Message) { Write-Host "[INFO] $Message" -ForegroundColor Cyan }
function Write-Warn($Message) { Write-Host "[WARN] $Message" -ForegroundColor Yellow }
function Write-Err($Message) { Write-Host "[ERR ] $Message" -ForegroundColor Red }

Write-Info "Script plantilla PINPON"
exit 0
'@

try {
    if ((Test-Path $ProjectPath) -and (-not $Force)) {
        Write-Err "La ruta ya existe. Usa -Force para sobreescribir archivos plantilla."
        exit 1
    }

    Ensure-Dir -Path $ProjectPath

    $dirs = @(
        ".github/workflows",
        "analysis",
        "config",
        "core",
        "docs",
        "downloads",
        "history",
        "ops",
        "pinpon_modules",
        "scripts",
        "tests",
        "ui",
        "utils",
        "validation"
    )

    foreach ($dir in $dirs) {
        Ensure-Dir -Path (Join-Path $ProjectPath $dir)
    }

    $credentialsJson = @'
{
  "efirma_cer_path": "",
  "efirma_key_path": "",
  "efirma_password": "",
  "gmail_address": "",
  "gmail_app_password": "",
  "sat_password": "",
  "sat_rfc": ""
}
'@

    $gmailJson = @'
{
  "gmail_address": "",
  "gmail_app_password": ""
}
'@

    Write-TemplateFile -Path (Join-Path $ProjectPath "config/pinpon_credentials.json") -Content $credentialsJson -Overwrite:$Force
    Write-TemplateFile -Path (Join-Path $ProjectPath "config/gmail_pinpon.json") -Content $gmailJson -Overwrite:$Force
    Write-TemplateFile -Path (Join-Path $ProjectPath "config/pinpon_smtp.json") -Content $gmailJson -Overwrite:$Force

    $templates = @{
        "README.md" = "# PINPON`n`nProyecto generado con pinpon_new_project.ps1`n"
        "requirements.txt" = "pytest`n"
        "color_utils.ps1" = $psTemplate
        "log_utils.ps1" = $psTemplate
        "file_utils.ps1" = $psTemplate
        "validate_all.ps1" = $psTemplate
        "validate_python.ps1" = $psTemplate
        "validate_gmail_api.ps1" = $psTemplate
        "validate_credentials.ps1" = $psTemplate
        "validate_smtp.ps1" = $psTemplate
        "validate_gmail_pinpon.ps1" = $psTemplate
        "validate_folders.ps1" = $psTemplate
        "validate_config.ps1" = $psTemplate
        "setup_pinpon.ps1" = $psTemplate
        "build_requirements.ps1" = $psTemplate
        "rebuild_venv.ps1" = $psTemplate
        "reset_pinpon.ps1" = $psTemplate
        "init_project_structure.ps1" = $psTemplate
        "check_venv.ps1" = $psTemplate
        "check_pip.ps1" = $psTemplate
        "check_python_version.ps1" = $psTemplate
        "show_json_keys.ps1" = $psTemplate
        "scripts/run_all_validators.ps1" = $psTemplate
        "scripts/run_tests.ps1" = $psTemplate
        "scripts/build.ps1" = $psTemplate
        "scripts/deploy.ps1" = $psTemplate
        "tests/test_validadores.py" = "def test_placeholder_validadores():`n    assert True`n"
        "tests/test_setup.py" = "def test_placeholder_setup():`n    assert True`n"
        "tests/test_ci_cd.py" = "def test_placeholder_ci_cd():`n    assert True`n"
        ".github/workflows/ci.yml" = "name: PINPON CI`non:`n  push:`n    branches: ['**']`n  pull_request:`n    branches: [main]`n"
        ".github/workflows/cd.yml" = "name: PINPON CD`non:`n  workflow_run:`n    workflows: ['PINPON CI']`n    types: [completed]`n"
        "docs/estructura.md" = "# Estructura`n"
        "docs/validadores.md" = "# Validadores`n"
        "docs/setup.md" = "# Setup`n"
        "docs/mantenimiento.md" = "# Mantenimiento`n"
        "docs/arquitectura.md" = "# Arquitectura`n"
        "docs/ci_cd.md" = "# CI/CD`n"
    }

    foreach ($relativePath in $templates.Keys) {
        Write-TemplateFile -Path (Join-Path $ProjectPath $relativePath) -Content $templates[$relativePath] -Overwrite:$Force
    }

    Write-Info "Proyecto PINPON generado en: $ProjectPath"
    exit 0
}
catch {
    Write-Err "Error en pinpon_new_project.ps1: $_"
    exit 1
}

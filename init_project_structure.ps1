param(
    [string]$Root = (Get-Location).Path
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "color_utils.ps1")
. (Join-Path $PSScriptRoot "file_utils.ps1")

try {
    $dirs = @(
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
        "validation",
        "dist"
    )

    foreach ($dir in $dirs) {
        Ensure-Directory -Path (Join-Path $Root $dir)
    }

    $credentialsTemplate = @{
        efirma_cer_path = ""
        efirma_key_path = ""
        efirma_password = ""
        gmail_address = ""
        gmail_app_password = ""
        sat_password = ""
        sat_rfc = ""
    }

    $gmailTemplate = @{
        gmail_address = ""
        gmail_app_password = ""
    }

    Ensure-JsonFile -Path (Join-Path $Root "config/pinpon_credentials.json") -Template $credentialsTemplate
    Ensure-JsonFile -Path (Join-Path $Root "config/gmail_pinpon.json") -Template $gmailTemplate
    Ensure-JsonFile -Path (Join-Path $Root "config/pinpon_smtp.json") -Template $gmailTemplate

    Write-Info "Estructura base inicializada"
    exit 0
}
catch {
    Write-Err "Error en init_project_structure.ps1: $_"
    exit 1
}

# scripts/setup_agent_environment.ps1
# Configura el entorno necesario para el agente declarativo PINPON:
#   - Detecta Node.js y npm (sin instalar automáticamente)
#   - Crea archivos base del agente si no existen
Write-Host "=== PINPON: Configuración del entorno del agente ===" -ForegroundColor Cyan

# ── 1. Detectar Node / npm ────────────────────────────────────────────────────
Write-Host "`n[1/4] Verificando Node.js y npm..." -ForegroundColor Yellow

$nodeVersion = $null
$npmVersion  = $null

Try { $nodeVersion = & node --version 2>$null } Catch {}
Try { $npmVersion  = & npm  --version 2>$null } Catch {}

if ($nodeVersion) {
    Write-Host "node detectado: $nodeVersion" -ForegroundColor Green
} else {
    Write-Host "node NO detectado." -ForegroundColor Red
}

if ($npmVersion) {
    Write-Host "npm detectado:  $npmVersion" -ForegroundColor Green
} else {
    Write-Host "npm NO detectado." -ForegroundColor Red
}

# ── 2. Diagnóstico de prerequisitos (sin instalación automática) ──────────────
Write-Host "`n[2/4] Validando prerequisitos (modo no-instalación)..." -ForegroundColor Yellow
if (-not $nodeVersion) {
    Write-Host "Node.js no está instalado. Instálalo manualmente desde https://nodejs.org o con tu gestor preferido." -ForegroundColor DarkYellow
} else {
    Write-Host "Node.js presente. No se requiere acción." -ForegroundColor DarkGray
}
if (-not $npmVersion) {
    Write-Host "npm no está disponible en PATH. Verifica instalación de Node.js y reinicia la terminal." -ForegroundColor DarkYellow
} else {
    Write-Host "npm presente. No se requiere acción." -ForegroundColor DarkGray
}

# ── 3. Crear archivos base del agente si no existen ──────────────────────────
Write-Host "`n[3/4] Verificando archivos base del agente..." -ForegroundColor Yellow

$repoRoot = Split-Path -Parent $PSScriptRoot

$agentFiles = @{
    "agent.yaml"                  = $repoRoot
    "agent.local.settings.json"   = $repoRoot
}

foreach ($file in $agentFiles.Keys) {
    $fullPath = Join-Path $agentFiles[$file] $file
    if (Test-Path $fullPath) {
        Write-Host "OK: $file ya existe." -ForegroundColor DarkGray
    } else {
        Write-Host "AVISO: $file no encontrado en $($agentFiles[$file]). Creando plantilla..." -ForegroundColor DarkYellow
        switch ($file) {
            "agent.yaml" {
                $template = @"
# agent.yaml — Configuración del agente declarativo PINPON
# Generado automáticamente por setup_agent_environment.ps1
name: pinpon-agent
description: Agente declarativo para análisis financiero y operativo PINPON
version: "1.0.0"
instructions: knowledge/instructions.md
knowledge:
  - knowledge/
actions:
  - actions/
"@
                Set-Content -Path $fullPath -Value $template -Encoding UTF8
            }
            "agent.local.settings.json" {
                $template = @"
{
  "agentName": "pinpon-agent",
  "environment": "local",
  "knowledgeDir": "knowledge",
  "actionsDir": "actions",
  "logLevel": "info"
}
"@
                Set-Content -Path $fullPath -Value $template -Encoding UTF8
            }
        }
        Write-Host "Plantilla creada: $fullPath" -ForegroundColor Green
    }
}

$knowledgeDir = Join-Path $repoRoot "knowledge"
if (-not (Test-Path $knowledgeDir)) {
    New-Item -ItemType Directory -Path $knowledgeDir | Out-Null
    Write-Host "Directorio knowledge/ creado." -ForegroundColor Green
} else {
    Write-Host "OK: knowledge/ ya existe." -ForegroundColor DarkGray
}

$actionsDir = Join-Path $repoRoot "actions"
if (-not (Test-Path $actionsDir)) {
    New-Item -ItemType Directory -Path $actionsDir | Out-Null
    Write-Host "Directorio actions/ creado." -ForegroundColor Green
} else {
    Write-Host "OK: actions/ ya existe." -ForegroundColor DarkGray
}

$instructionsPath = Join-Path $knowledgeDir "instructions.md"
if (-not (Test-Path $instructionsPath)) {
    @"
# Instrucciones del agente PINPON

Mantén respuestas en español, concisas y orientadas a validación documental.
"@ | Set-Content -Path $instructionsPath -Encoding UTF8
    Write-Host "Archivo knowledge/instructions.md creado." -ForegroundColor Green
} else {
    Write-Host "OK: knowledge/instructions.md ya existe." -ForegroundColor DarkGray
}

$actionsReadme = Join-Path $actionsDir "README.md"
if (-not (Test-Path $actionsReadme)) {
    @"
# actions

Define aquí acciones del agente declarativo PINPON.
"@ | Set-Content -Path $actionsReadme -Encoding UTF8
    Write-Host "Archivo actions/README.md creado." -ForegroundColor Green
} else {
    Write-Host "OK: actions/README.md ya existe." -ForegroundColor DarkGray
}

# ── 4. Resumen ────────────────────────────────────────────────────────────────
Write-Host "`n[4/4] Resumen del entorno:" -ForegroundColor Cyan
Write-Host "  node  : $(if ($nodeVersion) { $nodeVersion } else { 'NO DETECTADO' })"
Write-Host "  npm   : $(if ($npmVersion)  { $npmVersion  } else { 'NO DETECTADO' })"
Write-Host "  agent.yaml              : $(if (Test-Path (Join-Path $repoRoot 'agent.yaml'))                { 'OK' } else { 'FALTA' })"
Write-Host "  agent.local.settings    : $(if (Test-Path (Join-Path $repoRoot 'agent.local.settings.json')) { 'OK' } else { 'FALTA' })"
Write-Host "  knowledge/              : $(if (Test-Path (Join-Path $repoRoot 'knowledge'))                  { 'OK' } else { 'FALTA' })"
Write-Host "  actions/                : $(if (Test-Path (Join-Path $repoRoot 'actions'))                    { 'OK' } else { 'FALTA' })"

Write-Host "`n=== PINPON: Configuración del entorno completada ===" -ForegroundColor Cyan

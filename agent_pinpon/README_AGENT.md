# AGENTE PINPON (Microsoft 365 Copilot)

Este directorio contiene la declaración base de un **Declarative Agent** para Microsoft 365 Copilot integrado al ecosistema Pinpon.

## Estructura

- `agent.yaml`: definición principal del agente (instrucciones, capacidades, acciones, seguridad, contexto).
- `actions.yaml`: catálogo de acciones declarativas y contratos de entrada/salida.
- `knowledge.yaml`: fuentes de conocimiento e indexación.
- `environment.json`: variables base de entorno.

## Ejecución local

1. Ejecutar setup del entorno:
   - `pwsh ./scripts/setup_agent_environment.ps1 -Root .`
2. Inicializar/validar agente:
   - Validación: `pwsh ./scripts/init_agent.ps1 -Root . -ValidationOnly`
   - Ejecución: `pwsh ./scripts/init_agent.ps1 -Root .`

## Extender acciones

1. Agrega una nueva entrada en `actions.yaml` bajo `actions`.
2. Define `name`, `method`, `entrypoint`, `inputs`, `outputs`, `validations`, `errors`.
3. Registra el nombre en `agent.yaml > agent.actions.available`.

## Extender conocimiento

1. Agrega una nueva fuente en `knowledge.yaml > knowledge.sources`.
2. Define `id`, `type`, `path`, `indexed`, `priority`.
3. Si es externa, agrégala en `knowledge.external_connections` y configura el `auth_env`.

## Integración con Pinpon

- Marketplace: acción `analyze_marketplace` y pruebas en `tests/test_marketplace.py`.
- Loader dinámico: apoyado por `scripts/ci_local.ps1` y checks en CI.
- Módulos ERP: contexto inicial en `agent.yaml > agent.context.erp_modules`.

## Integración con CI/CD

- Workflow CI incluye `agent-validation` (no bloqueante) para validar:
  - archivos declarativos del agente,
  - pruebas `tests/test_agent_config.py`,
  - inicialización en modo validación.

## Debug

- Revisar salida de `scripts/init_agent.ps1`.
- Revisar variables en `.env` y `agent.local.settings.json`.
- Confirmar instalación de Node/npm y toolkit con `scripts/setup_agent_environment.ps1`.

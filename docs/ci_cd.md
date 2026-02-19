# CI/CD de PINPON

## CI (`.github/workflows/ci.yml`)

Triggers:

- `push` a cualquier rama.
- `pull_request` a `main`.

Jobs:

1. `build`: instala dependencias, inicializa estructura y genera artefacto.
2. `validate`: ejecuta `validate_all.ps1`.
3. `test`: ejecuta `scripts/run_tests.ps1`.
4. `security`: ejecuta auditoría básica de dependencias (`pip-audit`).

## CD (`.github/workflows/cd.yml`)

Trigger:

- `workflow_run` de `PINPON CI` exitoso para `main`.

Jobs:

1. Checkout del commit validado.
2. Build de release.
3. Upload de artefacto.
4. Deploy placeholder con `scripts/deploy.ps1`.
5. Rollback básico (`scripts/deploy.ps1 -Rollback`) si hay fallo.

## Convenciones

- Fallo en cualquier validador o test detiene el pipeline.
- Logs y artefactos se publican para diagnóstico.
- `main` solo debe recibir cambios con CI exitoso.

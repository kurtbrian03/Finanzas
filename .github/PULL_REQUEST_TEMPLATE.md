<!-- pinpon:auto-keep enabled -->
<!-- pinpon:checklist-version v1 -->

## Contexto

Describe brevemente el contexto de negocio/técnico de este cambio en Pinpon.

## Descripción

¿Qué se cambió y por qué?

## Impacto

- Componentes impactados:
- Riesgo estimado (Bajo/Medio/Alto):
- Compatibilidad retroactiva:

## Validaciones

Indica cómo validaste localmente/CI este PR.

## Checklist automático

### A) Validaciones generales
- [ ] Código formateado correctamente
- [ ] No se introducen rutas rotas
- [ ] No se rompen imports
- [ ] No se rompen módulos ERP existentes
- [ ] No se rompen scripts en /scripts
- [ ] No se rompen workflows existentes

### B) Validaciones CI/CD
- [ ] GitHub Actions pasa en Windows
- [ ] GitHub Actions pasa en Linux
- [ ] Azure Pipelines pasa
- [ ] GitLab CI pasa
- [ ] Runner local (ci_local.ps1) pasa
- [ ] pytest --import-mode=importlib pasa

### C) Validaciones Marketplace ERP
- [ ] registry.json válido
- [ ] installer.py detecta modos none/local/pip/submodule
- [ ] ui.py carga sin errores
- [ ] No se duplican módulos
- [ ] No se rompen módulos instalados

### D) Validaciones Loader Dinámico
- [ ] Detecta módulos locales
- [ ] Detecta módulos pip
- [ ] Detecta submódulos Git
- [ ] No rompe si un módulo no existe
- [ ] No rompe si marketplace está vacío

### E) Validaciones Submódulos Git
- [ ] .gitmodules válido
- [ ] git submodule status limpio
- [ ] convert_compras_to_submodule.ps1 funciona
- [ ] sync_submodules.yml no falla

### F) Validaciones Publicación Pip
- [ ] pyproject.toml válido
- [ ] setup.cfg válido
- [ ] build local funciona
- [ ] publish_pip_compras.ps1 idempotente
- [ ] No falla si versión ya existe

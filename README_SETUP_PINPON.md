# Setup PINPON (Windows PowerShell)

Objetivo: reconstruir entorno y validar configuraciones sin tocar datos sensibles.

## Scripts
- build_requirements.ps1: respalda requirements.txt y genera uno nuevo con pip freeze.
- rebuild_venv.ps1: elimina .venv con confirmacion, crea uno nuevo, instala requirements, valida python/pip.
- validate_python.ps1: comprueba python/pip y ejecuta prueba "PINPON OK".
- validate_gmail_api.ps1: verifica existencia y estructura JSON de config/gmail_pinpon.json, pinpon_credentials.json, pinpon_smtp.json.
- validate_credentials.ps1: valida campos requeridos client_id, client_secret, refresh_token, email sin mostrar valores.
- ops/pinpon.profile.ps1: perfil que activa .venv, define rutas y funciones pinpon-activate, pinpon-status, pinpon-paths.
- setup_pinpon.ps1: orquesta todo en orden con confirmacion y resumen.

## Orden recomendado
1) .\setup_pinpon.ps1  (responde "y" cuando confirme)
   - Internamente llama build_requirements, rebuild_venv, validate_python, validate_gmail_api, validate_credentials.
2) Cargar perfil: `.\ops\pinpon.profile.ps1` o agrega a tu `$PROFILE`.

## Uso individual
- Regenerar requirements: `.\build_requirements.ps1`
- Rehacer venv: `.\rebuild_venv.ps1 --yes` (evita preguntar al borrar .venv)
- Validar python: `.\validate_python.ps1`
- Validar Gmail API: `.\validate_gmail_api.ps1`
- Validar credenciales: `.\validate_credentials.ps1`

## Que no toca (seguro)
- config/, datos/, ops/, Obsidian/, vault/, .git/, .venv existente solo se elimina si confirmas en rebuild_venv.

## Restauracion si algo falla
- Usa los respaldos de requirements_backup_*.txt o tu control de versiones git.
- Si el nuevo .venv falla, borra y recrea con rebuild_venv.ps1.
- Si un script marca error, revisa el log correspondiente *.log en la raiz.

## Logs
- build_requirements.log
- rebuild_venv.log
- validate_python.log
- validate_gmail_api.log
- validate_credentials.log
- setup_pinpon.log
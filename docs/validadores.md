# Validadores PINPON

## Objetivo

Garantizar integridad mínima de entorno, credenciales, Gmail/SMTP y estructura del proyecto antes de ejecutar pruebas o despliegues.

## Scripts

- `validate_python.ps1`: valida versión de Python y `pip`.
- `validate_gmail_api.ps1`: valida `config/gmail_pinpon.json`.
- `validate_credentials.ps1`: valida `config/pinpon_credentials.json`.
- `validate_smtp.ps1`: valida `config/pinpon_smtp.json`.
- `validate_gmail_pinpon.ps1`: valida configuración Gmail PINPON.
- `validate_folders.ps1`: valida estructura de carpetas obligatoria.
- `validate_config.ps1`: valida claves de configuración críticas.
- `validate_all.ps1`: ejecuta todos los validadores.

## Claves requeridas

- `efirma_cer_path`
- `efirma_key_path`
- `efirma_password`
- `gmail_address`
- `gmail_app_password`
- `sat_password`
- `sat_rfc`

## Ejecución

- Validación global: `pwsh ./validate_all.ps1`
- Validación individual: `pwsh ./validate_credentials.ps1`

## Códigos de salida

- `exit 0`: validación exitosa.
- `exit 1`: error de validación.

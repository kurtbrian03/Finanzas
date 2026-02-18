# Finanzas

## Integración de submódulo PINPON

Este repositorio integra `PINPON` como submódulo Git en la ruta `./pinpon` (sin copiar scripts ni modificar el contenido interno de PINPON).

### Flujo en PowerShell (VS Code)

```powershell
# 1) Verificar que estás en Finanzas
Get-Location
git remote -v

# 2) (Solo maintainers) Agregar PINPON como submódulo (una sola vez)
git submodule add https://github.com/kurtbrian03/PINPON.git pinpon

# 3) Inicializar y actualizar submódulos (uso normal en dev/CI)
git submodule update --init --recursive

# 4) Confirmar configuración
git config --file .gitmodules --get-regexp submodule
```

### Uso desde Finanzas (desarrollo/CI)

- Clonado inicial de Finanzas con submódulos:

```powershell
git clone --recurse-submodules <URL_DE_FINANZAS>
```

- Si ya clonaste Finanzas sin submódulos:

```powershell
git submodule update --init --recursive
```

- Ejecutar scripts de PINPON desde Finanzas:

```powershell
pwsh ./pinpon/<script>.ps1
```

> Nota: no se incluyen ni exponen credenciales reales en este repositorio.

## App Streamlit: lector de CSV y Excel

### Instalación

```powershell
pip install -r requirements.txt
```

### Ejecución

```powershell
streamlit run streamlit_app.py
```

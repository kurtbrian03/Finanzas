# Deduplicador de Entornos Virtuales Python

Scripts para detectar y consolidar entornos virtuales (venv) duplicados de forma segura.

## Propósito

Encuentra venvs duplicados en un proyecto, compara sus dependencias y consolida todo en un único venv, creando backups de seguridad.

## Archivos

- `dedupe_venvs.ps1` - Script para Windows (PowerShell)
- `dedupe_venvs.sh` - Script para Linux/macOS (Bash)
- `DEDUPE_VENVS_README.md` - Esta documentación

## Requisitos

- Python 3.x instalado
- PowerShell 5.0+ (Windows) o Bash 4.0+ (Linux/macOS)
- Permisos de escritura en el directorio del proyecto
- Espacio en disco para backups (temporalmente duplica tamaño de venvs)

## Uso Básico

### Windows (PowerShell)

```powershell
# Ver qué haría (sin cambios)
.\dedupe_venvs.ps1 --dry-run

# Solo generar reporte
.\dedupe_venvs.ps1 --report-only

# Consolidar en .venv (con confirmación)
.\dedupe_venvs.ps1 --consolidate --target .venv

# Consolidar automático (sin confirmar)
.\dedupe_venvs.ps1 --consolidate --target .venv --yes
```

### Linux/macOS (Bash)

```bash
# Dar permisos de ejecución
chmod +x dedupe_venvs.sh

# Ver qué haría (sin cambios)
./dedupe_venvs.sh --dry-run

# Solo generar reporte
./dedupe_venvs.sh --report-only

# Consolidar en .venv (con confirmación)
./dedupe_venvs.sh --consolidate --target .venv

# Consolidar automático (sin confirmar)
./dedupe_venvs.sh --consolidate --target .venv --yes
```

## Modos de Operación

### `--dry-run` (por defecto)
No hace cambios. Solo analiza y genera reportes.

### `--report-only`
Genera solo el reporte sin hacer backups ni instalaciones.

### `--backup-only`
Crea backups de venvs duplicados sin instalar paquetes.

### `--consolidate`
Consolida todos los venvs en el objetivo:
1. Crea backups de venvs duplicados
2. Instala paquetes faltantes en el venv objetivo
3. Deja backups para restauración

### `--auto`
Consolidación automática. Requiere `--yes`.

### `--target <nombre>`
Especifica qué venv usar como principal.
Si no se indica, usa heurística: `.venv` > más reciente.

### `--yes` o `-y`
No pedir confirmaciones (para automatización).

### `--force-delete`
Borra backups. **¡Usar con precaución!** Solo tras verificar.

## Archivos Generados

- `dedupe_report.txt` - Reporte legible con análisis
- `dedupe_actions.log` - Log detallado de operaciones
- `<venv>-packages.txt` - Lista de paquetes por cada venv
- `<venv>-backup-YYYYMMDD_HHMMSS` - Backups de venvs

## Checklist Antes de Ejecutar

**✓ HACER SIEMPRE:**
1. Commit o stash de cambios actuales
2. Verificar que no hay procesos usando los venvs
3. Ejecutar primero con `--dry-run`
4. Revisar `dedupe_report.txt`
5. Tener backup del proyecto completo

**✓ DESPUÉS DE CONSOLIDAR:**
1. Activar venv objetivo: `source .venv/bin/activate` (Linux) o `.venv\Scripts\activate` (Windows)
2. Probar que funciona: `python --version`, `pip list`
3. Ejecutar tests del proyecto
4. Esperar 24-48h antes de borrar backups

## Ejemplos de Uso Completo

### Escenario 1: Primera vez (exploración)

```bash
# 1. Ver qué hay
./dedupe_venvs.sh --dry-run

# 2. Revisar reporte
cat dedupe_report.txt

# 3. Si todo OK, consolidar
./dedupe_venvs.sh --consolidate --target .venv
```

### Escenario 2: Automatizado en CI

```bash
./dedupe_venvs.sh --report-only --log ci-venv-report.log
```

### Escenario 3: Limpiar backups antiguos

```bash
# Manual: buscar backups
ls -la | grep backup

# Borrar backups (CUIDADO)
# Solo tras verificar que el venv consolidado funciona
rm -rf .venv-backup-20260101_120000
```

## Riesgos y Precauciones

### ⚠️ RIESGOS

1. **Pérdida de configuraciones específicas**: Si un venv tenía configuraciones únicas en `pyvenv.cfg`, se pierden
2. **Incompatibilidad de versiones**: Si consolidas venvs con diferentes versiones de Python, puede fallar
3. **Dependencias conflictivas**: Versiones incompatibles pueden causar errores
4. **Espacio en disco**: Backups duplican temporalmente el tamaño

### ✅ PRECAUCIONES

1. **NUNCA** ejecutar con `--force-delete` sin verificar primero
2. **SIEMPRE** revisar `dedupe_report.txt` antes de consolidar
3. **NO** consolidar venvs con versiones diferentes de Python
4. **HACER** commit antes de ejecutar
5. **ESPERAR** 24-48h antes de borrar backups
6. **PROBAR** el venv consolidado exhaustivamente

## Restaurar un Backup

Si algo sale mal:

```bash
# Linux/macOS
mv .venv .venv-failed
mv .venv-backup-20260217_120000 .venv

# Windows
Rename-Item .venv .venv-failed
Rename-Item .venv-backup-20260217_120000 .venv
```

## Detección de Problemas

El script detecta y advierte sobre:

- Venvs sin ejecutable Python
- Versiones diferentes de Python entre venvs
- `include-system-site-packages = true` en config
- Entornos Conda (no consolida automáticamente)
- Permisos insuficientes
- Espacio en disco insuficiente

## Comandos Git Útiles

Antes de ejecutar:

```bash
# Ver estado
git status

# Guardar cambios temporalmente
git stash

# Crear commit de seguridad
git add .
git commit -m "Antes de consolidar venvs"
```

Después si todo OK:

```bash
# Añadir .gitignore para backups
echo "*-backup-*" >> .gitignore
git add .gitignore
git commit -m "Ignorar backups de venvs"
```

## Solución de Problemas

### Error: "No se encontró Python"
**Causa**: El directorio no es un venv válido.
**Solución**: Verificar que la carpeta tenga `bin/python` o `Scripts/python.exe`.

### Error: "Permission denied"
**Causa**: Falta permisos de ejecución.
**Solución**: `chmod +x dedupe_venvs.sh` (Linux/macOS).

### Error al instalar paquetes
**Causa**: Versiones incompatibles o índice pip no disponible.
**Solución**: Revisar `dedupe_actions.log`, instalar manualmente los paquetes problemáticos.

### Venvs no detectados
**Causa**: Nombres no estándar.
**Solución**: Modificar `VENV_PATTERNS` en el script.

## Limitaciones

- No consolida entornos Conda automáticamente
- No maneja venvs con `include-system-site-packages`
- No detecta dependencias de desarrollo vs producción
- No valida compatibilidad entre versiones de paquetes

## Recomendaciones Prioritarias

### 🔴 ALTA PRIORIDAD

1. **Backup manual del proyecto completo** antes de ejecutar
2. **Nunca usar `--force-delete`** sin probar el venv consolidado 24-48h
3. **Commit de cambios** antes de cualquier consolidación

### 🟡 MEDIA PRIORIDAD

1. Ejecutar `--dry-run` primero siempre
2. Revisar manualmente `dedupe_report.txt`
3. Probar venv consolidado con suite de tests completa

### 🟢 BAJA PRIORIDAD

1. Agregar backups a `.gitignore`
2. Documentar qué venvs se consolidaron
3. Limpiar archivos `*-packages.txt` tras consolidar

## Soporte

Para problemas:
1. Revisar `dedupe_actions.log`
2. Verificar que backups existen antes de reportar error
3. Restaurar desde backup si es necesario

---

**Versión**: 1.0  
**Última actualización**: 2026-02-17  
**Licencia**: MIT

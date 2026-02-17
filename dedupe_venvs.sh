#!/usr/bin/env bash
#
# dedupe_venvs.sh - Detecta y consolida entornos virtuales Python duplicados
#
# Uso:
#   ./dedupe_venvs.sh --dry-run
#   ./dedupe_venvs.sh --consolidate --target .venv --yes
#   ./dedupe_venvs.sh --auto --target .venv
#

set -euo pipefail

# Configuración
VENV_PATTERNS=(".venv*" "venv*" "env" "ENV" "virtualenv*")
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="dedupe_actions.log"
REPORT_FILE="dedupe_report.txt"
MODE="dry-run"
TARGET_VENV=""
FORCE_DELETE=false
YES=false
PRUNE_DAYS=7

# Funciones auxiliares
log() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] $*"
    echo "$msg"
    echo "$msg" >> "$LOG_FILE"
}

show_help() {
    cat <<EOF
Uso: $0 [OPCIONES]

Opciones:
  --dry-run         Modo por defecto, no hace cambios (solo reportes)
  --backup-only     Renombra duplicados a backups
  --consolidate     Consolida paquetes en venv objetivo
  --target <name>   Especifica venv objetivo (por defecto: .venv)
  --force-delete    Borra backups (requiere confirmación)
  --yes, -y         No pedir confirmaciones
  --test            Simula en directorio temporal
  --auto            Consolida automático (requiere --yes)
  --prune           Sugiere eliminar backups antiguos
  --report-only     Solo genera reporte
  --log <path>      Ruta del log (por defecto: dedupe_actions.log)
  --report <path>   Ruta del reporte (por defecto: dedupe_report.txt)
  --help            Muestra esta ayuda

Ejemplos:
  ./dedupe_venvs.sh --dry-run
  ./dedupe_venvs.sh --consolidate --target .venv --yes
  ./dedupe_venvs.sh --auto --target .venv

EOF
    exit 0
}

# Parsear argumentos
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            MODE="dry-run"
            shift
            ;;
        --backup-only)
            MODE="backup-only"
            shift
            ;;
        --consolidate)
            MODE="consolidate"
            shift
            ;;
        --target)
            TARGET_VENV="$2"
            shift 2
            ;;
        --force-delete)
            FORCE_DELETE=true
            shift
            ;;
        --yes|-y)
            YES=true
            shift
            ;;
        --test)
            MODE="test"
            shift
            ;;
        --auto)
            MODE="auto"
            shift
            ;;
        --prune)
            MODE="prune"
            shift
            ;;
        --report-only)
            MODE="report-only"
            shift
            ;;
        --log)
            LOG_FILE="$2"
            shift 2
            ;;
        --report)
            REPORT_FILE="$2"
            shift 2
            ;;
        --help|-h)
            show_help
            ;;
        *)
            echo "Opción desconocida: $1"
            show_help
            ;;
    esac
done

# Inicializar log
> "$LOG_FILE"

log "=== DEDUPLICADOR DE ENTORNOS VIRTUALES ==="
log "Modo: $MODE"

# Función para detectar venvs
find_venvs() {
    local venvs=()
    
    for pattern in "${VENV_PATTERNS[@]}"; do
        while IFS= read -r -d '' dir; do
            # Verificar si tiene ejecutable Python
            if [[ -f "$dir/bin/python" ]] || [[ -f "$dir/Scripts/python.exe" ]]; then
                venvs+=("$dir")
            fi
        done < <(find . -maxdepth 1 -type d -name "$pattern" -print0 2>/dev/null)
    done
    
    # Eliminar duplicados y ordenar
    printf '%s\n' "${venvs[@]}" | sort -u
}

# Función para obtener info de un venv
get_venv_info() {
    local venv_path="$1"
    local python_exe=""
    
    if [[ -f "$venv_path/bin/python" ]]; then
        python_exe="$venv_path/bin/python"
    elif [[ -f "$venv_path/Scripts/python.exe" ]]; then
        python_exe="$venv_path/Scripts/python.exe"
    else
        log "ADVERTENCIA: No se encontró Python en $venv_path"
        return 1
    fi
    
    # Versión Python
    local py_version
    py_version=$("$python_exe" --version 2>&1 || echo "Desconocido")
    
    # Paquetes
    local packages_file="${venv_path}-packages.txt"
    "$python_exe" -m pip freeze > "$packages_file" 2>/dev/null || true
    
    # Hash de paquetes
    local pkg_hash
    if [[ -f "$packages_file" ]]; then
        pkg_hash=$(md5sum "$packages_file" 2>/dev/null | cut -d' ' -f1 || echo "none")
    else
        pkg_hash="none"
    fi
    
    # Retornar info en formato parseable
    echo "$venv_path|$py_version|$pkg_hash|$packages_file"
}

# Función para seleccionar venv objetivo
select_target_venv() {
    local -a venvs=("$@")
    
    # Si hay --target especificado y existe
    if [[ -n "$TARGET_VENV" ]] && [[ -d "$TARGET_VENV" ]]; then
        echo "$TARGET_VENV"
        return
    fi
    
    # Heurística: .venv > más reciente
    for venv in "${venvs[@]}"; do
        if [[ "$venv" == "./.venv" ]] || [[ "$venv" == ".venv" ]]; then
            echo "$venv"
            return
        fi
    done
    
    # Más reciente
    local newest=""
    local newest_time=0
    for venv in "${venvs[@]}"; do
        local mtime
        mtime=$(stat -c %Y "$venv" 2>/dev/null || stat -f %m "$venv" 2>/dev/null || echo 0)
        if [[ $mtime -gt $newest_time ]]; then
            newest_time=$mtime
            newest="$venv"
        fi
    done
    
    echo "$newest"
}

# Función para crear backup
backup_venv() {
    local venv_path="$1"
    local backup_name="${venv_path}-backup-${TIMESTAMP}"
    
    log "Creando backup: $backup_name"
    
    if [[ "$MODE" != "dry-run" ]] && [[ "$MODE" != "report-only" ]]; then
        mv "$venv_path" "$backup_name"
    fi
    
    echo "$backup_name"
}

# Función para instalar paquetes faltantes
install_missing_packages() {
    local target_venv="$1"
    shift
    local -a packages=("$@")
    
    local python_exe
    if [[ -f "$target_venv/bin/python" ]]; then
        python_exe="$target_venv/bin/python"
    else
        python_exe="$target_venv/Scripts/python.exe"
    fi
    
    for pkg in "${packages[@]}"; do
        log "Instalando: $pkg"
        if [[ "$MODE" != "dry-run" ]] && [[ "$MODE" != "report-only" ]]; then
            "$python_exe" -m pip install "$pkg" >> "$LOG_FILE" 2>&1 || {
                log "ERROR instalando $pkg"
            }
        fi
    done
}

# Generar reporte
generate_report() {
    local -a venv_infos=("$@")
    
    {
        echo "========================================"
        echo "REPORTE DE ENTORNOS VIRTUALES DUPLICADOS"
        echo "Generado: $(date)"
        echo "========================================"
        echo ""
        echo "ENTORNOS DETECTADOS: ${#venv_infos[@]}"
        echo ""
        
        for info in "${venv_infos[@]}"; do
            IFS='|' read -r path version hash packages_file <<< "$info"
            local pkg_count=0
            [[ -f "$packages_file" ]] && pkg_count=$(wc -l < "$packages_file")
            
            echo "--- $path ---"
            echo "Python: $version"
            echo "Paquetes: $pkg_count"
            echo "Hash: $hash"
            echo ""
        done
        
        echo "OBJETIVO SELECCIONADO: $TARGET_VENV"
        echo ""
        echo "RECOMENDACIONES:"
        echo "1. Revisar este reporte antes de consolidar"
        echo "2. Hacer commit de cambios actuales"
        echo "3. Ejecutar con --consolidate solo tras verificar"
        echo "4. Esperar 24h antes de usar --force-delete"
        echo ""
        echo "========================================"
    } > "$REPORT_FILE"
    
    log "Reporte generado: $REPORT_FILE"
}

# Flujo principal
echo ""
echo "=== DEDUPLICADOR DE ENTORNOS VIRTUALES ==="
echo ""

# Confirmación si no es dry-run
if [[ "$MODE" != "dry-run" ]] && [[ "$MODE" != "report-only" ]] && [[ "$YES" != true ]]; then
    echo -n "¡ADVERTENCIA! Modo activo. ¿Continuar? (S/N): "
    read -r confirm
    if [[ "$confirm" != "S" ]] && [[ "$confirm" != "s" ]]; then
        echo "Cancelado por el usuario."
        exit 0
    fi
fi

log "Iniciando análisis..."

# Detectar venvs
mapfile -t venv_paths < <(find_venvs)

if [[ ${#venv_paths[@]} -eq 0 ]]; then
    echo "No se encontraron entornos virtuales."
    exit 0
fi

log "Entornos encontrados: ${#venv_paths[@]}"

# Recopilar info
declare -a venv_infos=()
for venv in "${venv_paths[@]}"; do
    log "Analizando: $venv"
    info=$(get_venv_info "$venv")
    if [[ -n "$info" ]]; then
        venv_infos+=("$info")
    fi
done

# Seleccionar objetivo
target_venv=$(select_target_venv "${venv_paths[@]}")
TARGET_VENV="$target_venv"
log "Venv objetivo: $target_venv"

# Generar reporte
generate_report "${venv_infos[@]}"

if [[ "$MODE" == "report-only" ]]; then
    echo ""
    echo "Modo --report-only: Solo se generó el reporte."
    exit 0
fi

# Consolidar si se solicita
if [[ "$MODE" == "consolidate" ]] || [[ "$MODE" == "auto" ]]; then
    echo ""
    echo "Consolidando venvs en $target_venv"
    
    for venv in "${venv_paths[@]}"; do
        if [[ "$venv" == "$target_venv" ]]; then
            continue
        fi
        
        # Crear backup
        backup=$(backup_venv "$venv")
        
        # Calcular paquetes faltantes
        venv_packages="${venv}-packages.txt"
        target_packages="${target_venv}-packages.txt"
        
        if [[ -f "$venv_packages" ]] && [[ -f "$target_packages" ]]; then
            mapfile -t missing < <(comm -23 <(sort "$venv_packages") <(sort "$target_packages"))
            
            if [[ ${#missing[@]} -gt 0 ]]; then
                log "Instalando ${#missing[@]} paquetes faltantes"
                install_missing_packages "$target_venv" "${missing[@]}"
            fi
        fi
    done
fi

# Resumen final
echo ""
echo "=== RESUMEN ==="
echo "Venv objetivo: $target_venv"
echo "Reporte: $REPORT_FILE"
echo "Log: $LOG_FILE"
echo ""
echo "RECOMENDACIONES:"
echo "1. Revisar $REPORT_FILE antes de borrar backups"
echo "2. Probar que el venv objetivo funciona correctamente"
echo "3. Esperar 24h y luego usar --force-delete si todo OK"
echo ""
echo "✓ Proceso completado."

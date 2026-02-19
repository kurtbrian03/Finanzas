# Gitignore Guidelines — Finanzas

## 1) Introducción

El archivo `.gitignore` es un componente arquitectónico crítico del proyecto Finanzas. No es un detalle operativo menor: define qué pertenece al historial del producto y qué debe permanecer fuera del control de versiones por seguridad, trazabilidad y disciplina técnica.

Su función impacta directamente en:

- **Salud del repositorio:** evita crecimiento descontrolado por artefactos temporales.
- **Auditabilidad:** conserva un historial limpio y enfocado en cambios funcionales reales.
- **Mantenibilidad:** reduce ruido en revisiones, diffs y pull requests.
- **Prevención de incidentes:** evita commits masivos accidentales y exposición de información sensible.

---

## 2) Principios del `.gitignore` Vivo y Evolutivo

El `.gitignore` **no es estático**. Debe evolucionar junto con la arquitectura, las herramientas y los flujos operativos del proyecto.

Principios de gobierno:

1. **Evolución continua:** cada nueva herramienta, dependencia o pipeline debe evaluar su impacto en artefactos locales.
2. **Trazabilidad de intención:** cada bloque del `.gitignore` debe incluir comentario explicativo y motivo técnico.
3. **Cobertura preventiva:** se prioriza prevenir contaminación del repositorio antes de que ocurra.
4. **Consistencia organizacional:** mantener estructura por secciones para facilitar auditoría y mantenimiento.

Regla práctica oficial:

> **Si una herramienta genera artefactos locales, debe tener su propio bloque en el `.gitignore` con comentario y motivo.**

---

## 3) Grupos de Cobertura Obligatoria

### 3.1 Entornos virtuales
Incluye exclusión de `.venv/`, `venv/`, `env/`, `ENV/` y variantes de entorno local.

**Objetivo:** evitar versionar dependencias binarias, rutas locales y metadatos específicos de máquina.

### 3.2 Cachés de Python
Incluye `__pycache__/`, `*.py[cod]`, `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`, entre otros.

**Objetivo:** excluir artefactos de ejecución, pruebas y análisis estático que no representan código fuente.

### 3.3 Artefactos de Streamlit
Incluye `.streamlit/`.

**Objetivo:** evitar subir secretos, configuraciones locales y ajustes de entorno no portables.

### 3.4 Configuración local de VS Code
Incluye `.vscode/` (con opción de excepción controlada para recomendaciones).

**Objetivo:** evitar acoplar configuraciones personales del editor al repositorio compartido.

### 3.5 Logs, temporales, backups y locks
Incluye `*.log`, `*.tmp`, `*.bak`, `*.orig`, `*.lock`, `logs/`, etc.

**Objetivo:** eliminar ruido operativo y archivos transitorios sin valor versionable.

### 3.6 Archivos sensibles
Incluye `.env`, `.env.*`, claves y certificados (`*.pem`, `*.key`, `*.p12`, `*.pfx`, `*.crt`).

**Objetivo:** proteger secretos y credenciales para cumplir seguridad y buenas prácticas de compliance.

### 3.7 Conflictos y sincronización de OneDrive
Incluye patrones de conflicto/sincronización (`*conflict*`, `*sync-conflict*`, `*.odopen`, etc.).

**Objetivo:** impedir que estados de sincronización de OneDrive contaminen el historial del código.

### 3.8 Basura de sistema Windows/macOS/Linux
Incluye `Thumbs.db`, `Desktop.ini`, `.DS_Store`, `.Trash-*`, `.nfs*`, etc.

**Objetivo:** excluir metadatos del sistema operativo ajenos al dominio funcional del proyecto.

### 3.9 Datos locales
Incluye `data/`, `datasets/`, `temp/`, `tmp/`, `cache/`.

**Objetivo:** evitar versionar datos transitorios, experimentales o de ejecución local.

### 3.10 Reportes generados
Incluye carpetas de salida (`docs/reportes/`, `reports/`, `outputs/`) y patrones de exporte (`.csv`, `.xlsx`, `.pdf`, `.zip`) en rutas de generación.

**Objetivo:** prevenir commits masivos de artefactos generados automáticamente.

### 3.11 Imágenes oficiales del proyecto
Se define la regla operativa de ubicar imágenes oficiales en `/assets`.

**Objetivo:** separar recursos institucionales versionables de imágenes temporales de pruebas o depuración.

---

## 4) Mejoras de Robustez Aplicadas

Se agregaron patrones para escenarios frecuentes en el entorno real de Finanzas:

- `.vscode-test/`
- `.history/`
- `ehthumbs.db`
- `.Spotlight-V100/`

Justificación técnica:

- **`.vscode-test/`**: evita artefactos de pruebas/extensiones de VS Code.
- **`.history/`**: evita historiales locales automáticos de editores/extensiones.
- **`ehthumbs.db`**: complementa exclusión de cachés visuales de Windows.
- **`.Spotlight-V100/`**: cubre metadatos de indexación de macOS cuando existen intercambios cross-platform.

---

## 5) Checklist Oficial para Revisar `.gitignore` en Cada Pull Request

Antes de aprobar o fusionar cambios, validar:

- [ ] ¿Se añadieron nuevas herramientas o dependencias?
- [ ] ¿Aparecieron carpetas nuevas en `git status` que no deberían versionarse?
- [ ] ¿Se están generando artefactos temporales adicionales?
- [ ] ¿Existen configuraciones locales nuevas de IDE/editor?
- [ ] ¿Hay nuevos archivos de sincronización/conflicto (OneDrive u otros)?
- [ ] ¿El entorno virtual permanece fuera del repositorio?
- [ ] ¿Las imágenes oficiales están en `/assets` y no en rutas temporales?
- [ ] ¿El `.gitignore` mantiene estructura por secciones y comentarios?
- [ ] ¿Es necesario agregar un bloque nuevo con justificación explícita?

---

## 6) Buenas Prácticas para Mantener el Repositorio Limpio

1. **Evitar commits masivos accidentales**
   - Revisar siempre `git status` y `git diff --staged` antes de hacer commit.
   - En cambios estructurales, preferir commits pequeños y temáticos.

2. **Cuándo usar `git rm --cached`**
   - Cuando archivos no versionables ya fueron trackeados por error.
   - Comando recomendado para limpieza controlada:
     - `git rm -r --cached .`
     - `git add .`
     - `git status` (validación final)

3. **Validar que `.gitignore` funciona**
   - Verificar que artefactos locales no aparezcan en `git status`.
   - Usar `git check-ignore -v <ruta>` para confirmar qué regla los excluye.
   - En PRs, auditar que solo exista código, documentación y activos oficiales.

---

## 7) Conclusión

Este documento forma parte oficial del estándar operativo del proyecto Finanzas. Su cumplimiento garantiza repositorios limpios, revisiones eficientes y una postura profesional frente a auditoría, seguridad y mantenimiento.

La política es explícita: **`.gitignore` y esta guía deben mantenerse actualizados de forma continua** cada vez que evoluciona el ecosistema técnico del proyecto.

---

## Enlace de ejecución local de la aplicación

Este enlace permite validar operativamente que la aplicación se ejecuta correctamente después de aplicar cambios al `.gitignore` o a cualquier otro componente del proyecto.

Enlace local actual:

http://localhost:8501

Nota: este enlace puede cambiar si se modifica el puerto o la configuración del servidor Streamlit en el entorno de ejecución.

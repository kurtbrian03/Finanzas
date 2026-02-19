# 💙 README Empresarial — Workflow Integral Dropbox IA

> Documento corporativo del ecosistema de facturación inteligente sobre Dropbox, con auditoría técnica, trazabilidad y gobierno operativo.

---

## 1) Arquitectura del ecosistema Dropbox IA

El ecosistema está diseñado en capas para separar **captura**, **inteligencia documental**, **auditoría**, **visualización** y **gobierno CI/CD**.

### Capas

- **Ingesta y estructura**
  - Lectura recursiva de FACTURACION.
  - Validación/creación de estructura estándar de carpetas.
  - Renombrado y normalización de activos JPG.
- **Extracción y clasificación**
  - OCR/texto base de PDFs, TXT, DOCX.
  - Extracción avanzada CFDI (XML incrustado + fallback regex).
  - Clasificación de proveedor emisor (Aspel, Facturama, Facture, Contpaqi, Otros).
- **Motor de búsqueda + auditoría**
  - Ranking híbrido (exacto, fuzzy, semántico, tokens, temporal, estructural, boosting).
  - Auditoría por corrida y comparativa histórica snapshot vs snapshot.
  - Profiling por componente de motor (performance_metrics).
- **Validación fiscal**
  - Validación CFDI SAT (modo mock/http configurable por entorno).
- **Visualización ejecutiva (Streamlit)**
  - Panel histórico de auditoría.
  - Menú inteligente de facturas Aspel.
  - Dashboard de facturas por receptor.
- **Gobierno y CI/CD**
  - Pipeline automático de auditoría + profiling.
  - Política de degradación con exit code 0/1 para gates de calidad.

---

## 2) Flujo completo del pipeline

1. **Extracción**
   - `leer_dropbox_recursivo` indexa archivos y metadatos.
2. **Auditoría de búsqueda**
   - `SearchEngine` ejecuta consultas canónicas y exporta auditoría.
3. **Profiling**
   - `profiling=True` activa métricas de tiempo por componente.
4. **Validación SAT**
   - CFDI seleccionado se valida con API SAT (mock/http).
5. **Extracción XML CFDI**
   - Se intenta extraer CFDI incrustado en PDF (XMP/streams/nodos XML).
6. **Menú Aspel**
   - Facturas detectadas con autofill de UUID/RFC/Total.
7. **Renombrado JPG**
   - Normaliza naming por carpeta (`<carpeta>_nnn.jpg` / `Pendiente_nnn.jpg`).
8. **Clasificación por receptor**
   - Agrupa métricas para dashboard y artefactos por receptor.
9. **CI/CD GitHub Actions**
   - Compara snapshots, evalúa degradación y aprueba/falla pipeline.

---

## 3) Propósito de cada módulo crítico

| Módulo | Propósito empresarial | Salida principal |
|---|---|---|
| `dropbox_integration/search_engine.py` | Ranking inteligente y trazabilidad de búsqueda | resultados + auditoría + performance |
| `dropbox_integration/audit_diff.py` | Comparar versiones de relevancia entre snapshots | diff JSON/CSV/TXT |
| `analysis/cfdi_xml_extractor.py` | Extraer metadatos fiscales confiables desde XML incrustado | UUID, RFCs, total, fecha, timbre |
| `validation/cfdi_sat_api.py` | Verificar estatus CFDI en SAT | vigente/cancelado/no_encontrado |
| `dropbox_integration/aspel_invoice_menu.py` | Detectar y preparar menú inteligente de facturas | tabla de facturas con autofill |
| `dropbox_integration/image_renamer.py` | Estandarizar activos JPG para operación | renames auditables |
| `dropbox_integration/audit_ci.py` | Gate de calidad para CI/CD | exit code 0/1 |
| `dropbox_integration/invoice_provider_classifier.py` | Clasificar emisor/plataforma de factura | proveedor_detectado |

---

## 4) Estructura exacta de carpetas Dropbox

```text
FACTURACION/
│
├── ASPel/                      # Facturas Aspel (PDF/XML)
│   ├── 2024/
│   ├── 2025/
│   └── ...
│
├── Facturama/                  # Facturas Facturama
├── Facture/                    # Facturas Facture
├── Contpaqi/                   # Facturas Contpaqi
│
├── Imagenes/                   # Imágenes JPG por carpeta
│   ├── Cadera/
│   ├── Rodilla/
│   ├── Hallux valgus/
│   └── Pendiente/
│
├── HojaConsumo/                # Hojas de consumo sin nombre
└── Otros/                      # Archivos no clasificados
```

### Reglas de estructura

- Si carpeta de imágenes no representa persona válida → mover a `Imagenes/Pendiente/`.
- Facturas detectadas por proveedor pueden consolidarse en su carpeta correspondiente.
- El pipeline crea carpetas faltantes automáticamente.

---

## 5) ¿Cómo se generan snapshots?

En ejecución con auditoría:

- Se generan snapshots en `docs/versions/latest/dropbox/analytics/`:
  - `dropbox_search_audit_snapshot.json`
  - `dropbox_search_audit_snapshot.csv`
  - `dropbox_search_performance_snapshot.json` (si profiling)
  - `dropbox_search_performance_snapshot.csv` (si profiling)

El snapshot conserva contexto, scores y métricas de performance para comparabilidad temporal.

---

## 6) ¿Cómo se comparan versiones?

Se usa `compare_auditoria_snapshots` o CLI `audit_ci.py`:

- Input: snapshot A (anterior), snapshot B (actual).
- Output:
  - metadata de cobertura,
  - resumen de ranking (up/down/same),
  - delta de score final y por componente,
  - documentos comunes/nuevos/removidos,
  - top de cambios de ranking.

Ejemplo manual:

```powershell
& "./.venv/Scripts/python.exe" -m dropbox_integration.audit_ci `
  --snapshot-a "docs/versions/latest/dropbox/analytics/dropbox_search_audit_snapshot_prev.json" `
  --snapshot-b "docs/versions/latest/dropbox/analytics/dropbox_search_audit_snapshot.json" `
  --name-a "prev" --name-b "current" --out-dir "docs/reportes"
```

---

## 7) Ejecución manual del pipeline

### Corrida completa con auditoría + profiling

```powershell
& "./.venv/Scripts/python.exe" integrar_dropbox.py --audit-search --profiling --verbose
```

### Corrida conservadora (sin auditoría)

```powershell
& "./.venv/Scripts/python.exe" integrar_dropbox.py --verbose
```

### Corrida con enforcement de estructura

```powershell
& "./.venv/Scripts/python.exe" integrar_dropbox.py --enforce-structure --audit-search --profiling --verbose
```

---

## 8) GitHub Actions (CI/CD)

### Diseño recomendado

- Trigger: `pull_request` y `push` en `main`.
- Jobs:
  1. Preparar Python + dependencias.
  2. Ejecutar `integrar_dropbox.py --audit-search --profiling`.
  3. Ejecutar `audit_ci.py` contra snapshot previo/actual.
  4. Subir artefactos (`audit`, `diff`, `performance`, `receptor`).
- Política:
  - Si `down_pct` > umbral o `avg_delta_score_final` cae más de umbral → **fail**.

### Variables útiles

- `CFDI_SAT_MODE` = `mock` | `http`
- `CFDI_SAT_ENDPOINT` = URL proveedor SAT (si `http`)

---

## 9) Interpretación de artefactos generados

| Artefacto | Ubicación típica | Cómo interpretarlo |
|---|---|---|
| Auditoría búsqueda | `docs/reportes/*_audit.json/csv` | Descomposición de score por documento |
| Diff histórico | `docs/reportes/*audit_diff*.json/csv/txt` | Cambios de ranking y de score entre versiones |
| Performance | `docs/reportes/*_performance.json/csv` | Costos por componente y cuello de botella |
| Facturas por receptor | `docs/dropbox_invoices_by_receptor.json` | Total, conteo y evolución por receptor |

---

## 10) Diagrama ASCII de arquitectura

```text
                +-------------------------------+
                |        Dropbox FACTURACION     |
                +---------------+---------------+
                                |
                                v
                 +--------------+--------------+
                 |  lector_dropbox + estructura |
                 | (ingesta/normalización base) |
                 +--------------+---------------+
                                |
                 +--------------+---------------+
                 | extracción contenido / XML CFDI|
                 | cfdi_xml_extractor             |
                 +--------------+----------------+
                                |
        +-----------------------+------------------------+
        |                                                |
        v                                                v
+-------+----------------+                    +----------+----------------+
| invoice_provider_classifier |                | aspel_invoice_menu         |
| proveedor detectado         |                | menú inteligente + SAT     |
+---------------+-------------+                +----------+----------------+
                |                                             |
                +-------------------+-------------------------+
                                    |
                                    v
                        +-----------+-----------+
                        | search_engine         |
                        | auditoría + profiling |
                        +-----------+-----------+
                                    |
                                    v
                        +-----------+-----------+
                        | audit_diff / audit_ci |
                        | comparación + gates CI |
                        +-----------+-----------+
                                    |
                                    v
                      +-------------+-------------+
                      | Streamlit dashboards       |
                      | histórico + receptor + UI  |
                      +----------------------------+
```

---

## 11) Glosario empresarial

| Término | Definición |
|---|---|
| CFDI | Comprobante Fiscal Digital por Internet (factura electrónica MX). |
| UUID | Identificador único del timbre fiscal de un CFDI. |
| SAT | Servicio de Administración Tributaria (México). |
| Aspel | Plataforma/ERP de emisión y gestión de facturación. |
| Snapshot | Foto versionada del estado de auditoría/performance en un momento. |
| Diff | Comparación entre snapshots para evaluar mejora o degradación. |
| Profiling | Medición de tiempos por componente del motor de búsqueda. |
| Receptor | RFC/entidad que recibe la factura (cliente). |
| CI/CD | Integración y entrega continua con validaciones automáticas. |

---

## 12) Estilo corporativo (UI)

Paleta azul recomendada para paneles ejecutivos:

- `#0D47A1`
- `#1565C0`
- `#1E88E5`
- `#42A5F5`

---

## 13) Resumen ejecutivo

Este ecosistema proporciona una operación empresarial robusta para facturación documental en Dropbox con trazabilidad, validación fiscal, analítica por receptor, control de calidad por CI/CD y visualización ejecutiva en Streamlit.

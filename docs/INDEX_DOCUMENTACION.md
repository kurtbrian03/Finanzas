# 📚 Índice Maestro de Documentación del Proyecto

Este archivo centraliza **todas las versiones maestras de documentación**, permitiendo una navegación rápida y clara desde VS Code o GitHub.

La documentación está organizada por **tipos de formato**, **nivel de detalle** y **propósito**, siguiendo estándares profesionales de arquitectura, documentación técnica y control de versiones.

---

## 🧭 1. Documentación Maestra (Prompts Base)

### 🔹 1.1 [ARCHIVO_MAESTRO_DOCUMENTACION_EXTENDIDA.txt](ARCHIVO_MAESTRO_DOCUMENTACION_EXTENDIDA.txt)
**Descripción:**  
Versión completa, exhaustiva y altamente descriptiva.  
Incluye:
- ANSI
- ISO
- AWS/Google/Microsoft
- Diagramas
- Roadmap
- Manual técnico
- Múltiples formatos documentales

**Uso recomendado:**
- Como prompt base para agentes
- Como referencia arquitectónica completa
- Como documento madre del proyecto

---

### 🔹 1.2 [ARCHIVO_MAESTRO_DOCUMENTACION_OPCION_C.txt](ARCHIVO_MAESTRO_DOCUMENTACION_OPCION_C.txt)
**Descripción:**  
Versión optimizada bajo la estrategia **Opción C (nivel mixto)**:
- PDF y LaTeX → completos
- Markdown y HTML → intermedios
- Notion y Confluence → resumidos
- EPUB → ligero

**Uso recomendado:**
- Como plantilla para exportación a múltiples formatos
- Como documentación adaptable según el medio
- Como referencia para documentación modular

---

### 🔹 1.3 [PROMPT_MAESTRO_TOTAL_SISTEMA_DOCUMENTAL.txt](PROMPT_MAESTRO_TOTAL_SISTEMA_DOCUMENTAL.txt)
**Descripción:**  
Marco integral del ecosistema documental: portal, formatos, versionado, automatización, README, changelog y evolución.

**Uso recomendado:**
- Como contrato operativo documental
- Como guía de mantenimiento para agentes y desarrolladores
- Como referencia para escalar la plataforma documental

---

### 🔹 1.4 [PROMPTS_MAESTROS_SISTEMA_DOCUMENTAL_COMPLETO.txt](PROMPTS_MAESTROS_SISTEMA_DOCUMENTAL_COMPLETO.txt)
**Descripción:**  
Paquete con 5 prompts maestros listos para pegar en VS Code: README, portal, automatización, versionado y changelog.

**Uso recomendado:**
- Como kit rápido de operación documental
- Como guía de prompts reutilizables para agentes
- Como referencia táctica para iteraciones de documentación

---

### 🔹 1.5 [PROMPT_MAESTRO_TOTAL_DROPBOX_DASHBOARD_IA.txt](PROMPT_MAESTRO_TOTAL_DROPBOX_DASHBOARD_IA.txt)
**Descripción:**  
Prompt de integración completa para ingesta Dropbox, clasificación automática, visores (imágenes/PDF), dashboard documental, etiquetas inteligentes y clasificador IA.

**Uso recomendado:**
- Como blueprint funcional para expansión de módulos documentales
- Como referencia de roadmap técnico de automatización documental
- Como guía de implementación multi-módulo con trazabilidad

---

## 📄 2. Documentación por Formato

### 📘 2.1 PDF (Formal / Corporativo)
**Archivo:**
- [pdf/DOCUMENTACION_INTERNA.pdf.txt](pdf/DOCUMENTACION_INTERNA.pdf.txt)

**Contenido:**  
Versión completa para exportar a PDF desde Word/Docs/LibreOffice.  
Incluye arquitectura, flujos, diagramas, roadmap y manual técnico.

---

### 📝 2.2 Markdown (GitHub / Repositorios)
**Archivo:**
- [markdown/README_GITHUB.md](markdown/README_GITHUB.md)

**Contenido:**  
Versión intermedia, clara y navegable.  
Ideal para repositorios públicos o privados.

---

### 🌐 2.3 HTML (Documentación Web)
**Archivo:**
- [html/DOCUMENTACION_WEB.html](html/DOCUMENTACION_WEB.html)

**Contenido:**  
Versión web lista para integrarse en portales internos o documentación estática.

---

### 📚 2.4 LaTeX (Académico / Técnico)
**Archivo:**
- [latex/DOCUMENTACION_LATEX.tex](latex/DOCUMENTACION_LATEX.tex)

**Contenido:**  
Versión completa para generar documentación profesional en PDF mediante LaTeX.

---

### 📱 2.5 EPUB (Lectura ligera)
**Archivos:**
- [epub/EPUB_CONTENT.opf](epub/EPUB_CONTENT.opf)
- [epub/EPUB_TOC.ncx](epub/EPUB_TOC.ncx)
- [epub/EPUB_Text/document.xhtml](epub/EPUB_Text/document.xhtml)

**Contenido:**  
Versión ligera para lectura en dispositivos móviles o e-readers.

---

### 🧩 2.6 Notion (Modular / Colaborativo)
**Archivo:**
- [notion/NOTION_PAGE.json](notion/NOTION_PAGE.json)

**Contenido:**  
Bloques listos para importar en Notion como página de documentación.

---

### 🏢 2.7 Confluence (Wiki Empresarial)
**Archivo:**
- [confluence/DOCUMENTACION_CONFLUENCE.wiki](confluence/DOCUMENTACION_CONFLUENCE.wiki)

**Contenido:**  
Versión resumida para integrarse en espacios de documentación corporativa.

---

## ⚙️ 3. Automatización documental

### 3.1 Script de regeneración

- [scripts/regenerar_documentacion.py](scripts/regenerar_documentacion.py)

Permite:
- Regenerar un formato específico
- Regenerar todos los formatos
- Validar integridad de archivos mínimos
- (Opcional) registrar entrada en changelog documental

### 3.2 Guía de scripts

- [scripts/README.md](scripts/README.md)

### 3.3 Integración Dropbox

- Script: [../integrar_dropbox.py](../integrar_dropbox.py)
- Guía: [markdown/DROPBOX_IMPORT.md](markdown/DROPBOX_IMPORT.md)
- Mapeo JSON: [dropbox_mapeo_documentos.json](dropbox_mapeo_documentos.json)
- Mapeo Markdown: [dropbox_mapeo_documentos.md](dropbox_mapeo_documentos.md)
- Asignación app: [dropbox_asignacion_app.json](dropbox_asignacion_app.json)

---

## 🧾 4. Versionado y control de cambios

### 4.1 Versiones documentales

- [versions/README.md](versions/README.md)
- [versions/LATEST_VERSION.txt](versions/LATEST_VERSION.txt)
- [versions/v1/README.md](versions/v1/README.md)
- [versions/v2/README.md](versions/v2/README.md)
- [versions/v3/README.md](versions/v3/README.md)

### 4.2 Changelog documental

- [CHANGELOG_DOCUMENTACION.md](CHANGELOG_DOCUMENTACION.md)

---

## 🗂️ 5. Estructura Recomendada del Directorio `docs/`

```text
docs/
│
├── ARCHIVO_MAESTRO_DOCUMENTACION_EXTENDIDA.txt
├── ARCHIVO_MAESTRO_DOCUMENTACION_OPCION_C.txt
├── PROMPT_MAESTRO_TOTAL_SISTEMA_DOCUMENTAL.txt
├── PROMPTS_MAESTROS_SISTEMA_DOCUMENTAL_COMPLETO.txt
├── PROMPT_MAESTRO_TOTAL_DROPBOX_DASHBOARD_IA.txt
├── INDEX_DOCUMENTACION.md
├── CHANGELOG_DOCUMENTACION.md
│
├── pdf/
│   └── DOCUMENTACION_INTERNA.pdf.txt
│
├── markdown/
│   ├── README_GITHUB.md
│   └── DROPBOX_IMPORT.md
│
├── html/
│   └── DOCUMENTACION_WEB.html
│
├── latex/
│   └── DOCUMENTACION_LATEX.tex
│
├── notion/
│   └── NOTION_PAGE.json
│
├── confluence/
│   └── DOCUMENTACION_CONFLUENCE.wiki
│
├── scripts/
│   ├── README.md
│   └── regenerar_documentacion.py
│
├── dropbox_mapeo_documentos.json
├── dropbox_mapeo_documentos.md
├── dropbox_asignacion_app.json
│
├── versions/
│   ├── README.md
│   ├── LATEST_VERSION.txt
│   ├── v1/
│   │   └── README.md
│   ├── v2/
│   │   └── README.md
│   └── v3/
│       └── README.md
│
└── epub/
    ├── EPUB_CONTENT.opf
    ├── EPUB_TOC.ncx
    └── EPUB_Text/
        └── document.xhtml
```

## 🎯 6. Propósito del Índice

Este índice sirve como:

- Mapa de navegación para toda la documentación
- Referencia rápida para desarrolladores y auditores
- Punto de entrada único para VS Code
- Guía de exportación a múltiples formatos
- Estructura estándar para documentación empresarial

## 🚀 7. Próximos pasos sugeridos

- Integrar este índice en el README principal del repositorio
- Añadir badges o enlaces rápidos en GitHub
- Automatizar exportaciones con scripts (listo para expansión)
- Versionar snapshots documentales por release

## 📎 8. Referencias rápidas

- Manual técnico: [MANUAL_TECNICO.md](MANUAL_TECNICO.md)
- Roadmap de producto: [ROADMAP.md](ROADMAP.md)
- Diagrama de arquitectura: [ARCHITECTURE_DIAGRAM.md](ARCHITECTURE_DIAGRAM.md)

## 🗃️ 9. Documentos importados desde Dropbox

- Mapeo: [dropbox_mapeo_documentos.json](dropbox_mapeo_documentos.json)
- Resumen: [dropbox_mapeo_documentos.md](dropbox_mapeo_documentos.md)
- Asignación app: [dropbox_asignacion_app.json](dropbox_asignacion_app.json)
- Guía markdown: [markdown/DROPBOX_IMPORT.md](markdown/DROPBOX_IMPORT.md)

## 🧭 10. Dashboard visual

- Módulo: `dropbox_integration/dashboard_documentos.py`
- Permite filtros por tipo/carpeta y apertura de visores.

## 🤖 11. Clasificador IA

- Módulo: `dropbox_integration/ai_classifier.py`
- Sugiere categoría, etiquetas y módulo destino.

## 📄 12. Visor PDF

- Módulo: `dropbox_integration/pdf_viewer.py`
- Navegación por página, zoom y exportación de página como imagen.

## 🏷️ 13. Etiquetas inteligentes

- Módulo: `dropbox_integration/tagging_engine.py`
- Etiquetado automático + edición manual de etiquetas.

## 🔎 14. Búsqueda avanzada Dropbox IA

- Motor: `dropbox_integration/search_engine.py`
- Extracción de contenido: `dropbox_integration/content_extractor.py`
- Guía: [markdown/DROPBOX_SEARCH.md](markdown/DROPBOX_SEARCH.md)
- Estadísticas: [dropbox_search_stats.json](dropbox_search_stats.json)

## 📊 15. Analítica documental Dropbox IA

- Motor analítico: `dropbox_integration/analytics_engine.py`
- Árbol virtual: `dropbox_integration/folder_tree.py`
- Reportes: `dropbox_integration/report_generator.py`
- Guía: [markdown/DROPBOX_ANALYTICS.md](markdown/DROPBOX_ANALYTICS.md)
- Artefactos: [dropbox_analytics.json](dropbox_analytics.json), [dropbox_folder_tree.json](dropbox_folder_tree.json)


## 🧪 16. Auditoría de búsqueda generada

- Snapshot: `docs/versions/latest/dropbox/analytics/dropbox_search_audit_snapshot.json`
- Snapshot CSV: `docs/versions/latest/dropbox/analytics/dropbox_search_audit_snapshot.csv`
- Reportes incluyen `*_audit.json` y `*_audit.csv` en ZIP/TXT/Excel cuando existe auditoría.

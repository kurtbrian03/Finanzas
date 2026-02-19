# Roadmap de Mejoras

## Corto plazo (1–2 semanas)

### Objetivo
Consolidar la base modular, mejorar mantenibilidad inmediata y trazabilidad.

### Tareas clave
- Limpieza fina de imports y reexportaciones internas.
- Homogeneizar docstrings en todos los módulos.
- Añadir validaciones de lint/format en pipeline local.
- Persistencia básica del historial con `history/persistence.py` (opt-in).
- Pruebas de humo automáticas para rutas del router.

### Riesgos potenciales
- Regresiones por refactors menores en import paths.
- Desalineación de cache (`st.cache_data`) con cambios de firma.

### Dependencias
- Entorno Python estable en `.venv`.
- Convenciones internas de arquitectura acordadas por el equipo.

---

## Mediano plazo (1–2 meses)

### Objetivo
Aumentar valor analítico y rendimiento operativo.

### Tareas clave
- Integración con APIs SAT (consulta validación y metadatos oficiales).
- Dashboards analíticos con KPIs fiscales y tendencias.
- Cache inteligente de análisis PDF/Excel por hash de archivo.
- Profiling de rendimiento para PDFs de gran volumen.
- Controles de seguridad adicionales para datos sensibles.

### Riesgos potenciales
- Límites/cuotas de API SAT.
- Incremento de complejidad en sincronización de estado y caché.

### Dependencias
- Credenciales y acceso API SAT.
- Políticas de seguridad y compliance definidas.

---

## Largo plazo (3–6 meses)

### Objetivo
Evolucionar hacia plataforma empresarial inteligente y multiusuario.

### Tareas clave
- IA documental avanzada para clasificación/etiquetado automático CFDI.
- Motor de reglas fiscales configurable por organización.
- Soporte multiusuario con control de roles y auditoría persistente.
- Integración con BD empresarial (PostgreSQL/SQL Server).
- API interna para interoperabilidad con ERP/contabilidad.

### Riesgos potenciales
- Complejidad de gobernanza de datos y seguridad.
- Costos de infraestructura y operación IA.

### Dependencias
- Infraestructura de base de datos y autenticación.
- Definición de arquitectura de despliegue (on-prem/cloud híbrido).

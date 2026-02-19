# Mapa de Integración ERP–PINPON

Documento oficial de arquitectura para la integración entre el ecosistema PINPON y ERPs empresariales (Alpha ERP, SAP Business One, CONTPAQi, Aspel o plataformas equivalentes).

---

## 1. Introducción

### ¿Qué es un mapa de integración?
Un mapa de integración es la representación formal de **cómo, cuándo y bajo qué reglas** se intercambian datos entre sistemas. En entornos empresariales, este mapa no solo describe endpoints o archivos, sino también:

- dominios de negocio involucrados,
- reglas de validación y calidad de datos,
- eventos disparadores,
- trazabilidad y auditoría,
- estrategias de recuperación ante fallos.

### ERP transaccional vs PINPON documental inteligente
| Dimensión | ERP transaccional | PINPON documental inteligente |
|---|---|---|
| Propósito | Registrar y operar transacciones de negocio | Ingerir, validar, auditar y enriquecer evidencia documental/fiscal |
| Núcleo | Compras, ventas, inventario, bancos, nómina, contabilidad | XML/PDF CFDI, validación SAT, auditoría fiscal, clasificación documental |
| Modelo operativo | Maestro transaccional y contable | Maestro documental, evidencia y analítica fiscal |
| Resultado | Operación diaria y estados financieros | Control de cumplimiento, calidad fiscal y automatización documental |

### Cómo PINPON complementa al ERP
PINPON agrega capacidades que normalmente no son núcleo del ERP:

- **Validación SAT** de CFDI (estatus, UUID, emisor/receptor, timbrado).
- **Auditoría documental** (consistencia de importes, impuestos, fechas, relación con órdenes/pagos).
- **Análisis fiscal** (riesgos, anomalías, cumplimiento, tendencias).
- **Automatización documental** (clasificación, etiquetado, reglas de ruteo y sincronización).

### Objetivo del documento
Definir de forma unificada:

1. flujos de datos bidireccionales,
2. puntos de integración técnica,
3. dependencias entre módulos,
4. modelo de eventos,
5. reglas de seguridad, auditoría, compatibilidad y operación.

### Alcance
- Integración de PINPON con módulos ERP de Compras, Ventas, Inventarios, Nómina, Bancos y Contabilidad.
- Patrones técnicos (REST, webhooks, colas, sincronización batch/real-time).
- Gobierno de datos, trazabilidad, monitoreo y resiliencia.

### No-alcance
- Diseño específico de UI por proveedor ERP.
- Implementación de conectores propietarios cerrados.
- Definición legal/tax advisory fuera del plano técnico-operativo.

### Beneficios esperados
- Reducción de errores de captura/manuales.
- Menor riesgo fiscal por inconsistencias CFDI–ERP.
- Incremento de trazabilidad y auditabilidad extremo a extremo.
- Base técnica escalable para crecimiento modular.

---

## 2. Arquitectura general de integración

```text
        ┌──────────────────────────┐        ┌────────────────────────────┐
        │           ERP            │ <----> │           PINPON           │
        │ (Transaccional/Contable) │        │ (Documental/Fiscal/IA)     │
        └──────────────────────────┘        └────────────────────────────┘
               ▲            ▲                       ▲            ▲
               │            │                       │            │
       Compras/Ventas/Inventarios          XML/PDF/Validación SAT/Auditoría
       Bancos/Nómina/Contabilidad          Dashboards/Automatización/Alertas
```

### Flujo bidireccional
1. **ERP → PINPON**: órdenes, recepciones, pólizas, estatus de pago, movimientos de almacén.
2. **PINPON → ERP**: validaciones SAT, conciliaciones, estatus documental, propuestas de póliza, incidencias.

### Módulos ERP que consumen datos de PINPON
- Compras: estatus SAT, validación proveedor, incidencias de CFDI.
- Ventas: estatus factura emitida, trazabilidad de cobro.
- Bancos: conciliación factura–pago y alertas de duplicidad.
- Contabilidad: pólizas propuestas, discrepancias fiscales.

### Módulos PINPON que consumen datos del ERP
- Clasificación documental guiada por catálogos ERP (proveedor, centro de costo, cuenta).
- Motor de auditoría cruzada CFDI vs operación real.
- Dashboards por módulo y estatus de integración.

### Eventos disparadores de sincronización
- Recepción de XML/PDF (proveedor o cliente).
- Emisión CFDI de venta.
- Registro/confirmación de pago.
- Timbrado de nómina.
- Cierre diario/contable (batch).

### Reglas operativas transversales
- **Seguridad**: autenticación fuerte (JWT/API Key), TLS, firma de payload cuando aplique.
- **Auditoría**: bitácora inmutable por transacción (`trace_id`, `actor`, `timestamp`, `resultado`).
- **Versionado**: contratos API versionados (`/v1`, `/v2`) + compatibilidad backward.
- **Compatibilidad**: mapeo por adaptador ERP (Strategy pattern por proveedor).
- **Fallback**: cola de reintentos y modo degradado por módulo.
- **Recuperación**: replay de eventos desde DLQ/repository de eventos.
- **Monitoreo**: métricas de latencia, error rate, lag, throughput.
- **Logging**: estructurado JSON, niveles y correlación por `trace_id`.

---

## 3. Compras → Integración con PINPON

### Flujo funcional
- PINPON recibe CFDI de proveedores (ingreso/egreso, notas de crédito, etc.).
- Se ejecuta validación SAT en línea o diferida.
- Se auditan campos clave: UUID, RFC emisor/receptor, fecha, subtotal, IVA, total.
- Se vincula contra OC/recepción del ERP.
- Se actualiza CxP con estatus documental y fiscal.

### Diagrama ASCII (flujo)
```text
Proveedor XML/PDF
      │
      ▼
┌───────────────┐   validar SAT   ┌───────────────┐
│    PINPON     │ ───────────────▶│  Servicio SAT │
│ Ingesta/Audit │◀─────────────── │   (estatus)   │
└──────┬────────┘                 └───────────────┘
       │ mapeo OC/CxP
       ▼
┌───────────────┐
│      ERP      │
│ Compras/CxP   │
└───────────────┘
```

### Modelo de datos propuesto (compras)
| Campo | Fuente | Tipo | Regla |
|---|---|---|---|
| `uuid` | XML CFDI | string | Único, obligatorio |
| `rfc_emisor` | XML CFDI | string | Debe existir en catálogo proveedor |
| `rfc_receptor` | XML CFDI | string | Debe coincidir con RFC empresa |
| `monto_total` | XML CFDI | decimal | `>= 0` |
| `oc_id` | ERP | string | Nullable, requerido para automatización total |
| `sat_status` | SAT | enum | `vigente/cancelado/no_encontrado` |
| `audit_score` | PINPON | int | 0–100 |

### Secuencia
```text
PINPON -> SAT: validar(uuid, rfc_emisor, rfc_receptor, total)
SAT --> PINPON: estatus
PINPON -> ERP: upsert_documento_compra + estatus_sat + incidencias
ERP --> PINPON: confirmación recepción/OC/CxP
PINPON -> AuditLog: registrar evento integrado
```

### Eventos
- `compra.xml_recibido`
- `compra.sat_validado`
- `compra.audit_detectada`
- `compra.erp_sincronizada`
- `compra.error_integracion`

### Reglas
- Conciliación documental obligatoria antes de contabilizar CxP automática.
- Si `sat_status != vigente`, bloquear contabilización automática y generar alerta.
- Seguridad por rol (`Administrador`, `Auditor`, `Lectura`) para acciones críticas.

---

## 4. Ventas → Integración con PINPON

### Flujo funcional
- PINPON procesa CFDI emitidos por ventas.
- Ejecuta validación SAT y genera indicadores comerciales/fiscales.
- Sincroniza con ERP: factura, pedido y estatus de cobranza.

### Diagrama ASCII (flujo)
```text
ERP Ventas/Facturación
        │ CFDI emitido
        ▼
   ┌──────────┐      validar SAT      ┌──────────┐
   │ PINPON   │ ────────────────────▶ │   SAT    │
   └────┬─────┘ ◀──────────────────── │          │
        │                                
        ▼
   Dashboards (clientes/ingresos/morosidad)
        │
        └──────────▶ ERP Cobranza (estatus pago)
```

### Modelo de datos propuesto (ventas)
| Campo | Tipo | Nota |
|---|---|---|
| `invoice_uuid` | string | UUID CFDI venta |
| `cliente_id` | string | Catálogo ERP |
| `pedido_id` | string | Relación comercial |
| `total` | decimal | Importe total |
| `payment_status` | enum | `pendiente/parcial/pagado/vencido` |
| `sat_status` | enum | Resultado validación SAT |

### Secuencia
```text
ERP -> PINPON: evento CFDI emitido
PINPON -> SAT: valida CFDI
PINPON -> ERP: actualiza estatus SAT + riesgo + trazabilidad
ERP -> PINPON: notifica pagos/cobranza
PINPON -> Dashboard: recalcula KPIs ventas
```

### Eventos
- `venta.cfdi_emitido`
- `venta.sat_validado`
- `venta.cobranza_actualizada`
- `venta.alerta_vencimiento`

### Reglas
- Si SAT reporta inconsistencia, marcar factura en cuarentena fiscal.
- Restricción de edición retroactiva de documentos sincronizados.

---

## 5. Inventarios / Almacén → Integración con PINPON

### Flujo funcional
- PINPON extrae conceptos de XML (clave SAT, cantidad, unidad, importe).
- Cruza con movimientos físicos y kardex del ERP.
- Detecta discrepancias documentales vs operativas.

### Diagrama ASCII
```text
XML CFDI conceptos
      │
      ▼
┌───────────────┐   cruce    ┌───────────────┐
│    PINPON     │ ─────────▶ │ ERP Inventario│
│ parser/audit  │ ◀───────── │ Kardex/Costos │
└──────┬────────┘            └───────────────┘
       │
       └────▶ Alertas de discrepancia (cantidad/costo)
```

### Modelo de datos
| Campo | Tipo | Regla |
|---|---|---|
| `sku_sat` | string | Normalizado |
| `qty_xml` | decimal | > 0 |
| `qty_kardex` | decimal | >= 0 |
| `cost_xml` | decimal | >= 0 |
| `cost_erp` | decimal | >= 0 |
| `delta_qty` | decimal | `qty_xml - qty_kardex` |
| `delta_cost` | decimal | `cost_xml - cost_erp` |

### Secuencia
```text
PINPON -> ERP: consulta movimientos por periodo
PINPON: compara conceptos XML vs kardex
PINPON -> ERP: publica discrepancias/ajustes propuestos
ERP -> PINPON: confirma ajuste aplicado
```

### Eventos
- `inventario.xml_parseado`
- `inventario.discrepancia_detectada`
- `inventario.ajuste_confirmado`

### Reglas
- Umbrales de tolerancia por producto/familia.
- Bloqueo de cierre de periodo con discrepancias críticas.

---

## 6. Nómina → Integración con PINPON

### Flujo funcional
- Ingesta de CFDI nómina.
- Validación SAT de timbrado y estructura.
- Auditoría de percepciones, deducciones, ISR, subsidio.
- Envío de resultados al ERP (pólizas/reportes laborales).

### Diagrama ASCII
```text
CFDI Nómina ──▶ PINPON Validador ──▶ SAT
      │              │                 │
      │              └──── auditoría ──┘
      ▼
 ERP Nómina/Contabilidad ◀── pólizas + incidencias
```

### Modelo de datos
| Campo | Tipo |
|---|---|
| `payroll_uuid` | string |
| `employee_id` | string |
| `gross_salary` | decimal |
| `deductions_total` | decimal |
| `isr_retained` | decimal |
| `subsidy_applied` | decimal |
| `sat_status` | enum |
| `anomaly_flags` | array[string] |

### Secuencia
```text
PINPON -> SAT: valida nómina UUID
PINPON -> MotorFiscal: calcula consistencias ISR/subsidio
PINPON -> ERP: exporta póliza y reporte de incidencias
ERP -> PINPON: acuse de contabilización
```

### Eventos
- `nomina.cfdi_recibido`
- `nomina.sat_validado`
- `nomina.anomalia_detectada`
- `nomina.poliza_publicada`

### Reglas
- Detección de duplicados por empleado/periodo/UUID.
- Control de acceso reforzado por sensibilidad de datos laborales.

---

## 7. Bancos → Integración con PINPON

### Flujo funcional
- PINPON procesa complementos de pago.
- Conciliación automática factura–pago.
- Publicación de estatus a ERP bancos/cobranza.

### Diagrama ASCII
```text
Complemento de Pago XML
          │
          ▼
      ┌──────────┐    concilia    ┌───────────────┐
      │ PINPON   │ ─────────────▶ │ ERP Bancos/CxC│
      └────┬─────┘ ◀───────────── │               │
           │
           └──▶ alertas duplicado / pago incompleto
```

### Modelo de datos
| Campo | Tipo |
|---|---|
| `payment_uuid` | string |
| `related_invoice_uuid` | string |
| `amount_paid` | decimal |
| `currency` | string |
| `bank_reference` | string |
| `reconciliation_status` | enum |

### Secuencia
```text
PINPON -> ERP: consulta saldo factura
PINPON: compara saldo vs pago reportado
PINPON -> ERP: aplica conciliación (auto/manual)
ERP -> PINPON: confirma asiento bancario
```

### Eventos
- `banco.pago_xml_recibido`
- `banco.conciliacion_ok`
- `banco.pago_duplicado`
- `banco.pago_incompleto`

### Reglas
- No aplicar automáticamente si referencia bancaria no coincide.
- Alertar cuando pago excede saldo remanente.

---

## 8. Contabilidad automática → Integración con PINPON

### Flujo funcional
- PINPON centraliza validaciones CFDI y auditoría fiscal.
- Genera propuestas de pólizas y cruces con catálogo contable ERP.
- Detecta inconsistencias entre XML y póliza registrada.

### Diagrama ASCII
```text
CFDI + reglas fiscales
       │
       ▼
┌───────────────┐   pólizas propuestas   ┌───────────────┐
│    PINPON     │ ─────────────────────▶ │ ERP Contable  │
│ fiscal engine │ ◀───────────────────── │ Catálogo/Asien│
└──────┬────────┘                        └───────────────┘
       │
       └────▶ excepciones / auditoría fiscal
```

### Modelo de datos
| Campo | Tipo | Nota |
|---|---|---|
| `entry_id` | string | Identificador póliza propuesta |
| `cfdi_uuid` | string | Referencia documental |
| `account_debit` | string | Cuenta cargo |
| `account_credit` | string | Cuenta abono |
| `tax_breakdown` | object | IVA/ISR/retenciones |
| `consistency_status` | enum | `ok/warn/error` |

### Secuencia
```text
PINPON -> MotorContable: mapear CFDI a cuentas
PINPON -> ERP: publicar póliza propuesta
ERP -> PINPON: confirmar/rechazar
PINPON -> AuditLog: registrar motivo y evidencia
```

### Eventos
- `conta.poliza_generada`
- `conta.poliza_rechazada`
- `conta.inconsistencia_xml_poliza`

### Reglas
- Catálogo contable versionado.
- Regla de doble validación para pólizas automáticas de alto impacto.

---

## 9. Mapa global de integración (ASCII completo)

```text
                                  ┌───────────────────────────────────────────────┐
                                  │                    PINPON                     │
                                  │ Ingesta XML/PDF | SAT | Auditoría | Dashboard │
                                  └───────────────┬───────────────────────────────┘
                                                  │
                     ┌────────────────────────────┼────────────────────────────┐
                     │                            │                            │
               ┌─────▼─────┐                ┌────▼─────┐                ┌─────▼─────┐
               │  Compras  │                │  Ventas  │                │ Inventario │
               │ OC/CxP    │                │ CxC/CRM  │                │ Kardex/Cost│
               └─────┬─────┘                └────┬─────┘                └─────┬─────┘
                     │                            │                            │
                     │                            │                            │
               ┌─────▼─────┐                ┌────▼─────┐                ┌─────▼─────┐
               │  Bancos   │                │  Nómina  │                │Contabilidad│
               │ Conciliac │                │ Timbrado │                │ Pólizas/Fis│
               └─────┬─────┘                └────┬─────┘                └─────┬─────┘
                     │                            │                            │
                     └───────────────┬────────────┴───────────────┬────────────┘
                                     │                            │
                                ┌────▼────────────────────────────▼────┐
                                │             ERP Completo             │
                                │ Alpha/SAP B1/CONTPAQi/Aspel/Otros   │
                                └───────────────────────────────────────┘

Controles transversales:
- Seguridad: IAM, TLS, firmas, segregación por rol
- Auditoría: bitácora inmutable por trace_id
- Sincronización: real-time + batch + replay
- Resiliencia: retry, DLQ, fallback por módulo
- Observabilidad: logs estructurados, métricas, alertas
```

---

## 10. Puntos de integración técnica

### Mecanismos soportados
1. **APIs REST**
   - Operaciones idempotentes (`PUT/PATCH` con `external_id`).
   - Contratos versionados por dominio (`/api/v1/compras/...`).

2. **Webhooks**
   - Eventos near real-time (emitir CFDI, pago recibido, póliza aplicada).
   - Verificación de firma (`HMAC`) y anti-replay.

3. **Lectura XML/PDF**
   - Parser estructural de CFDI + extracción semántica.
   - OCR opcional para anexos no estructurados.

4. **Sincronización programada**
   - Jobs horarios/diarios para reconciliación y cierres.

5. **Sincronización en tiempo real**
   - Publicación inmediata de cambios críticos (pagos, cancelaciones SAT).

### Reglas técnicas
- **Seguridad**: OAuth2/JWT o API Keys rotables; mínimo privilegio.
- **Auditoría**: toda transacción con `trace_id`, `source_system`, `payload_hash`.
- **Manejo de errores**: catálogo de códigos (`INT-4XX`, `INT-5XX`, `SAT-XXX`).
- **Versionado**: no romper contratos; deprecación controlada.
- **Compatibilidad**: adapters por ERP y mapper de catálogos.
- **Rollback**: compensaciones por evento (saga) para consistencia eventual.
- **Logging**: JSON estructurado, redacción de secretos.
- **Monitoreo/alertas**: SLO por módulo y alarmas por desviación.
- **Colas de mensajes**: Kafka/Rabbit/SQS para desacoplar y escalar.

---

## 11. Modelo de datos unificado ERP–PINPON

### Entidades principales
- `Company`
- `Vendor`
- `Customer`
- `CFDI_Document`
- `Payment_Complement`
- `Inventory_Movement`
- `Accounting_Entry`
- `Payroll_Receipt`
- `Integration_Event`
- `Audit_Record`

### Relaciones clave
- `CFDI_Document` ↔ `Vendor/Customer`
- `CFDI_Document` ↔ `Accounting_Entry`
- `CFDI_Document` ↔ `Payment_Complement`
- `Inventory_Movement` ↔ `CFDI_Document`
- `Integration_Event` ↔ cualquier entidad sincronizada

### Reglas de integridad
- `uuid` único global por CFDI.
- `rfc_emisor/receptor` con validación estructural y catálogo.
- `monto_total` coherente con desglose de impuestos.
- `sat_status` obligatorio para contabilización automática.

### JSON ejemplo — Documento CFDI unificado
```json
{
  "uuid": "C3A9F0A1-7E2C-4E8F-9D7B-1234567890AB",
  "tipo": "ingreso",
  "rfc_emisor": "AAA010101AAA",
  "rfc_receptor": "BBB010101BBB",
  "fecha_emision": "2026-02-19T08:30:00Z",
  "subtotal": 10000.00,
  "impuestos": {
    "iva": 1600.00,
    "retenciones": 0.00
  },
  "total": 11600.00,
  "sat_status": "vigente",
  "source": "pinpon"
}
```

### Payload ejemplo — Publicación a ERP
```json
{
  "trace_id": "int-20260219-000145",
  "event": "compra.sat_validado",
  "erp_target": "sap-b1",
  "document": {
    "uuid": "C3A9F0A1-7E2C-4E8F-9D7B-1234567890AB",
    "vendor_code": "V-000445",
    "amount_total": 11600.00,
    "sat_status": "vigente"
  },
  "audit": {
    "score": 97,
    "warnings": []
  }
}
```

### Ejemplo de transformación
```text
Entrada PINPON: rfc_emisor + uuid + total + sat_status
Transformación: lookup vendor_code ERP por RFC
Salida ERP: ap_invoice_header(vendor_code, ext_uuid, amount, validation_status)
```

---

## 12. Diagramas de secuencia

### A) Recepción XML → Validación SAT → ERP
```text
Proveedor -> PINPON: subir XML CFDI
PINPON -> SAT: validar uuid/rfc/total
SAT -> PINPON: estatus=vigente
PINPON -> ERP: crear/actualizar documento
ERP -> PINPON: acuse + id interno
PINPON -> AuditLog: registrar traza completa
```

### B) Confirmación de pago
```text
Banco/ERP -> PINPON: evento pago confirmado
PINPON -> MotorConciliacion: cruza factura vs pago
PINPON -> ERP: actualizar estatus cobranza
ERP -> PINPON: confirmación final
```

### C) Auditoría y sincronización
```text
Scheduler -> PINPON: iniciar reconciliación batch
PINPON -> ERP: consulta deltas
PINPON -> SAT: validación masiva de pendientes
PINPON -> ERP: correcciones propuestas
PINPON -> Alerting: notificar errores críticos
```

---

## 13. Diagramas de eventos

### Taxonomía de eventos
- **Disparadores**: `xml_recibido`, `cfdi_emitido`, `pago_confirmado`, `nomina_timbrada`.
- **Internos**: `sat_validado`, `audit_score_calculado`, `mapper_resuelto`.
- **Externos**: `erp_ack`, `erp_rechazo`, `sat_no_disponible`.
- **Auditoría**: `audit_warning`, `audit_error`, `audit_override`.
- **Error**: `integracion_timeout`, `payload_invalido`, `auth_failed`.
- **Recuperación**: `retry_programado`, `replay_ejecutado`, `dlq_resuelta`.

### Diagrama de eventos (alto nivel)
```text
xml_recibido
   └─> sat_validado
       ├─> erp_sync_ok
       │    └─> audit_record_closed
       └─> erp_sync_error
            ├─> retry_programado
            └─> dlq_enqueued
```

---

## 14. Roadmap de implementación

### Fase 1 — Fundacional
- Definir contratos API/eventos y modelo de datos unificado.
- Implementar conectores base (REST + batch).
- Habilitar observabilidad mínima (logs, métricas, alertas básicas).

### Fase 2 — Módulos de mayor impacto
1. Compras
2. Ventas
3. Bancos

### Fase 3 — Profundización operativa
4. Inventarios
5. Contabilidad automática
6. Nómina

### Dependencias técnicas
- Catálogos maestros ERP (proveedor, cliente, cuentas, almacenes).
- Servicio SAT disponible con estrategias de fallback.
- Infraestructura de eventos/colas para desacople.

### Riesgos principales
- Inconsistencia de catálogos entre ERP y documentos.
- Variabilidad de implementaciones por proveedor ERP.
- Fallos SAT o latencia externa alta.

### Estrategia incremental
- Piloto por módulo y por unidad de negocio.
- Feature flags por integración.
- Rollout gradual con métricas de aceptación.

### Pruebas automáticas recomendadas
- Contratos API (consumer-driven contracts).
- Pruebas de idempotencia.
- Pruebas de reconciliación (XML vs ERP).
- Pruebas de resiliencia (caídas SAT/ERP).

### Validación con datos reales
- Dataset histórico por módulo.
- Casos borde: CFDI cancelado, pago parcial, nómina duplicada.
- Auditoría de resultados contra cierre contable.

### Escalabilidad
- Procesamiento asíncrono por colas.
- Particionado por empresa/periodo/módulo.
- Cache de catálogos y resultados SAT cuando normativamente proceda.

---

## Apéndice A — Reglas maestras de integración

1. **No se contabiliza automáticamente** un documento no vigente ante SAT.
2. Todo evento debe tener `trace_id` y `payload_hash`.
3. Todo cambio de estado crítico exige acuse del sistema destino.
4. Cualquier falla > umbral definido debe generar alerta operacional.
5. El historial de auditoría es inmutable y consultable por rol autorizado.

## Apéndice B — Matriz rápida de compatibilidad

| ERP | Integración recomendada | Nivel inicial |
|---|---|---|
| Alpha ERP | API + batch CSV/XML | Medio |
| SAP Business One | Service Layer/DI API + eventos | Alto |
| CONTPAQi | SDK/DB bridge controlado + colas | Medio |
| Aspel | Interfaces de importación + API auxiliar | Medio |
| ERP moderno cloud | REST/Webhooks nativos | Alto |

---

### Estado del documento
- Tipo: **Guía oficial de arquitectura**
- Versión: **1.0**
- Uso: diseño, implementación y auditoría de integración ERP–PINPON

# Arquitectura del Sistema

## 1) Diagrama ASCII (módulos y flujo)

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                                 app.py                                     │
│                    (entrypoint + bootstrap + dispatch)                     │
└───────────────┬───────────────────────────────┬────────────────────────────┘
                │                               │
                v                               v
      ┌──────────────────┐             ┌──────────────────┐
      │   core.lifecycle │             │    core.router   │
      │ bootstrap_app()  │             │ dispatch()       │
      └────────┬─────────┘             └────────┬─────────┘
               │                                 │
               v                                 v
      ┌──────────────────┐             ┌──────────────────┐
      │ core.state_mgr   │<----------->│  ui.navigation   │
      │ session_state    │             │ sidebar/routes   │
      └────────┬─────────┘             └────────┬─────────┘
               │                                 │
               └──────────────┬──────────────────┘
                              v
                     ┌──────────────────┐
                     │    ui.layout     │
                     │ page orchestration│
                     └───────┬──────────┘
                             │
              ┌──────────────┼───────────────────────────────────────────────┐
              v              v                      v                         v
      ┌──────────────┐ ┌──────────────┐     ┌──────────────┐         ┌──────────────┐
      │ analysis/*   │ │ validation/* │     │ downloads/*  │         │ history/*    │
      │ PDF/Excel    │ │ RFC/Folio    │     │ filtros+zip  │         │ audit logs   │
      └──────┬───────┘ └──────┬───────┘     └──────┬───────┘         └──────┬───────┘
             │                │                    │                        │
             └──────────┬─────┴──────────┬─────────┴───────────────┬────────┘
                        v                v                         v
                     ┌────────────────────────────────────────────────────────┐
                     │                    ui.components                       │
                     │ previews PDF/Excel (solo lectura) + panel análisis    │
                     └────────────────────────────────────────────────────────┘
```

## 2) Pseudo-UML (módulos y dependencias)

```text
class app.py {
  +main()
}

class core.state_manager.StateManager {
  +initialize()
  +get(key)
  +set(key, value)
  +append_log(item)
  +append_event(event)
}

class core.router {
  +build_routes()
  +dispatch(state, selected_label, handlers)
}

class ui.layout {
  +render_document_viewer(state, carpeta)
  +render_validation_page(state)
  +render_downloads_page(state, carpeta)
  +render_history_page(state)
  +render_settings_page(state)
}

class analysis.pdf_analyzer {
  +analizar_pdf(path, max_paginas)
}

class analysis.excel_analyzer {
  +analizar_excel(df)
}

class validation.rfc_validator {
  +validar_rfc(rfc)
}

class validation.folio_validator {
  +validar_folio(folio)
}

class downloads.download_filters {
  +indexar_documentos(carpeta)
  +aplicar_filtros(...)
}

class downloads.file_packager {
  +construir_zip_memoria(paths)
}

class history.history_manager {
  +register_action(state, accion, detalle)
}

app.py --> core.lifecycle
app.py --> core.router
app.py --> ui.navigation
app.py --> ui.layout
ui.layout --> ui.components
ui.layout --> analysis.*
ui.layout --> validation.*
ui.layout --> downloads.*
ui.layout --> history.*
core.router --> core.state_manager
history.history_manager --> core.state_manager
```

## 3) Flujo del Router

```text
[Sidebar selection]
      |
      v
 build_routes() -> map label => route_key
      |
      v
 dispatch(state, selected_label, handlers)
      |
      +--> route inexistente? -> error + event(router_error)
      |
      +--> handler faltante? -> error + event(router_missing_handler)
      |
      +--> handler válido -> event(route_change) -> render módulo
```

## 4) Flujo de datos operacional

```text
Carga/Selección documento
   -> Validación de tipo
   -> Vista previa integrada (solo lectura)
   -> Análisis automático (PDF/Excel)
   -> Resultados en panel derecho
   -> Descarga manual opcional (botón)
   -> Registro en historial/logs
```

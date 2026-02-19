from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
from tkinter import BOTH, END, LEFT, RIGHT, Button, Checkbutton, Frame, Label, StringVar, Tk
from tkinter import ttk

from .image_viewer import ImageViewer
from .pdf_viewer import PdfViewer


class DashboardDocumentos:
    """Dashboard visual de documentos importados."""

    def __init__(self, registros: list[dict[str, object]], search_stats: dict[str, object] | None = None) -> None:
        self.registros = registros
        self.filtro_tipo = StringVar(value="TODOS")
        self.filtro_carpeta = StringVar(value="TODOS")
        self.solo_imagenes = StringVar(value="0")
        self.search_stats = search_stats or {}

        self.root = Tk()
        self.root.title("Dashboard de Documentos")

        top = Frame(self.root)
        top.pack(fill=BOTH)

        tipos = sorted({str(r.get("categoria", "Sin clasificar")) for r in registros})
        carpetas = sorted({str(r.get("carpeta", "")) for r in registros})
        ttk.Combobox(top, textvariable=self.filtro_tipo, values=["TODOS", *tipos], state="readonly").pack(side=LEFT)
        ttk.Combobox(top, textvariable=self.filtro_carpeta, values=["TODOS", *carpetas], state="readonly").pack(side=LEFT)
        Checkbutton(top, text="Solo imágenes", variable=self.solo_imagenes, onvalue="1", offvalue="0").pack(side=LEFT)
        Button(top, text="Aplicar filtros", command=self._render_rows).pack(side=LEFT)
        Button(top, text="Abrir imagen", command=self._abrir_imagen).pack(side=RIGHT)
        Button(top, text="Abrir PDF", command=self._abrir_pdf).pack(side=RIGHT)

        self.tree = ttk.Treeview(
            self.root,
            columns=("vista", "nombre", "tipo", "carpeta", "modulo", "etiquetas"),
            show="headings",
            height=20,
        )
        for key, title in [
            ("vista", "Vista previa"),
            ("nombre", "Nombre"),
            ("tipo", "Tipo"),
            ("carpeta", "Carpeta"),
            ("modulo", "Módulo asignado"),
            ("etiquetas", "Etiquetas"),
        ]:
            self.tree.heading(key, text=title)
            self.tree.column(key, width=110 if key == "vista" else 220)
        self.tree.pack(fill=BOTH, expand=True)

        self.stats = Label(self.root, justify=LEFT)
        self.stats.pack(fill=BOTH)

        self.stats_analitica = Label(self.root, justify=LEFT)
        self.stats_analitica.pack(fill=BOTH)

        self.stats_busqueda = Label(self.root, justify=LEFT)
        self.stats_busqueda.pack(fill=BOTH)

        self._render_rows()
        self._render_search_panel()

    def _filtrados(self) -> list[dict[str, object]]:
        out = self.registros
        if self.filtro_tipo.get() != "TODOS":
            out = [r for r in out if str(r.get("categoria", "")) == self.filtro_tipo.get()]
        if self.filtro_carpeta.get() != "TODOS":
            out = [r for r in out if str(r.get("carpeta", "")) == self.filtro_carpeta.get()]
        if self.solo_imagenes.get() == "1":
            out = [r for r in out if str(r.get("extension", "")).lower() in {".jpg", ".jpeg", ".png"}]
        return out

    def _render_rows(self) -> None:
        for row in self.tree.get_children():
            self.tree.delete(row)

        rows = self._filtrados()
        for item in rows:
            etiquetas = item.get("etiquetas", [])
            etiquetas_lista = etiquetas if isinstance(etiquetas, list) else []
            self.tree.insert(
                "",
                END,
                values=(
                    "🖼" if str(item.get("extension", "")).lower() in {".jpg", ".jpeg", ".png"} else "",
                    item.get("nombre_archivo", ""),
                    item.get("categoria", ""),
                    item.get("carpeta", ""),
                    item.get("modulo_asignado", ""),
                    ", ".join(str(x) for x in etiquetas_lista),
                ),
                tags=(str(item.get("ruta_completa", "")),),
            )

        tipo_counter = Counter(str(r.get("categoria", "")) for r in rows)
        carpeta_counter = Counter(str(r.get("carpeta", "")) for r in rows)
        imagenes = [r for r in rows if str(r.get("extension", "")).lower() in {".jpg", ".jpeg", ".png"}]
        carpetas_img = Counter(str(r.get("carpeta", "")) for r in imagenes)
        ext_img = Counter(str(r.get("extension", "")).lower() for r in imagenes)
        stats_lines = [
            f"Total de archivos: {len(rows)}",
            "Total por tipo: " + ", ".join(f"{k}={v}" for k, v in tipo_counter.items()),
            "Total por carpeta: " + ", ".join(f"{k}={v}" for k, v in carpeta_counter.items()),
            f"Total de imágenes: {len(imagenes)}",
            "Imágenes por carpeta: " + ", ".join(f"{k}={v}" for k, v in carpetas_img.items()),
            "Imágenes por extensión: " + ", ".join(f"{k}={v}" for k, v in ext_img.items()),
        ]
        self.stats.config(text="\n".join(stats_lines))

        proveedores = Counter(str(r.get("proveedor_virtual", "SIN_PROVEEDOR")) for r in rows)
        hospitales = Counter(str(r.get("hospital_virtual", "SIN_HOSPITAL")) for r in rows)
        meses = Counter(str(r.get("mes_virtual", "SIN_MES")) for r in rows)
        analitica_lines = [
            "Analítica documental",
            "Top proveedores: " + ", ".join(f"{k}={v}" for k, v in proveedores.most_common(5)),
            "Top hospitales: " + ", ".join(f"{k}={v}" for k, v in hospitales.most_common(5)),
            "Serie temporal (mes): " + ", ".join(f"{k}={v}" for k, v in meses.most_common(12)),
        ]
        self.stats_analitica.config(text="\n".join(analitica_lines))

    def _render_search_panel(self) -> None:
        terminos = self.search_stats.get("terminos_mas_buscados", {}) if isinstance(self.search_stats, dict) else {}
        tipos = self.search_stats.get("tipos_mas_encontrados", {}) if isinstance(self.search_stats, dict) else {}
        carpetas = self.search_stats.get("carpetas_mas_relevantes", {}) if isinstance(self.search_stats, dict) else {}

        def _fmt(data: object) -> str:
            if isinstance(data, dict) and data:
                return ", ".join(f"{k}={v}" for k, v in data.items())
            return "sin datos"

        lines = [
            "Búsqueda avanzada",
            f"Términos más buscados: {_fmt(terminos)}",
            f"Tipos más encontrados: {_fmt(tipos)}",
            f"Carpetas más relevantes: {_fmt(carpetas)}",
        ]
        self.stats_busqueda.config(text="\n".join(lines))

    def _get_selected_path(self) -> Path | None:
        selected = self.tree.selection()
        if not selected:
            return None
        tag = self.tree.item(selected[0], "tags")
        if not tag:
            return None
        return Path(tag[0])

    def _abrir_imagen(self) -> None:
        path = self._get_selected_path()
        if path and path.suffix.lower() in {".jpg", ".jpeg", ".png"}:
            ImageViewer(path.parent).run()

    def _abrir_pdf(self) -> None:
        path = self._get_selected_path()
        if path and path.suffix.lower() == ".pdf":
            PdfViewer(path).run()

    def run(self) -> None:
        self.root.mainloop()


def cargar_search_stats(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}

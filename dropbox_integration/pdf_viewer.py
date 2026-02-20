from __future__ import annotations

from pathlib import Path
from tkinter import BOTH, LEFT, RIGHT, Button, Frame, Label, Tk, filedialog

try:
    import pymupdf as fitz  # type: ignore
except Exception:
    fitz = None

try:
    from PIL import Image, ImageTk
except Exception:
    Image = None
    ImageTk = None


class PdfViewer:
    """Visor PDF básico con navegación/zoom y exportación de página."""

    def __init__(self, pdf_path: Path | str) -> None:
        self.pdf_path = Path(pdf_path)
        self.page_index = 0
        self.zoom = 1.5
        self.root = Tk()
        self.root.title(f"Visor PDF - {self.pdf_path.name}")

        self.image_label = Label(self.root)
        self.image_label.pack(fill=BOTH, expand=True)
        self.meta_label = Label(self.root)
        self.meta_label.pack(fill=BOTH)

        controls = Frame(self.root)
        controls.pack(fill=BOTH)
        Button(controls, text="Anterior", command=self.prev_page).pack(side=LEFT)
        Button(controls, text="Siguiente", command=self.next_page).pack(side=LEFT)
        Button(controls, text="Zoom +", command=self.zoom_in).pack(side=LEFT)
        Button(controls, text="Zoom -", command=self.zoom_out).pack(side=LEFT)
        Button(controls, text="Exportar página", command=self.export_page).pack(side=RIGHT)

        if fitz is None:
            raise RuntimeError("PyMuPDF (fitz) no está disponible en el entorno.")
        assert fitz is not None
        self.doc = fitz.open(self.pdf_path)

    def _render(self) -> None:
        if Image is None or ImageTk is None:
            self.meta_label.config(text="Pillow no disponible para renderizar el PDF.")
            return
        assert fitz is not None
        page = self.doc.load_page(self.page_index)
        pix = page.get_pixmap(matrix=fitz.Matrix(self.zoom, self.zoom), alpha=False)
        image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        tk_img = ImageTk.PhotoImage(image)
        self.image_label.config(image=tk_img)
        setattr(self.image_label, "image_ref", tk_img)
        self.meta_label.config(text=f"Página {self.page_index + 1}/{self.doc.page_count} | Zoom {self.zoom:.1f}x")

    def next_page(self) -> None:
        if self.page_index < self.doc.page_count - 1:
            self.page_index += 1
            self._render()

    def prev_page(self) -> None:
        if self.page_index > 0:
            self.page_index -= 1
            self._render()

    def zoom_in(self) -> None:
        self.zoom = min(self.zoom + 0.2, 4.0)
        self._render()

    def zoom_out(self) -> None:
        self.zoom = max(self.zoom - 0.2, 0.6)
        self._render()

    def export_page(self) -> None:
        assert fitz is not None
        page = self.doc.load_page(self.page_index)
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
        out = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png")])
        if out:
            pix.save(out)

    def run(self) -> None:
        self._render()
        self.root.mainloop()

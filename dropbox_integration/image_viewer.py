from __future__ import annotations

from pathlib import Path
from tkinter import BOTH, LEFT, RIGHT, Button, Frame, Label, Tk
from typing import Any

import numpy as np
import streamlit as st

try:
    import cv2  # type: ignore
except Exception:
    cv2 = None

try:
    from PIL import Image, ImageTk
except Exception:
    Image = None
    ImageTk = None

VALID_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def cargar_imagen(ruta: Path | str) -> tuple[Any, dict[str, Any]]:
    """Carga imagen JPG/PNG y retorna PIL image + metadatos base."""
    path = Path(ruta)
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"Archivo de imagen no encontrado: {path}")
    if path.suffix.lower() not in VALID_IMAGE_EXTENSIONS:
        raise ValueError(f"Formato no soportado para visor de imágenes: {path.suffix}")
    if Image is None:
        raise RuntimeError("Pillow no está instalado en el entorno.")

    try:
        imagen = Image.open(path)
        imagen.load()
    except Exception as error:
        raise RuntimeError(f"No se pudo abrir la imagen (corrupta/permisos): {error}") from error

    info = {
        "nombre": path.name,
        "ruta": str(path),
        "carpeta_origen": path.parent.name,
        "extension": path.suffix.lower(),
        "size_bytes": path.stat().st_size,
    }
    return imagen, info


def obtener_info_imagen(imagen: Any, size_bytes: int = 0) -> dict[str, Any]:
    """Obtiene resolución, tamaño, modo y formato de una imagen PIL."""
    width, height = imagen.size
    kb = size_bytes / 1024 if size_bytes else 0
    mb = kb / 1024 if kb else 0
    return {
        "width": width,
        "height": height,
        "resolucion": f"{width}x{height}",
        "size_bytes": size_bytes,
        "size_kb": kb,
        "size_mb": mb,
        "modo": str(imagen.mode),
        "formato": str(imagen.format or "unknown").upper(),
    }


def generar_thumbnail(imagen: Any, tamaño: tuple[int, int] = (300, 300)) -> Any:
    """Genera thumbnail preservando proporción."""
    thumb = imagen.copy()
    thumb.thumbnail(tamaño)
    return thumb


def aplicar_zoom_rotacion(imagen: Any, zoom: float = 1.0, rotacion: int = 0) -> Any:
    """Aplica zoom y rotación a imagen PIL para vista previa en Streamlit."""
    out = imagen.copy()
    if rotacion:
        out = out.rotate(rotacion, expand=True)
    zoom = max(0.1, zoom)
    if zoom != 1.0:
        new_w = max(1, int(out.width * zoom))
        new_h = max(1, int(out.height * zoom))
        out = out.resize((new_w, new_h))
    return out


def cargar_imagen_cv2(ruta: Path | str) -> np.ndarray | None:
    """Carga imagen con OpenCV (opcional) y devuelve ndarray BGR."""
    if cv2 is None:
        return None
    return cv2.imread(str(Path(ruta)))


def mostrar_en_streamlit(ruta: Path | str, zoom: float = 1.0, rotacion: int = 0) -> None:
    """Renderiza imagen + thumbnail + metadatos en Streamlit."""
    imagen, base = cargar_imagen(ruta)
    info = obtener_info_imagen(imagen, int(base["size_bytes"]))
    thumb = generar_thumbnail(imagen)
    vista = aplicar_zoom_rotacion(imagen, zoom=zoom, rotacion=rotacion)

    st.image(vista, caption=f"{base['nombre']} (zoom={zoom:.1f}x, rotación={rotacion}°)", use_container_width=True)
    st.image(thumb, caption="Thumbnail", width=220)
    st.write(
        {
            "resolucion": info["resolucion"],
            "modo": info["modo"],
            "formato": info["formato"],
            "tamaño_kb": round(info["size_kb"], 2),
            "tamaño_mb": round(info["size_mb"], 4),
            "carpeta_origen": base["carpeta_origen"],
            "ruta": base["ruta"],
        }
    )


class ImageViewer:
    """Visor local (Tkinter) de JPG/PNG con navegación."""

    def __init__(self, image_dir: Path | str) -> None:
        self.image_dir = Path(image_dir)
        self.images = sorted([p for p in self.image_dir.rglob("*") if p.is_file() and p.suffix.lower() in VALID_IMAGE_EXTENSIONS])
        self.index = 0
        self.root = Tk()
        self.root.title("Visor de Imágenes")
        self.image_label = Label(self.root)
        self.image_label.pack(fill=BOTH, expand=True)
        self.meta_label = Label(self.root, justify=LEFT)
        self.meta_label.pack(fill=BOTH)

        controls = Frame(self.root)
        controls.pack(fill=BOTH)
        Button(controls, text="Anterior", command=self.prev_image).pack(side=LEFT)
        Button(controls, text="Siguiente", command=self.next_image).pack(side=RIGHT)

    def _render_current(self) -> None:
        if not self.images:
            self.meta_label.config(text="No hay imágenes en la carpeta.")
            return
        path = self.images[self.index]
        if Image is None or ImageTk is None:
            self.meta_label.config(text=f"Pillow no disponible. Archivo: {path.name}")
            return

        img, base = cargar_imagen(path)
        width, height = img.size
        img.thumbnail((1200, 800))
        tk_img = ImageTk.PhotoImage(img)
        self.image_label.config(image=tk_img)
        setattr(self.image_label, "image_ref", tk_img)

        size_bytes = int(base["size_bytes"])
        self.meta_label.config(
            text=f"Nombre: {path.name} | Resolución: {width}x{height} | Tamaño: {size_bytes} bytes | {self.index + 1}/{len(self.images)}"
        )

    def next_image(self) -> None:
        if not self.images:
            return
        self.index = (self.index + 1) % len(self.images)
        self._render_current()

    def prev_image(self) -> None:
        if not self.images:
            return
        self.index = (self.index - 1) % len(self.images)
        self._render_current()

    def run(self) -> None:
        self._render_current()
        self.root.mainloop()

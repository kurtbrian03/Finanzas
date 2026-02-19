from __future__ import annotations

import argparse
import re
from datetime import date
from pathlib import Path

DOCS_DIR = Path(__file__).resolve().parents[1]
MASTER_FILE = DOCS_DIR / "ARCHIVO_MAESTRO_DOCUMENTACION_OPCION_C.txt"
CHANGELOG_FILE = DOCS_DIR / "CHANGELOG_DOCUMENTACION.md"

TARGET_FILES = {
    "pdf": DOCS_DIR / "pdf" / "DOCUMENTACION_INTERNA.pdf.txt",
    "markdown": DOCS_DIR / "markdown" / "README_GITHUB.md",
    "html": DOCS_DIR / "html" / "DOCUMENTACION_WEB.html",
    "latex": DOCS_DIR / "latex" / "DOCUMENTACION_LATEX.tex",
    "notion": DOCS_DIR / "notion" / "NOTION_PAGE.json",
    "confluence": DOCS_DIR / "confluence" / "DOCUMENTACION_CONFLUENCE.wiki",
    "epub": DOCS_DIR / "epub" / "EPUB_Text" / "document.xhtml",
}

SECTION_MAP = {
    "pdf": "SECCIÓN 2",
    "markdown": "SECCIÓN 3",
    "html": "SECCIÓN 4",
    "latex": "SECCIÓN 5",
    "epub": "SECCIÓN 6",
    "notion": "SECCIÓN 7",
    "confluence": "SECCIÓN 8",
}


def extract_section(master_text: str, section_label: str) -> str:
    escaped = re.escape(section_label)
    pattern = rf"{escaped}[\s\S]*?(?=\n\n#####################################################################\n\nSECCIÓN \d|\n\n=====================================================================\nFIN DEL ARCHIVO MAESTRO|$)"
    match = re.search(pattern, master_text)
    if not match:
        return ""
    return match.group(0).strip() + "\n"


def render_output(target: str, master_text: str) -> str:
    section = extract_section(master_text, SECTION_MAP[target])
    if not section:
        section = f"{SECTION_MAP[target]} no encontrada en archivo maestro.\n"

    header = (
        f"# AUTO-GENERADO ({target})\n"
        "# Fuente maestra: ../ARCHIVO_MAESTRO_DOCUMENTACION_OPCION_C.txt\n"
        "# Portal: ../INDEX_DOCUMENTACION.md\n\n"
    )

    if target == "html":
        return (
            "<!DOCTYPE html>\n"
            "<html><head><meta charset=\"UTF-8\"><title>Documentación Web</title></head><body>\n"
            "<h1>Documentación del Sistema</h1>\n"
            "<p>Portal documental: ../INDEX_DOCUMENTACION.md</p>\n"
            f"<pre>{section}</pre>\n"
            "</body></html>\n"
        )

    if target == "latex":
        safe_section = section.replace("\\", "\\\\")
        return (
            "\\documentclass{article}\n"
            "\\usepackage[utf8]{inputenc}\n"
            "\\begin{document}\n"
            "Portal documental: ../INDEX_DOCUMENTACION.md\\\\\n"
            "\\begin{verbatim}\n"
            f"{safe_section}"
            "\\end{verbatim}\n"
            "\\end{document}\n"
        )

    if target == "notion":
        notion_body = section.replace('"', "'").replace("\n", " ").strip()
        return (
            "["
            "{\"type\":\"heading_1\",\"text\":\"Documentación del Sistema\"},"
            "{\"type\":\"paragraph\",\"text\":\"Portal: ../INDEX_DOCUMENTACION.md\"},"
            f"{{\"type\":\"paragraph\",\"text\":\"{notion_body}\"}}"
            "]\n"
        )

    if target == "confluence":
        return (
            "h1. Documentación del Sistema\n"
            "Portal documental: ../INDEX_DOCUMENTACION.md\n\n"
            f"{section}"
        )

    if target == "epub":
        return (
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
            "<html xmlns=\"http://www.w3.org/1999/xhtml\">"
            "<head><title>Documentación</title></head><body>"
            "<h1>Documentación del Sistema</h1>"
            "<p>Portal: ../INDEX_DOCUMENTACION.md</p>"
            f"<pre>{section}</pre>"
            "</body></html>\n"
        )

    return header + section


def write_target(target: str, master_text: str) -> None:
    path = TARGET_FILES[target]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_output(target, master_text), encoding="utf-8")


def validate_targets(selected: list[str]) -> tuple[bool, list[str]]:
    missing = [str(TARGET_FILES[name]) for name in selected if not TARGET_FILES[name].exists()]
    return (len(missing) == 0, missing)


def append_changelog(message: str) -> None:
    header = f"\n\n## [auto-{date.today().isoformat()}] — {date.today().isoformat()}\n### Changed\n- {message}\n"
    CHANGELOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not CHANGELOG_FILE.exists():
        CHANGELOG_FILE.write_text("# Changelog de Documentación\n", encoding="utf-8")
    with CHANGELOG_FILE.open("a", encoding="utf-8") as file:
        file.write(header)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Regenera artefactos documentales desde plantilla maestra.")
    parser.add_argument(
        "--target",
        default="all",
        choices=["all", *TARGET_FILES.keys()],
        help="Formato a regenerar o 'all' para regenerar todo.",
    )
    parser.add_argument("--validate", action="store_true", help="Valida que los archivos objetivo existan.")
    parser.add_argument("--log", type=str, default="", help="Mensaje para registrar en changelog documental.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if not MASTER_FILE.exists():
        raise FileNotFoundError(f"No se encontró el maestro requerido: {MASTER_FILE}")

    master_text = MASTER_FILE.read_text(encoding="utf-8")

    selected = list(TARGET_FILES.keys()) if args.target == "all" else [args.target]

    for name in selected:
        write_target(name, master_text)

    if args.validate:
        ok, missing = validate_targets(selected)
        if not ok:
            print("Validación fallida. Faltan archivos:")
            for item in missing:
                print(f"- {item}")
            return 1

    if args.log.strip():
        append_changelog(args.log.strip())

    print(f"Regeneración completada para: {', '.join(selected)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

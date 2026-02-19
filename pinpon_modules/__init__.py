"""Módulos funcionales ERP para el ecosistema PINPON."""

from __future__ import annotations

import importlib
from importlib import metadata
from pathlib import Path
import re
from typing import Callable, cast


ERP_MODULE_IMPORTS: dict[str, str] = {
	"erp_compras": "pinpon_modules.compras.ui",
	"erp_ventas": "pinpon_modules.ventas.ui",
	"erp_inventarios": "pinpon_modules.inventarios.ui",
}

MODULE_MAP = ERP_MODULE_IMPORTS.copy()
PROJECT_ROOT = Path(__file__).resolve().parents[1]
PINPON_MODULES_DIR = Path(__file__).resolve().parent
GITMODULES_PATH = PROJECT_ROOT / ".gitmodules"

_loaded_erp_modules: dict[str, Callable[[], None]] = {}


def get_registered_modules() -> dict[str, str]:
	"""Retorna la tabla de módulos ERP registrados por clave de ruta."""
	_discover_all_modules()
	return MODULE_MAP.copy()


def get_loaded_modules() -> dict[str, Callable[[], None]]:
	"""Retorna funciones render ya cargadas dinámicamente."""
	return _loaded_erp_modules.copy()


def _resolve_render_callable(module_key: str, module: object) -> Callable[[], None]:
	suffix = module_key.replace("erp_", "", 1)
	candidate_names = (
		f"render_modulo_{suffix}",
		f"render_{suffix}",
		"render_modulo",
		"render",
	)

	for name in candidate_names:
		candidate = getattr(module, name, None)
		if callable(candidate):
			return cast(Callable[[], None], candidate)

	raise AttributeError(
		f"El módulo '{module_key}' no expone una función render válida. "
		f"Intentos: {', '.join(candidate_names)}"
	)


def load_module(module_key: str) -> Callable[[], None]:
	"""Carga un módulo ERP de forma dinámica y retorna su función render principal."""
	if module_key in _loaded_erp_modules:
		return _loaded_erp_modules[module_key]

	_discover_all_modules()
	import_path = MODULE_MAP.get(module_key)
	if not import_path:
		raise ModuleNotFoundError(f"No hay registro para el módulo ERP: {module_key}")

	module = importlib.import_module(import_path)
	render_callable = _resolve_render_callable(module_key, module)
	_loaded_erp_modules[module_key] = render_callable
	return render_callable


def register_module(module_key: str, import_path: str) -> None:
	"""Registra o actualiza una ruta de importación para un módulo ERP."""
	MODULE_MAP[module_key] = import_path
	_loaded_erp_modules.pop(module_key, None)


def unregister_module(module_key: str) -> None:
	"""Elimina un módulo registrado de forma dinámica sin tocar el mapa base."""
	if module_key in MODULE_MAP and module_key not in ERP_MODULE_IMPORTS:
		MODULE_MAP.pop(module_key, None)
	_loaded_erp_modules.pop(module_key, None)


def _discover_installed_package_modules() -> None:
	"""Auto-detecta paquetes pip `pinpon-modulo-*` y los registra dinámicamente."""
	for dist in metadata.distributions():
		name = (dist.metadata.get("Name") or "").strip().lower().replace("_", "-")
		if not name.startswith("pinpon-modulo-"):
			continue

		suffix = name.replace("pinpon-modulo-", "", 1).replace("-", "_")
		module_key = f"erp_{suffix}"
		import_path = f"pinpon_modulo_{suffix}.ui"
		if module_key not in MODULE_MAP:
			MODULE_MAP[module_key] = import_path


def _discover_git_submodule_modules() -> None:
	"""Detecta módulos ERP declarados como submódulos en .gitmodules."""
	if not GITMODULES_PATH.exists():
		return

	content = GITMODULES_PATH.read_text(encoding="utf-8")
	paths = re.findall(r"path\s*=\s*pinpon_modules/([\w\-]+)", content)

	for folder in paths:
		module_key = f"erp_{folder.replace('-', '_')}"
		import_path = f"pinpon_modules.{folder.replace('-', '_')}.ui"
		if module_key not in MODULE_MAP:
			MODULE_MAP[module_key] = import_path


def _discover_local_folder_modules() -> None:
	"""Detecta módulos ERP locales dentro de pinpon_modules/* con ui.py."""
	if not PINPON_MODULES_DIR.exists():
		return

	for entry in PINPON_MODULES_DIR.iterdir():
		if not entry.is_dir():
			continue
		if entry.name.startswith("__"):
			continue

		ui_path = entry / "ui.py"
		if not ui_path.exists():
			continue

		module_key = f"erp_{entry.name}"
		import_path = f"pinpon_modules.{entry.name}.ui"
		if module_key not in MODULE_MAP:
			MODULE_MAP[module_key] = import_path


def _discover_all_modules() -> None:
	"""Ejecuta todas las estrategias de descubrimiento de módulos ERP."""
	_discover_git_submodule_modules()
	_discover_installed_package_modules()
	_discover_local_folder_modules()


__all__ = [
	"MODULE_MAP",
	"ERP_MODULE_IMPORTS",
	"get_registered_modules",
	"get_loaded_modules",
	"register_module",
	"unregister_module",
	"load_module",
]

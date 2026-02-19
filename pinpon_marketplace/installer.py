from __future__ import annotations

import json
import shutil
import subprocess
import sys
from importlib import metadata
from pathlib import Path
from typing import Any

from pinpon_modules import register_module, unregister_module


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = Path(__file__).resolve().parent / "registry.json"
PINPON_MODULES_DIR = PROJECT_ROOT / "pinpon_modules"


def _load_gitmodules_text() -> str:
    gitmodules = PROJECT_ROOT / ".gitmodules"
    if not gitmodules.exists():
        return ""
    return gitmodules.read_text(encoding="utf-8")


def _is_git_submodule(module_id: str) -> bool:
    module_folder = _module_folder_from_id(module_id)
    submodule_name = f"pinpon_modules/{module_folder}"
    text = _load_gitmodules_text()
    return f"[submodule \"{submodule_name}\"]" in text


def _pip_distribution_name(module_id: str) -> str:
    suffix = module_id.replace("erp_", "", 1).replace("_", "-")
    return f"pinpon-modulo-{suffix}"


def _is_pip_installed(module_id: str) -> bool:
    dist_name = _pip_distribution_name(module_id)
    for dist in metadata.distributions():
        name = (dist.metadata.get("Name") or "").strip().lower().replace("_", "-")
        if name == dist_name:
            return True
    return False


def _module_installation_mode(module_id: str) -> str:
    folder = PINPON_MODULES_DIR / _module_folder_from_id(module_id)

    if folder.exists() and _is_git_submodule(module_id):
        return "submodule"

    if _is_pip_installed(module_id):
        return "pip"

    if folder.exists():
        return "local"

    return "none"


def _module_folder_from_id(module_id: str) -> str:
    return module_id.replace("erp_", "", 1)


def _import_path_from_id(module_id: str) -> str:
    return f"pinpon_modules.{_module_folder_from_id(module_id)}.ui"


def _load_registry() -> list[dict[str, Any]]:
    payload = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    return payload if isinstance(payload, list) else []


def list_available_modules() -> list[dict[str, Any]]:
    modules = []
    for module in _load_registry():
        module_id = str(module.get("id", "")).strip()
        mode = _module_installation_mode(module_id)
        module_copy = dict(module)
        module_copy["installed"] = mode != "none"
        module_copy["installation_mode"] = mode
        module_copy["status"] = {
            "submodule": "Instalado (submódulo Git)",
            "pip": "Instalado (pip)",
            "local": "Instalado (carpeta local)",
            "none": "No instalado",
        }[mode]
        module_copy["can_uninstall"] = mode in {"local", "pip"}
        module_copy["can_update"] = mode in {"local", "pip"}
        modules.append(module_copy)
    return modules


def install_module(module_id: str) -> dict[str, Any]:
    available = {m["id"]: m for m in _load_registry()}
    if module_id not in available:
        raise ValueError(f"Módulo no registrado: {module_id}")

    mode = _module_installation_mode(module_id)
    if mode == "submodule":
        return {"ok": False, "message": f"El módulo {module_id} está instalado como submódulo Git."}
    if mode == "pip":
        return {"ok": False, "message": f"El módulo {module_id} está instalado como paquete pip."}
    if mode == "local":
        return {"ok": False, "message": f"El módulo {module_id} ya está instalado localmente."}

    module_meta = available[module_id]
    target_dir = PINPON_MODULES_DIR / _module_folder_from_id(module_id)

    repo_url = str(module_meta["repo"])
    result = subprocess.run(
        ["git", "clone", repo_url, str(target_dir)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        return {
            "ok": False,
            "message": f"No fue posible clonar {module_id}: {result.stderr.strip() or result.stdout.strip()}",
        }

    register_module(module_id, _import_path_from_id(module_id))
    return {"ok": True, "message": f"Módulo {module_id} instalado correctamente."}


def uninstall_module(module_id: str) -> dict[str, Any]:
    mode = _module_installation_mode(module_id)

    if mode == "submodule":
        return {"ok": False, "message": f"El módulo {module_id} está como submódulo Git y no se desinstala desde marketplace."}

    if mode == "pip":
        package = _pip_distribution_name(module_id)
        result = subprocess.run(
            [sys.executable, "-m", "pip", "uninstall", "-y", package],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return {"ok": False, "message": f"No fue posible desinstalar {module_id} vía pip: {result.stderr.strip() or result.stdout.strip()}"}
        unregister_module(module_id)
        return {"ok": True, "message": f"Módulo {module_id} desinstalado (pip)."}

    target_dir = PINPON_MODULES_DIR / _module_folder_from_id(module_id)

    if not target_dir.exists():
        return {"ok": False, "message": f"El módulo {module_id} no está instalado."}

    shutil.rmtree(target_dir)
    unregister_module(module_id)
    return {"ok": True, "message": f"Módulo {module_id} desinstalado correctamente."}


def update_module(module_id: str) -> dict[str, Any]:
    mode = _module_installation_mode(module_id)

    if mode == "submodule":
        return {"ok": False, "message": f"El módulo {module_id} está como submódulo Git y su actualización se gestiona con git submodule."}

    if mode == "pip":
        package = _pip_distribution_name(module_id)
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", package],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return {"ok": False, "message": f"No fue posible actualizar {module_id} vía pip: {result.stderr.strip() or result.stdout.strip()}"}
        register_module(module_id, _import_path_from_id(module_id))
        return {"ok": True, "message": f"Módulo {module_id} actualizado (pip)."}

    target_dir = PINPON_MODULES_DIR / _module_folder_from_id(module_id)

    if not target_dir.exists():
        return {"ok": False, "message": f"El módulo {module_id} no está instalado."}

    result = subprocess.run(
        ["git", "-C", str(target_dir), "pull", "--ff-only"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        return {
            "ok": False,
            "message": f"No fue posible actualizar {module_id}: {result.stderr.strip() or result.stdout.strip()}",
        }

    register_module(module_id, _import_path_from_id(module_id))
    return {"ok": True, "message": f"Módulo {module_id} actualizado correctamente."}

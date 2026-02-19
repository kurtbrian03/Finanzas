def simulate_router(title: str, rules: dict):
    """
    Simula el comportamiento del router de plantillas por título.
    Devuelve el nombre de la plantilla sugerida.
    """
    title_lower = title.lower()
    for key, template in rules.items():
        if key.lower() in title_lower:
            return template
    return "general"


def test_router_basic_mapping():
    rules = {
        "ci": "ci_cd.md",
        "marketplace": "marketplace.md",
        "loader": "loader.md",
        "submodule": "submodule.md",
        "pip": "pip_module.md",
        "erp": "erp_module.md",
    }

    assert simulate_router("CI: actualizar workflows", rules) == "ci_cd.md"
    assert simulate_router("marketplace: agregar módulo", rules) == "marketplace.md"
    assert simulate_router("loader: fix dinámico", rules) == "loader.md"
    assert simulate_router("submodule: sync compras", rules) == "submodule.md"
    assert simulate_router("pip: publicar módulo", rules) == "pip_module.md"
    assert simulate_router("ERP: agregar inventarios", rules) == "erp_module.md"


def test_router_case_insensitive():
    rules = {
        "ci": "ci_cd.md",
        "marketplace": "marketplace.md",
    }

    assert simulate_router("Ci: cambios", rules) == "ci_cd.md"
    assert simulate_router("MARKETPLACE update", rules) == "marketplace.md"


def test_router_default_template():
    rules = {
        "ci": "ci_cd.md",
        "marketplace": "marketplace.md",
    }

    assert simulate_router("Refactor general", rules) == "general"

from __future__ import annotations

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AGENT_DIR = PROJECT_ROOT / "agent_pinpon"


def _load_yaml_json(path: Path) -> dict:
    raw = path.read_text(encoding="utf-8")
    return json.loads(raw)


def test_agent_files_exist() -> None:
    required = [
        AGENT_DIR / "agent.yaml",
        AGENT_DIR / "actions.yaml",
        AGENT_DIR / "knowledge.yaml",
        AGENT_DIR / "environment.json",
        AGENT_DIR / "README_AGENT.md",
    ]
    missing = [str(p) for p in required if not p.exists()]
    assert not missing, f"Faltan archivos del agente: {missing}"


def test_agent_yaml_syntax_and_required_fields() -> None:
    payload = _load_yaml_json(AGENT_DIR / "agent.yaml")
    assert "agent" in payload

    agent = payload["agent"]
    required_keys = {
        "name",
        "id",
        "version",
        "description",
        "instructions",
        "capabilities",
        "actions",
        "knowledge",
        "connections",
        "security",
        "context",
    }
    assert required_keys.issubset(set(agent.keys()))

    assert isinstance(agent["instructions"], list)
    assert isinstance(agent["capabilities"], dict)
    assert isinstance(agent["actions"], dict)
    assert isinstance(agent["connections"], dict)


def test_actions_yaml_syntax_and_structure() -> None:
    payload = _load_yaml_json(AGENT_DIR / "actions.yaml")
    assert "actions" in payload

    actions = payload["actions"]
    assert isinstance(actions, list)
    assert actions, "Debe existir al menos una acción"

    for action in actions:
        required = {"name", "description", "method", "inputs", "outputs", "validations", "errors"}
        assert required.issubset(set(action.keys())), f"Acción incompleta: {action}"
        assert isinstance(action["name"], str)
        assert isinstance(action["inputs"], dict)
        assert isinstance(action["outputs"], dict)
        assert isinstance(action["validations"], list)
        assert isinstance(action["errors"], list)


def test_knowledge_yaml_syntax_and_structure() -> None:
    payload = _load_yaml_json(AGENT_DIR / "knowledge.yaml")
    assert "knowledge" in payload

    knowledge = payload["knowledge"]
    assert isinstance(knowledge, dict)
    assert "sources" in knowledge
    assert isinstance(knowledge["sources"], list)

    for source in knowledge["sources"]:
        required = {"id", "type", "path", "indexed", "priority"}
        assert required.issubset(set(source.keys())), f"Fuente de conocimiento incompleta: {source}"


def test_environment_json_structure() -> None:
    payload = json.loads((AGENT_DIR / "environment.json").read_text(encoding="utf-8"))
    required = {
        "PINPON_WORKSPACE",
        "PINPON_AGENT_MODE",
        "PINPON_AGENT_LOG_LEVEL",
        "PINPON_AGENT_ENDPOINT",
    }
    assert required.issubset(set(payload.keys()))


def test_cross_reference_actions_and_agent() -> None:
    agent = _load_yaml_json(AGENT_DIR / "agent.yaml")["agent"]
    actions = _load_yaml_json(AGENT_DIR / "actions.yaml")["actions"]

    declared = set(agent["actions"]["available"])
    implemented = {a["name"] for a in actions}

    assert declared.issubset(implemented), "agent.actions.available contiene acciones no implementadas"

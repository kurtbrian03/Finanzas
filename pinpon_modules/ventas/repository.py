"""Persistencia JSON para el módulo de Ventas."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class VentasRepository:
    ENTITIES = ("clientes", "cotizaciones", "pedidos", "facturas_emitidas", "cobranzas")

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or (Path(__file__).resolve().parent / "ventas_db.json")
        self._ensure_store()

    def _ensure_store(self) -> None:
        if self.db_path.exists():
            return
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._save(
            {
                "clientes": [],
                "cotizaciones": [],
                "pedidos": [],
                "facturas_emitidas": [],
                "cobranzas": [],
                "next_ids": {
                    "clientes": 1,
                    "cotizaciones": 1,
                    "pedidos": 1,
                    "facturas_emitidas": 1,
                    "cobranzas": 1,
                },
            }
        )

    def _assert_entity(self, entity: str) -> None:
        if entity not in self.ENTITIES:
            raise ValueError(f"Entidad no soportada: {entity}")

    def _load(self) -> dict[str, Any]:
        try:
            return json.loads(self.db_path.read_text(encoding="utf-8"))
        except Exception as error:
            raise RuntimeError(f"No fue posible leer el repositorio de ventas: {error}") from error

    def _save(self, data: dict[str, Any]) -> None:
        try:
            self.db_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as error:
            raise RuntimeError(f"No fue posible guardar el repositorio de ventas: {error}") from error

    def _next_id(self, payload: dict[str, Any], entity: str) -> int:
        current = int(payload["next_ids"][entity])
        payload["next_ids"][entity] = current + 1
        return current

    def list_all(self, entity: str) -> list[dict[str, Any]]:
        self._assert_entity(entity)
        payload = self._load()
        return list(payload.get(entity, []))

    def get_by_id(self, entity: str, item_id: int) -> dict[str, Any] | None:
        self._assert_entity(entity)
        payload = self._load()
        for item in payload.get(entity, []):
            if int(item.get("id", 0)) == int(item_id):
                return dict(item)
        return None

    def create(self, entity: str, item: dict[str, Any]) -> dict[str, Any]:
        self._assert_entity(entity)
        payload = self._load()
        record = dict(item)
        record["id"] = self._next_id(payload, entity)
        payload[entity].append(record)
        self._save(payload)
        return record

    def update(self, entity: str, item_id: int, item: dict[str, Any]) -> dict[str, Any] | None:
        self._assert_entity(entity)
        payload = self._load()
        bucket = payload.get(entity, [])
        for idx, current in enumerate(bucket):
            if int(current.get("id", 0)) == int(item_id):
                updated = dict(item)
                updated["id"] = int(item_id)
                bucket[idx] = updated
                self._save(payload)
                return updated
        return None

    def delete(self, entity: str, item_id: int) -> bool:
        self._assert_entity(entity)
        payload = self._load()
        bucket = payload.get(entity, [])
        original_size = len(bucket)
        payload[entity] = [x for x in bucket if int(x.get("id", 0)) != int(item_id)]
        deleted = len(payload[entity]) < original_size
        if deleted:
            self._save(payload)
        return deleted

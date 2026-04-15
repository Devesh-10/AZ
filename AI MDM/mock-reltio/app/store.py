"""
In-memory entity store with JSON persistence.
Loads seed data on startup. Persists to data/store.json.
"""
import json
import time
import uuid
from pathlib import Path
from typing import Iterator

from app.models import Entity, AttributeValue
from app.seed_data import HCPS, HCOS, PRODUCTS

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
STORE_FILE = DATA_DIR / "store.json"


def _new_uri() -> str:
    return f"entities/{uuid.uuid4().hex[:12]}"


def _now_ms() -> int:
    return int(time.time() * 1000)


def _to_attrs(d: dict) -> dict[str, list[AttributeValue]]:
    return {k: [AttributeValue(value=v)] for k, v in d.items() if v is not None}


class EntityStore:
    def __init__(self):
        self._entities: dict[str, Entity] = {}
        self._merged: dict[str, str] = {}  # loserUri -> winnerUri

    def seed_if_empty(self) -> None:
        if self._entities:
            return
        for raw in HCPS:
            self._create("HCP", _to_attrs(raw))
        for raw in HCOS:
            self._create("HCO", _to_attrs(raw))
        for raw in PRODUCTS:
            self._create("Product", _to_attrs(raw))

    def _create(self, type_name: str, attrs: dict[str, list[AttributeValue]]) -> Entity:
        uri = _new_uri()
        now = _now_ms()
        entity = Entity(
            uri=uri,
            type=f"configuration/entityTypes/{type_name}",
            attributes=attrs,
            createdTime=now,
            updatedTime=now,
        )
        self._entities[uri] = entity
        return entity

    def create(self, type_name: str, attrs: dict[str, list[AttributeValue]]) -> Entity:
        return self._create(type_name, attrs)

    def get(self, uri: str) -> Entity | None:
        # follow merge redirects
        while uri in self._merged:
            uri = self._merged[uri]
        return self._entities.get(uri)

    def update(self, uri: str, attrs: dict[str, list[AttributeValue]]) -> Entity | None:
        entity = self.get(uri)
        if not entity:
            return None
        entity.attributes.update(attrs)
        entity.updatedTime = _now_ms()
        return entity

    def delete(self, uri: str) -> bool:
        return self._entities.pop(uri, None) is not None

    def all(self) -> Iterator[Entity]:
        return iter(self._entities.values())

    def by_type(self, type_short: str) -> Iterator[Entity]:
        suffix = f"/{type_short}"
        return (e for e in self._entities.values() if e.type.endswith(suffix))

    def merge(self, winner_uri: str, loser_uri: str) -> Entity | None:
        winner = self.get(winner_uri)
        loser = self.get(loser_uri)
        if not winner or not loser or winner.uri == loser.uri:
            return None
        # merge attributes - winner wins on conflict, loser fills gaps
        for k, v in loser.attributes.items():
            if k not in winner.attributes:
                winner.attributes[k] = v
        winner.updatedTime = _now_ms()
        self._merged[loser.uri] = winner.uri
        del self._entities[loser.uri]
        return winner

    def persist(self) -> None:
        DATA_DIR.mkdir(exist_ok=True)
        STORE_FILE.write_text(
            json.dumps(
                {
                    "entities": {k: v.model_dump() for k, v in self._entities.items()},
                    "merged": self._merged,
                },
                indent=2,
            )
        )

    def load(self) -> bool:
        if not STORE_FILE.exists():
            return False
        data = json.loads(STORE_FILE.read_text())
        self._entities = {k: Entity(**v) for k, v in data["entities"].items()}
        self._merged = data.get("merged", {})
        return True


store = EntityStore()

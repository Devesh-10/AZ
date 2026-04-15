"""
Reltio HTTP client. Same interface for mock and real Reltio.
Real Reltio: set RELTIO_BASE_URL and RELTIO_AUTH_TOKEN.
"""
from typing import Any
import httpx

from app.core.config import get_settings

settings = get_settings()


def _headers() -> dict[str, str]:
    h = {"Content-Type": "application/json"}
    if settings.reltio_auth_token:
        h["Authorization"] = f"Bearer {settings.reltio_auth_token}"
    return h


def _attrs_to_reltio(plain: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    return {k: [{"value": v}] for k, v in plain.items() if v is not None}


def _attrs_from_reltio(reltio_attrs: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    return {k: v[0]["value"] for k, v in reltio_attrs.items() if v}


class ReltioClient:
    def __init__(self, base_url: str | None = None):
        self.base_url = (base_url or settings.reltio_base_url).rstrip("/")
        self._client = httpx.Client(timeout=10.0)

    def _post(self, path: str, body: dict) -> Any:
        r = self._client.post(f"{self.base_url}{path}", json=body, headers=_headers())
        r.raise_for_status()
        return r.json()

    def _get(self, path: str) -> Any:
        r = self._client.get(f"{self.base_url}{path}", headers=_headers())
        r.raise_for_status()
        return r.json()

    # ---------- agent-facing methods (return plain dicts, not Reltio shape) ----------

    def search(self, entity_type: str, query: dict[str, str], max_results: int = 10) -> list[dict]:
        clauses = [f"equals(type,'{entity_type}')"]
        for k, v in query.items():
            clauses.append(f"contains(attributes.{k},'{v}')")
        filter_str = " and ".join(clauses)
        results = self._post("/entities/_search", {"filter": filter_str, "max": max_results})
        return [self._flatten(e) for e in results]

    def match_probe(self, entity_type: str, attributes: dict[str, Any]) -> list[dict]:
        body = {
            "type": f"configuration/entityTypes/{entity_type}",
            "attributes": _attrs_to_reltio(attributes),
        }
        results = self._post("/entities/_matchProbe", body)
        return [
            {
                "uri": m["uri"],
                "matchScore": m["matchScore"],
                "matchRules": m["matchRules"],
                "entity": self._flatten(m["entity"]),
            }
            for m in results
        ]

    def potential_matches(self, uri: str) -> list[dict]:
        results = self._get(f"/{uri}/_potentialMatches")
        return [
            {
                "uri": m["uri"],
                "matchScore": m["matchScore"],
                "matchRules": m["matchRules"],
                "entity": self._flatten(m["entity"]),
            }
            for m in results
        ]

    def create(self, entity_type: str, attributes: dict[str, Any]) -> dict:
        body = {
            "type": f"configuration/entityTypes/{entity_type}",
            "attributes": _attrs_to_reltio(attributes),
        }
        return self._flatten(self._post("/entities", body))

    def get(self, uri: str) -> dict:
        return self._flatten(self._get(f"/{uri}"))

    def merge(self, winner_uri: str, loser_uri: str) -> dict:
        return self._flatten(
            self._post("/entities/_merge", {"winnerUri": winner_uri, "loserUri": loser_uri})
        )

    @staticmethod
    def _flatten(entity: dict) -> dict:
        return {
            "uri": entity["uri"],
            "type": entity["type"].rsplit("/", 1)[-1],
            "attributes": _attrs_from_reltio(entity.get("attributes", {})),
        }


_client_instance: ReltioClient | None = None


def get_client() -> ReltioClient:
    global _client_instance
    if _client_instance is None:
        _client_instance = ReltioClient()
    return _client_instance

"""
Reltio-compatible entity endpoints.
Reference shapes from docs.reltio.com developer-resources.
"""
from fastapi import APIRouter, HTTPException

from app.models import (
    CreateEntityRequest,
    Entity,
    MergeRequest,
    PotentialMatch,
    SearchRequest,
)
from app.matching import find_potential_matches, find_matches_for_payload
from app.store import store

router = APIRouter()


def _short_type(entity_type: str) -> str:
    return entity_type.rsplit("/", 1)[-1]


@router.post("/entities", response_model=Entity)
def create_entity(req: CreateEntityRequest):
    short = _short_type(req.type)
    return store.create(short, req.attributes)


@router.get("/entities/{uri_path:path}", response_model=Entity)
def get_entity(uri_path: str):
    full = uri_path if uri_path.startswith("entities/") else f"entities/{uri_path}"
    entity = store.get(full)
    if not entity:
        raise HTTPException(404, "Entity not found")
    return entity


@router.put("/entities/{uri_path:path}", response_model=Entity)
def update_entity(uri_path: str, req: CreateEntityRequest):
    full = uri_path if uri_path.startswith("entities/") else f"entities/{uri_path}"
    entity = store.update(full, req.attributes)
    if not entity:
        raise HTTPException(404, "Entity not found")
    return entity


@router.post("/entities/_search", response_model=list[Entity])
def search_entities(req: SearchRequest):
    """
    Simplified Reltio filter parser.
    Supports: equals(type,'HCP'), contains(attributes.LastName,'Chen'), and "and"/"or".
    """
    results = list(store.all())
    if req.filter:
        results = _apply_filter(results, req.filter)
    return results[req.offset : req.offset + req.max]


@router.get("/entities/{uri_path:path}/_potentialMatches", response_model=list[PotentialMatch])
def potential_matches(uri_path: str):
    full = uri_path if uri_path.startswith("entities/") else f"entities/{uri_path}"
    entity = store.get(full)
    if not entity:
        raise HTTPException(404, "Entity not found")
    return find_potential_matches(entity)


@router.post("/entities/_matchProbe", response_model=list[PotentialMatch])
def match_probe(req: CreateEntityRequest):
    """
    Non-Reltio convenience: score a hypothetical entity (not yet created) against the store.
    Used by the agent's search-before-create flow.
    """
    short = _short_type(req.type)
    plain_attrs = {k: v[0].value for k, v in req.attributes.items() if v}
    return find_matches_for_payload(short, plain_attrs)


@router.post("/entities/_merge", response_model=Entity)
def merge_entities(req: MergeRequest):
    winner = store.merge(req.winnerUri, req.loserUri)
    if not winner:
        raise HTTPException(400, "Merge failed: invalid URIs or same entity")
    return winner


# ---------- minimal filter parser ----------

def _apply_filter(entities: list[Entity], filter_str: str) -> list[Entity]:
    """
    Tiny subset of Reltio filter syntax.
    Supports tokens joined by ' and ': equals(...) , contains(...) , startsWith(...).
    """
    clauses = [c.strip() for c in filter_str.split(" and ")]
    out = entities
    for clause in clauses:
        out = [e for e in out if _match_clause(e, clause)]
    return out


def _match_clause(entity: Entity, clause: str) -> bool:
    if clause.startswith("equals(") and clause.endswith(")"):
        body = clause[len("equals("):-1]
        path, _, val = body.partition(",")
        return _get_path(entity, path.strip()) == _strip_quotes(val)
    if clause.startswith("contains(") and clause.endswith(")"):
        body = clause[len("contains("):-1]
        path, _, val = body.partition(",")
        v = _get_path(entity, path.strip())
        return v is not None and _strip_quotes(val).lower() in str(v).lower()
    if clause.startswith("startsWith(") and clause.endswith(")"):
        body = clause[len("startsWith("):-1]
        path, _, val = body.partition(",")
        v = _get_path(entity, path.strip())
        return v is not None and str(v).lower().startswith(_strip_quotes(val).lower())
    return False


def _strip_quotes(s: str) -> str:
    s = s.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ("'", '"'):
        return s[1:-1]
    return s


def _get_path(entity: Entity, path: str) -> str | None:
    if path == "type":
        return entity.type.rsplit("/", 1)[-1]
    if path.startswith("attributes."):
        attr = path[len("attributes."):]
        vals = entity.attributes.get(attr)
        if vals:
            return str(vals[0].value)
    return None

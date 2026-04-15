"""
Fuzzy matching for HCP / HCO / Product entities.
Approximates Reltio's match-rule scoring.
"""
from rapidfuzz import fuzz

from app.models import Entity, PotentialMatch
from app.store import store


def _attr(entity: Entity, name: str) -> str | None:
    vals = entity.attributes.get(name)
    if not vals:
        return None
    return str(vals[0].value) if vals[0].value is not None else None


def _short_type(entity: Entity) -> str:
    return entity.type.rsplit("/", 1)[-1]


def _score_hcp(a: Entity, b: Entity) -> tuple[float, list[str]]:
    """Return (score 0-100, list of rules that fired)."""
    rules: list[str] = []
    score = 0.0

    npi_a, npi_b = _attr(a, "NPI"), _attr(b, "NPI")
    if npi_a and npi_b and npi_a == npi_b:
        return 100.0, ["NPI_EXACT"]

    fn_a, fn_b = (_attr(a, "FirstName") or ""), (_attr(b, "FirstName") or "")
    ln_a, ln_b = (_attr(a, "LastName") or ""), (_attr(b, "LastName") or "")
    city_a, city_b = (_attr(a, "City") or ""), (_attr(b, "City") or "")
    state_a, state_b = (_attr(a, "State") or ""), (_attr(b, "State") or "")

    ln_score = fuzz.ratio(ln_a.lower(), ln_b.lower())
    fn_score = fuzz.ratio(fn_a.lower(), fn_b.lower())
    fn_partial = fuzz.partial_ratio(fn_a.lower(), fn_b.lower())

    if ln_score >= 85 and (fn_score >= 70 or fn_partial >= 90):
        score = (ln_score * 0.5) + (max(fn_score, fn_partial) * 0.3)
        rules.append("FUZZY_NAME")
        if city_a.lower() == city_b.lower() and city_a:
            score += 15
            rules.append("CITY_MATCH")
        if state_a == state_b and state_a:
            score += 5
            rules.append("STATE_MATCH")

    return min(score, 99.0), rules


def _score_hco(a: Entity, b: Entity) -> tuple[float, list[str]]:
    rules: list[str] = []
    name_a = (_attr(a, "Name") or "").lower()
    name_b = (_attr(b, "Name") or "").lower()
    city_a = (_attr(a, "City") or "").lower()
    city_b = (_attr(b, "City") or "").lower()

    name_score = fuzz.token_set_ratio(name_a, name_b)
    if name_score >= 70:
        score = name_score * 0.7
        rules.append("FUZZY_NAME")
        if city_a == city_b and city_a:
            score += 25
            rules.append("CITY_MATCH")
        return min(score, 99.0), rules
    return 0.0, []


def _score_product(a: Entity, b: Entity) -> tuple[float, list[str]]:
    name_a = (_attr(a, "Name") or "").lower()
    name_b = (_attr(b, "Name") or "").lower()
    s = fuzz.ratio(name_a, name_b)
    if s >= 80:
        return float(s), ["NAME_FUZZY"]
    return 0.0, []


def _score(a: Entity, b: Entity) -> tuple[float, list[str]]:
    t = _short_type(a)
    if _short_type(b) != t:
        return 0.0, []
    if t == "HCP":
        return _score_hcp(a, b)
    if t == "HCO":
        return _score_hco(a, b)
    if t == "Product":
        return _score_product(a, b)
    return 0.0, []


def find_potential_matches(target: Entity, threshold: float = 60.0) -> list[PotentialMatch]:
    results: list[PotentialMatch] = []
    for candidate in store.all():
        if candidate.uri == target.uri:
            continue
        score, rules = _score(target, candidate)
        if score >= threshold:
            results.append(
                PotentialMatch(
                    uri=candidate.uri,
                    matchScore=round(score, 2),
                    matchRules=rules,
                    entity=candidate,
                )
            )
    results.sort(key=lambda m: m.matchScore, reverse=True)
    return results


def find_matches_for_payload(type_name: str, attrs: dict, threshold: float = 60.0) -> list[PotentialMatch]:
    """Score a hypothetical entity (not yet in store) against all entities."""
    from app.models import AttributeValue, Entity

    probe = Entity(
        uri="probe/temp",
        type=f"configuration/entityTypes/{type_name}",
        attributes={k: [AttributeValue(value=v)] for k, v in attrs.items() if v is not None},
    )
    return find_potential_matches(probe, threshold=threshold)

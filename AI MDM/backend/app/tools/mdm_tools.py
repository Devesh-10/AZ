"""
LangChain tools for the MDM Agent.
Each tool wraps a Reltio API call and returns structured JSON the LLM can reason over.

Governance is enforced by tool ordering in the system prompt:
  - Any create_entity call MUST be preceded by find_potential_duplicates
  - The agent presents candidates and asks for confirmation before creating
"""
import json
from typing import Any

from langchain_core.tools import tool

from app.tools.reltio_client import get_client


@tool
def search_master_data(entity_type: str, attributes: dict[str, str], max_results: int = 10) -> str:
    """
    Search master data by attribute filters. Use this when the user asks to FIND or LOOK UP
    existing entities (e.g. "show me oncologists in Boston", "find Dr. Chen").

    Args:
        entity_type: One of "HCP", "HCO", "Product".
        attributes: Dict of attribute name -> substring to match (case-insensitive contains).
            Examples for HCP: {"LastName": "Chen", "City": "Boston", "Specialty": "Oncology"}
            Examples for HCO: {"Name": "Mass General", "City": "Boston"}
        max_results: Cap on results (default 10).

    Returns:
        JSON list of matching entities with uri, type, attributes.
    """
    client = get_client()
    results = client.search(entity_type, attributes, max_results=max_results)
    return json.dumps({"count": len(results), "results": results}, indent=2)


@tool
def find_potential_duplicates(entity_type: str, attributes: dict[str, Any]) -> str:
    """
    Score a hypothetical new entity against existing master data and return potential duplicates.
    YOU MUST CALL THIS BEFORE create_entity to enforce the search-before-create governance rule.

    Args:
        entity_type: "HCP", "HCO", or "Product".
        attributes: The full attribute set of the entity the user wants to create.
            HCP example: {"FirstName": "Sara", "LastName": "Chen", "City": "Boston",
                          "State": "MA", "Specialty": "Oncology", "NPI": "1234567890"}
            HCO example: {"Name": "Mass General Hospital", "City": "Boston", "State": "MA"}

    Returns:
        JSON list of potential matches with uri, matchScore (0-100), matchRules,
        and the candidate entity. Empty list means no duplicates -> safe to create.
    """
    client = get_client()
    matches = client.match_probe(entity_type, attributes)
    return json.dumps({"count": len(matches), "matches": matches}, indent=2)


@tool
def create_entity(entity_type: str, attributes: dict[str, Any], confirmed_no_duplicate: bool) -> str:
    """
    Create a new master data entity. ONLY call this after:
      1. find_potential_duplicates was called for the same payload, AND
      2. Either no duplicates were returned, OR the user has explicitly confirmed
         they want to create a new entity despite duplicates.

    Args:
        entity_type: "HCP", "HCO", or "Product".
        attributes: Full attribute set for the new entity.
        confirmed_no_duplicate: Set to true ONLY if step 1+2 above are satisfied.
            If false, this tool will refuse the create.

    Returns:
        JSON of the created entity, or an error message if governance was bypassed.
    """
    if not confirmed_no_duplicate:
        return json.dumps({
            "error": "GOVERNANCE_BLOCK",
            "message": "create_entity requires confirmed_no_duplicate=true. "
                       "Run find_potential_duplicates first and present results to the user.",
        })
    client = get_client()
    created = client.create(entity_type, attributes)
    return json.dumps({"status": "created", "entity": created}, indent=2)


@tool
def get_entity(uri: str) -> str:
    """
    Retrieve a single entity by URI (e.g., "entities/abc123").
    Use this when the user references a specific entity from earlier search results.
    """
    client = get_client()
    return json.dumps(client.get(uri), indent=2)


@tool
def merge_entities(winner_uri: str, loser_uri: str) -> str:
    """
    Merge two duplicate entities. The winner is kept; the loser is consolidated into it.
    Use this after the user has confirmed two entities should be merged.

    Args:
        winner_uri: URI of the entity to keep (typically the more complete record).
        loser_uri: URI of the entity to merge into the winner.
    """
    client = get_client()
    merged = client.merge(winner_uri, loser_uri)
    return json.dumps({"status": "merged", "entity": merged}, indent=2)


ALL_TOOLS = [
    search_master_data,
    find_potential_duplicates,
    create_entity,
    get_entity,
    merge_entities,
]

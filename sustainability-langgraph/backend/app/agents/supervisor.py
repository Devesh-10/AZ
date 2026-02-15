"""
Supervisor Agent for Sustainability Insight Agent
Routes queries to appropriate agents using semantic embeddings.
Uses AWS Bedrock Titan embeddings for similarity matching.
"""

import json
import numpy as np
from datetime import datetime
from functools import lru_cache
from langchain_aws import ChatBedrock, BedrockEmbeddings


def cosine_similarity(X, Y):
    """Compute cosine similarity between X and Y using numpy."""
    X_norm = X / np.linalg.norm(X, axis=1, keepdims=True)
    Y_norm = Y / np.linalg.norm(Y, axis=1, keepdims=True)
    return np.dot(X_norm, Y_norm.T)

from app.core.config import get_settings
from app.models.state import SIAState, AgentLog
from app.tools.data_catalogue import KPI_CATALOGUE, FOUNDATION_DATA_PRODUCTS

settings = get_settings()

# Initialize embeddings model (cached)
_embeddings_model = None


def get_embeddings_model():
    """Get or create embeddings model singleton"""
    global _embeddings_model
    if _embeddings_model is None:
        _embeddings_model = BedrockEmbeddings(
            model_id="amazon.titan-embed-text-v2:0",
            region_name=settings.aws_region
        )
    return _embeddings_model


# Pre-computed KPI embeddings cache
_kpi_embeddings_cache = None


def _build_kpi_descriptions() -> dict[str, str]:
    """Build semantic descriptions for each KPI for embedding."""
    descriptions = {}
    for kpi_id, info in KPI_CATALOGUE.items():
        text_parts = [
            info["name"],
            info["description"],
            ", ".join(info["aliases"]),
            " | ".join(info["sample_queries"])
        ]
        descriptions[kpi_id] = " ".join(text_parts)
    return descriptions


def _get_kpi_embeddings() -> tuple[list[str], np.ndarray]:
    """Get or compute KPI embeddings"""
    global _kpi_embeddings_cache

    if _kpi_embeddings_cache is None:
        embeddings_model = get_embeddings_model()
        descriptions = _build_kpi_descriptions()

        kpi_ids = list(descriptions.keys())
        kpi_texts = list(descriptions.values())

        kpi_vectors = embeddings_model.embed_documents(kpi_texts)
        _kpi_embeddings_cache = (kpi_ids, np.array(kpi_vectors))

    return _kpi_embeddings_cache


def _semantic_match_kpi_with_embeddings(query: str) -> tuple[str | None, float]:
    """Hybrid semantic matching using embeddings + keyword boosting."""
    try:
        embeddings_model = get_embeddings_model()
        kpi_ids, kpi_vectors = _get_kpi_embeddings()

        query_vector = embeddings_model.embed_query(query)
        query_vector = np.array(query_vector).reshape(1, -1)

        similarities = cosine_similarity(query_vector, kpi_vectors)[0]

        query_lower = query.lower()
        boosted_scores = []

        for i, kpi_id in enumerate(kpi_ids):
            base_score = similarities[i]
            boost = 0.0

            kpi_info = KPI_CATALOGUE[kpi_id]

            for alias in kpi_info["aliases"]:
                if alias.lower() in query_lower:
                    boost = max(boost, 0.4)
                    break

            if kpi_info["name"].lower() in query_lower:
                boost = max(boost, 0.3)

            for sample in kpi_info["sample_queries"]:
                sample_words = set(sample.lower().split())
                query_words = set(query_lower.split())
                overlap = len(sample_words & query_words) / max(len(sample_words), 1)
                if overlap > 0.5:
                    boost = max(boost, 0.2)

            final_score = min(base_score + boost, 1.0)
            boosted_scores.append(final_score)

        best_idx = np.argmax(boosted_scores)
        best_score = boosted_scores[best_idx]
        best_kpi = kpi_ids[best_idx]

        return best_kpi, float(best_score)

    except Exception as e:
        print(f"Embeddings error: {e}")
        return _fallback_keyword_match(query)


def _fallback_keyword_match(query: str) -> tuple[str | None, float]:
    """Fallback keyword matching if embeddings fail"""
    query_lower = query.lower()
    best_match = None
    best_score = 0.0

    for kpi_id, info in KPI_CATALOGUE.items():
        score = 0.0
        for alias in info["aliases"]:
            if alias.lower() in query_lower:
                score = max(score, 0.7)
        if info["name"].lower() in query_lower:
            score = max(score, 0.6)
        if score > best_score:
            best_score = score
            best_match = kpi_id

    return best_match, best_score


SUPERVISOR_SYSTEM_PROMPT = """You are a Sustainability Insight Agent (SIA) supervisor responsible for routing user queries.

## Your Role
Analyze user queries and route them to the appropriate agent:
1. **KPI** - Simple sustainability KPI lookups (energy, emissions, water, waste, EV fleet)
2. **COMPLEX** - Any question requiring analysis, comparison, or recommendations
3. **CLARIFY** - Query is too vague to understand what the user wants

## Available KPIs (route to KPI agent):
{kpi_list}

## Foundation Data Products (route to COMPLEX/Analyst agent):
{fdp_list}

## IMPORTANT: Route generously to COMPLEX
- If unsure, route to COMPLEX - the Analyst agent can handle unknown queries gracefully
- Only use CLARIFY if the query is genuinely too vague to understand intent

## Sustainability Terminology:
- "emissions" / "carbon" / "CO2" = greenhouse gas emissions
- "energy" / "power" = energy consumption
- "water" = water usage
- "waste" / "recycling" = waste management
- "EV" / "electric vehicles" / "fleet" = EV transition

## Routing Rules:
- Single KPI questions → KPI
- "Why" / "How can we" / analysis questions → COMPLEX
- Genuinely ambiguous → CLARIFY

## Output Format (JSON):
{{
    "route_type": "KPI" | "COMPLEX" | "CLARIFY",
    "route_reason": "Brief explanation",
    "matched_kpi": "kpi_id if KPI route, else null",
    "extracted_filters": {{"site": "...", "year": "...", "quarter": "..."}} or null
}}

Respond ONLY with valid JSON.
"""


def _build_kpi_list() -> str:
    """Build formatted KPI list for prompt"""
    lines = []
    for kpi_id, info in KPI_CATALOGUE.items():
        aliases = ", ".join(info["aliases"])
        lines.append(f"- {kpi_id}: {info['name']} ({aliases})")
    return "\n".join(lines)


def _build_fdp_list() -> str:
    """Build formatted Foundation Data Products list for prompt"""
    lines = []
    for fdp_id, info in FOUNDATION_DATA_PRODUCTS.items():
        samples = "; ".join(info["sample_queries"][:2])
        lines.append(f"- {fdp_id}: {info['name']} - {info['description']} (e.g., {samples})")
    return "\n".join(lines)


def _needs_transactional_data(query: str) -> bool:
    """
    Check if query needs Transactional/Master folder data (route to Analyst).

    Simple routing logic:
    - KPI folder data (summaries) → KPI Agent
    - Master/Transactional folder data (detailed records) → Analyst Agent

    Transactional data includes:
    - fleet_asset_inventory, fleet_asset_type, fleet_fuel_powertrain_type
    - energy_consumption, water_usage, greenhouse_gas_emissions, waste_record
    - fleet_fuel_consumption, fleet_mileage
    """
    query_lower = query.lower()

    # Patterns that indicate need for Transactional/Master data (route to Analyst)
    transactional_patterns = [
        # Fleet asset details (from fleet_asset_inventory, fleet_asset_type, fleet_fuel_powertrain_type)
        "fleet asset", "asset type", "vehicle type", "by vehicle type",
        "powertrain", "by powertrain", "powertrain type",
        "diesel car", "petrol car", "hybrid car", "electric car",
        "diesel count", "petrol count", "hybrid count",
        "car count", "cars count", "vehicle count by",
        "asset count by", "assets by",
        "fuel type", "by fuel type",

        # Grouping/breakdown patterns (needs detailed records)
        "count by", "breakdown by", "grouped by", "group by",
        "by type", "by year and type", "trend by year",

        # Analysis patterns (needs complex joins)
        "why is", "why are", "why did",
        "how can we", "how to improve", "how to reduce",
        "what's causing", "what is causing",
        "recommendations", "suggest", "analyze",
        "compare", "comparison",
        "main contributors", "biggest", "largest",

        # Raw consumption data (from transactional tables)
        "consumption details", "consumption records",
        "usage records", "detailed records"
    ]

    return any(p in query_lower for p in transactional_patterns)


def _is_kpi_summary_query(query: str) -> bool:
    """
    Check if query can be answered from KPI folder summary tables.

    KPI summary tables:
    - energy_monthly_summary, energy_quarterly_summary
    - greenhouse_gas_emissions_monthly_summary, greenhouse_gas_emissions_quarterly_summary
    - water_monthly_summary, waste_monthly_summary
    - electric_vehicle_transition_quarterly_summary (EV totals only)
    """
    query_lower = query.lower()

    # Patterns for KPI summary data
    kpi_patterns = [
        # Total/aggregate queries (from summary tables)
        "total energy", "energy consumption", "energy usage",
        "total emissions", "ghg emissions", "carbon emissions", "scope 1", "scope 2",
        "total water", "water usage", "water consumption",
        "total waste", "waste generated", "recycling",
        "total fleet", "fleet size", "ev count", "electric vehicle count",
        "ev transition rate", "ev percentage",

        # Time-based aggregate queries
        "last year", "this year", "quarterly", "monthly",
        "what was our", "how much"
    ]

    # Also match if asking about data availability
    if "what data" in query_lower or "ev fleet data" in query_lower:
        return True

    return any(p in query_lower for p in kpi_patterns)


def supervisor_agent(state: SIAState) -> dict:
    """
    Supervisor agent that routes queries based on data folder location.

    Simple routing logic:
    - KPI folder data → KPI Agent
    - Master/Transactional folder data → Analyst Agent
    """
    user_query = state["user_query"]

    # FIRST: Check if query needs Transactional/Master data → Route to Analyst
    if _needs_transactional_data(user_query):
        log_entry: AgentLog = {
            "agent_name": "Supervisor",
            "input_summary": user_query[:100],
            "output_summary": "Routed to Analyst agent",
            "reasoning_summary": "Query requires Transactional/Master data (detailed records)",
            "status": "success",
            "timestamp": datetime.now().isoformat()
        }
        return {
            "route_type": "COMPLEX",
            "route_reason": "Query requires Transactional/Master data (detailed records)",
            "matched_kpi": None,
            "extracted_filters": _extract_filters(user_query),
            "agent_logs": [log_entry]
        }

    # Use embeddings for semantic matching
    matched_kpi, confidence = _semantic_match_kpi_with_embeddings(user_query)

    # High confidence match
    if confidence > 0.6 and matched_kpi:
        kpi_name = KPI_CATALOGUE[matched_kpi]['name']
        log_entry: AgentLog = {
            "agent_name": "Supervisor",
            "input_summary": user_query[:100],
            "output_summary": f"Routed to KPI agent for {matched_kpi}",
            "reasoning_summary": f"Semantic match for '{kpi_name}' with {confidence*100:.0f}% confidence",
            "status": "success",
            "timestamp": datetime.now().isoformat()
        }

        return {
            "route_type": "KPI",
            "route_reason": f"Semantic match for {kpi_name} (confidence: {confidence:.2f})",
            "matched_kpi": matched_kpi,
            "extracted_filters": _extract_filters(user_query),
            "agent_logs": [log_entry]
        }

    # Medium confidence - use LLM to verify
    if confidence > 0.4 and matched_kpi:
        llm = ChatBedrock(
            model_id=settings.supervisor_model,
            region_name=settings.aws_region
        )

        from langchain_core.messages import HumanMessage, SystemMessage

        system_prompt = SUPERVISOR_SYSTEM_PROMPT.format(
            kpi_list=_build_kpi_list(),
            fdp_list=_build_fdp_list()
        )

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Route this query: {user_query}")
        ]

        try:
            response = llm.invoke(messages)
            result = json.loads(response.content)

            log_entry: AgentLog = {
                "agent_name": "Supervisor",
                "input_summary": user_query[:100],
                "output_summary": f"Routed to {result.get('route_type')} (LLM verified)",
                "reasoning_summary": result.get("route_reason"),
                "status": "success",
                "timestamp": datetime.now().isoformat()
            }

            return {
                "route_type": result.get("route_type"),
                "route_reason": result.get("route_reason"),
                "matched_kpi": result.get("matched_kpi"),
                "extracted_filters": result.get("extracted_filters") or _extract_filters(user_query),
                "agent_logs": [log_entry]
            }
        except Exception as e:
            kpi_name = KPI_CATALOGUE[matched_kpi]['name']
            log_entry: AgentLog = {
                "agent_name": "Supervisor",
                "input_summary": user_query[:100],
                "output_summary": f"Routed to KPI agent for {matched_kpi}",
                "reasoning_summary": "LLM verification unavailable, using embedding result",
                "status": "success",
                "timestamp": datetime.now().isoformat()
            }

            return {
                "route_type": "KPI",
                "route_reason": f"Embedding match for {kpi_name}",
                "matched_kpi": matched_kpi,
                "extracted_filters": _extract_filters(user_query),
                "agent_logs": [log_entry]
            }

    # Low confidence - use LLM for full routing
    llm = ChatBedrock(
        model_id=settings.supervisor_model,
        region_name=settings.aws_region
    )

    from langchain_core.messages import HumanMessage, SystemMessage

    system_prompt = SUPERVISOR_SYSTEM_PROMPT.format(
        kpi_list=_build_kpi_list(),
        fdp_list=_build_fdp_list()
    )

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Route this query: {user_query}")
    ]

    try:
        response = llm.invoke(messages)
        result = json.loads(response.content)

        log_entry: AgentLog = {
            "agent_name": "Supervisor",
            "input_summary": user_query[:100],
            "output_summary": f"Routed to {result.get('route_type')}",
            "reasoning_summary": result.get("route_reason"),
            "status": "success",
            "timestamp": datetime.now().isoformat()
        }

        return {
            "route_type": result.get("route_type"),
            "route_reason": result.get("route_reason"),
            "matched_kpi": result.get("matched_kpi"),
            "extracted_filters": result.get("extracted_filters") or _extract_filters(user_query),
            "agent_logs": [log_entry]
        }

    except Exception as e:
        log_entry: AgentLog = {
            "agent_name": "Supervisor",
            "input_summary": user_query[:100],
            "output_summary": "Routed to Analyst (fallback)",
            "reasoning_summary": f"Routing error: {str(e)}",
            "status": "error",
            "timestamp": datetime.now().isoformat()
        }

        return {
            "route_type": "COMPLEX",
            "route_reason": "Fallback routing due to error",
            "matched_kpi": None,
            "extracted_filters": _extract_filters(user_query),
            "agent_logs": [log_entry]
        }


def _extract_filters(query: str) -> dict:
    """Extract common filters from query (site, year, quarter)"""
    import re
    from datetime import datetime

    filters = {}
    query_lower = query.lower()

    # Extract year - handle relative expressions first
    current_year = datetime.now().year
    if "last year" in query_lower:
        filters["year"] = current_year - 1
    elif "this year" in query_lower:
        filters["year"] = current_year
    else:
        # Extract explicit year
        year_match = re.search(r'\b(202[0-9])\b', query_lower)
        if year_match:
            filters["year"] = int(year_match.group(1))

    # Extract quarter
    quarter_match = re.search(r'q([1-4])|quarter\s*([1-4])', query_lower)
    if quarter_match:
        filters["quarter"] = int(quarter_match.group(1) or quarter_match.group(2))

    # Extract site - use word boundaries to avoid matching inside words
    site_patterns = [
        (r'\bmacclesfield\b', "Macclesfield"),
        (r'\bgaithersburg\b', "Gaithersburg"),
        (r'\bsodertalje\b', "Sodertalje"),
        (r'\buk\b', "UK"),
        (r'\bus\b', "US"),
        (r'\busa\b', "USA"),
        (r'\bsweden\b', "Sweden"),
    ]
    for pattern, site_name in site_patterns:
        if re.search(pattern, query_lower):
            filters["site"] = site_name
            break

    # Extract market/region - use word boundaries
    region_patterns = [
        (r'\beurope\b', "Europe"),
        (r'\bamericas\b', "Americas"),
        (r'\basia\b', "Asia"),
        (r'\bapac\b', "APAC"),
    ]
    for pattern, region_name in region_patterns:
        if re.search(pattern, query_lower):
            filters["market"] = region_name
            break

    return filters if filters else None

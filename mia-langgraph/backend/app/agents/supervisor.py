"""
Supervisor Agent for MIA
Routes queries to appropriate agents using semantic embeddings.
Uses AWS Bedrock Titan embeddings for similarity matching.
"""

import json
import numpy as np
from datetime import datetime
from functools import lru_cache
from langchain_aws import ChatBedrock, BedrockEmbeddings


def cosine_similarity(X, Y):
    """Compute cosine similarity between X and Y using numpy (no sklearn dependency)."""
    # Normalize vectors
    X_norm = X / np.linalg.norm(X, axis=1, keepdims=True)
    Y_norm = Y / np.linalg.norm(Y, axis=1, keepdims=True)
    # Compute cosine similarity
    return np.dot(X_norm, Y_norm.T)

from app.core.config import get_settings
from app.models.state import MIAState, AgentLog
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
    """
    Build semantic descriptions for each KPI for embedding.

    IMPORTANT: Only include user-facing semantic content, NOT:
    - Table names (KPI_STORE_WEEKLY, etc.)
    - Column names (batch_yield_avg_pct, etc.)
    - Technical schema details

    This ensures embeddings capture what users ASK about, not how data is stored.
    """
    descriptions = {}
    for kpi_id, info in KPI_CATALOGUE.items():
        # Only semantic content - what users might say/ask
        text_parts = [
            info["name"],                    # "Batch Yield"
            info["description"],             # User-friendly description
            ", ".join(info["aliases"]),      # Alternative names users might use
            " | ".join(info["sample_queries"])  # Example questions
        ]
        # Explicitly exclude: table, unit, target, column names
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

        # Generate embeddings for all KPIs
        kpi_vectors = embeddings_model.embed_documents(kpi_texts)
        _kpi_embeddings_cache = (kpi_ids, np.array(kpi_vectors))

    return _kpi_embeddings_cache


def _semantic_match_kpi_with_embeddings(query: str) -> tuple[str | None, float]:
    """
    Hybrid semantic matching using embeddings + keyword boosting.
    Returns (kpi_id, confidence_score)
    """
    try:
        embeddings_model = get_embeddings_model()
        kpi_ids, kpi_vectors = _get_kpi_embeddings()

        # Embed the query
        query_vector = embeddings_model.embed_query(query)
        query_vector = np.array(query_vector).reshape(1, -1)

        # Calculate cosine similarity
        similarities = cosine_similarity(query_vector, kpi_vectors)[0]

        # Hybrid scoring: boost embedding score with keyword matches
        query_lower = query.lower()
        boosted_scores = []

        for i, kpi_id in enumerate(kpi_ids):
            base_score = similarities[i]
            boost = 0.0

            kpi_info = KPI_CATALOGUE[kpi_id]

            # Boost for alias matches (strong signal)
            for alias in kpi_info["aliases"]:
                if alias.lower() in query_lower:
                    boost = max(boost, 0.4)
                    break

            # Boost for name match
            if kpi_info["name"].lower() in query_lower:
                boost = max(boost, 0.3)

            # Boost for sample query word overlap
            for sample in kpi_info["sample_queries"]:
                sample_words = set(sample.lower().split())
                query_words = set(query_lower.split())
                overlap = len(sample_words & query_words) / max(len(sample_words), 1)
                if overlap > 0.5:
                    boost = max(boost, 0.2)

            # Combine: embedding score + boost, capped at 1.0
            final_score = min(base_score + boost, 1.0)
            boosted_scores.append(final_score)

        # Find best match
        best_idx = np.argmax(boosted_scores)
        best_score = boosted_scores[best_idx]
        best_kpi = kpi_ids[best_idx]

        return best_kpi, float(best_score)

    except Exception as e:
        print(f"Embeddings error: {e}")
        # Fallback to keyword matching
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


# System prompt for LLM routing (used when embeddings confidence is low)
SUPERVISOR_SYSTEM_PROMPT = """You are a Manufacturing Insight Agent (MIA) supervisor responsible for routing user queries.

## Your Role
Analyze user queries and route them to the appropriate agent:
1. **KPI** - Simple KPI lookups from pre-computed data (yield, RFT, OEE, cycle time, etc.)
2. **COMPLEX** - Multi-step analysis requiring deep reasoning, comparisons, trend analysis, or joining multiple data sources
3. **CLARIFY** - Query is ambiguous and needs clarification
4. **REJECT** - Query is outside manufacturing domain or inappropriate

## Available KPIs (route to KPI agent):
{kpi_list}

## Foundation Data Products (route to COMPLEX/Analyst agent):
{fdp_list}

## Routing Rules:
- Single KPI questions (e.g., "What is the batch yield?") → KPI
- Questions about trends, comparisons, root causes → COMPLEX
- Questions about orders, batches, deviations → COMPLEX
- Ambiguous queries without clear intent → CLARIFY
- Non-manufacturing questions → REJECT

## Output Format (JSON):
{{
    "route_type": "KPI" | "COMPLEX" | "CLARIFY" | "REJECT",
    "route_reason": "Brief explanation",
    "matched_kpi": "kpi_id if KPI route, else null",
    "extracted_filters": {{"sku": "...", "site": "...", "time_period": "..."}} or null
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


def _is_complex_query(query: str) -> bool:
    """Check if query requires complex analysis that cannot be answered with simple SQL"""
    query_lower = query.lower()

    # Questions asking for recommendations, improvements, or root cause analysis
    analysis_indicators = [
        "how can we improve", "how to improve", "how do we improve",
        "why is", "why are", "why did",
        "root cause", "reason for", "reasons for",
        "what's causing", "what is causing",
        "recommendations", "suggest", "advice",
        "should we", "what should",
        "do you think", "will there be risk",  # Predictive/opinion questions
    ]

    # Multi-KPI or comparison queries
    comparison_indicators = [
        "compare", "comparison", "versus", "vs",
        "correlation", "relationship",
        "all kpis", "multiple kpis",
    ]

    # Transaction-level data queries (not pre-aggregated KPIs)
    transaction_indicators = [
        "orders", "quarantine", "release",
        "predict", "forecast",
        "batch b", "batch id", "order id",  # Specific batch/order queries
        "waiting time", "wait time",  # Process timing queries
        "by order", "per order",  # Order-level breakdown
        "mlt", "manufacturing lead time",  # MLT queries need order data
        "scheduled", "finished",  # Order scheduling queries
        "packing orders", "formulation orders",  # Order-type queries
    ]

    # Dimensions not available in KPI tables (require COMPLEX routing)
    unsupported_dimensions = [
        "by brand", "by market", "china market", "china",
        "by region", "by country", "by customer",
    ]

    # Check for batch ID patterns (e.g., B2025-00007)
    import re
    has_batch_id = bool(re.search(r'b\d{4}-\d+', query_lower))

    all_indicators = analysis_indicators + comparison_indicators + transaction_indicators + unsupported_dimensions
    return any(indicator in query_lower for indicator in all_indicators) or has_batch_id


def supervisor_agent(state: MIAState) -> dict:
    """
    Supervisor agent that routes queries using semantic embeddings.

    Args:
        state: Current MIA state with user query

    Returns:
        Updated state with routing decision
    """
    user_query = state["user_query"]

    # Check if this is clearly a complex query
    if _is_complex_query(user_query):
        log_entry = AgentLog(
            agent_name="Supervisor",
            input_summary=user_query[:100],
            output_summary="Routed to Analyst agent",
            reasoning_summary="Query requires complex analysis",
            status="success",
            timestamp=datetime.now().isoformat()
        )
        return {
            "route_type": "COMPLEX",
            "route_reason": "Query requires multi-step analysis or comparison",
            "matched_kpi": None,
            "extracted_filters": _extract_filters(user_query),
            "agent_logs": [log_entry]
        }

    # Use embeddings for semantic matching
    matched_kpi, confidence = _semantic_match_kpi_with_embeddings(user_query)

    # High confidence match - route to KPI agent
    # Threshold lowered for Titan embeddings + keyword boost hybrid
    if confidence > 0.6 and matched_kpi:
        kpi_name = KPI_CATALOGUE[matched_kpi]['name']
        log_entry = AgentLog(
            agent_name="Supervisor",
            input_summary=user_query[:100],
            output_summary=f"Routed to KPI agent for {matched_kpi}",
            reasoning_summary=f"Hybrid semantic search matched '{kpi_name}' with {confidence*100:.0f}% confidence. Method: AWS Titan embeddings + keyword boosting.",
            status="success",
            timestamp=datetime.now().isoformat()
        )

        return {
            "route_type": "KPI",
            "route_reason": f"Semantic match for {KPI_CATALOGUE[matched_kpi]['name']} (confidence: {confidence:.2f})",
            "matched_kpi": matched_kpi,
            "extracted_filters": _extract_filters(user_query),
            "agent_logs": [log_entry]
        }

    # Medium confidence - use LLM to verify
    if confidence > 0.4 and matched_kpi:
        # Use LLM to confirm the match
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

            kpi_name = KPI_CATALOGUE[matched_kpi]['name']
            log_entry = AgentLog(
                agent_name="Supervisor",
                input_summary=user_query[:100],
                output_summary=f"Routed to {result.get('route_type')} (LLM verified)",
                reasoning_summary=f"Hybrid search found '{kpi_name}' ({confidence*100:.0f}% confidence). LLM verification: {result.get('route_reason')}",
                status="success",
                timestamp=datetime.now().isoformat()
            )

            return {
                "route_type": result.get("route_type"),
                "route_reason": result.get("route_reason"),
                "matched_kpi": result.get("matched_kpi"),
                "extracted_filters": result.get("extracted_filters") or _extract_filters(user_query),
                "agent_logs": [log_entry]
            }
        except Exception as e:
            # LLM failed, use embedding result
            kpi_name = KPI_CATALOGUE[matched_kpi]['name']
            log_entry = AgentLog(
                agent_name="Supervisor",
                input_summary=user_query[:100],
                output_summary=f"Routed to KPI agent for {matched_kpi}",
                reasoning_summary=f"Hybrid search matched '{kpi_name}' ({confidence*100:.0f}% confidence). LLM verification unavailable, using embedding result.",
                status="success",
                timestamp=datetime.now().isoformat()
            )

            return {
                "route_type": "KPI",
                "route_reason": f"Embedding match for {KPI_CATALOGUE[matched_kpi]['name']}",
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

        log_entry = AgentLog(
            agent_name="Supervisor",
            input_summary=user_query[:100],
            output_summary=f"Routed to {result.get('route_type')}",
            reasoning_summary=result.get("route_reason"),
            status="success",
            timestamp=datetime.now().isoformat()
        )

        return {
            "route_type": result.get("route_type"),
            "route_reason": result.get("route_reason"),
            "matched_kpi": result.get("matched_kpi"),
            "extracted_filters": result.get("extracted_filters") or _extract_filters(user_query),
            "agent_logs": [log_entry]
        }

    except Exception as e:
        # Complete fallback
        log_entry = AgentLog(
            agent_name="Supervisor",
            input_summary=user_query[:100],
            output_summary="Routed to Analyst (fallback)",
            reasoning_summary=f"Routing error: {str(e)}",
            status="error",
            timestamp=datetime.now().isoformat()
        )

        return {
            "route_type": "COMPLEX",
            "route_reason": "Fallback routing due to error",
            "matched_kpi": None,
            "extracted_filters": _extract_filters(user_query),
            "agent_logs": [log_entry]
        }


def _extract_filters(query: str) -> dict:
    """Extract common filters from query (SKU, site, time period)"""
    import re

    filters = {}
    query_lower = query.lower()

    # Extract SKU
    sku_match = re.search(r'sku[_\s]?(\d+)', query_lower)
    if sku_match:
        filters["sku"] = f"SKU_{sku_match.group(1)}"

    # Extract site
    site_match = re.search(r'(fctn-plant-\d+|plant\s*\d+)', query_lower)
    if site_match:
        filters["site"] = site_match.group(1).upper().replace(" ", "-")

    # Extract time period
    if "this week" in query_lower:
        filters["time_period"] = "current_week"
    elif "last week" in query_lower:
        filters["time_period"] = "last_week"
    elif "this month" in query_lower:
        filters["time_period"] = "current_month"
    elif "last month" in query_lower:
        filters["time_period"] = "last_month"

    # Extract month/year
    month_match = re.search(r'(january|february|march|april|may|june|july|august|september|october|november|december)\s*(\d{4})?', query_lower)
    if month_match:
        filters["month"] = month_match.group(1).capitalize()
        if month_match.group(2):
            filters["year"] = month_match.group(2)

    return filters if filters else None

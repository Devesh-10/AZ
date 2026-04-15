"""
Supervisor Agent for MIA
Routes queries to appropriate agents using semantic embeddings.
Uses AWS Bedrock Titan embeddings for similarity matching.
Supports conversational memory for follow-up questions.
"""

import json
import re
import numpy as np
from datetime import datetime
from functools import lru_cache
from langchain_aws import ChatBedrock, BedrockEmbeddings
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage


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


# ==========================================
# Conversational Memory - Follow-up Detection
# ==========================================

FOLLOW_UP_PATTERNS = [
    r"^what\s+(do|did|does|is|are|was|were)\s+(you|that|it|this)\s+mean",
    r"^(tell me more|explain|elaborate|clarify)",
    r"^(why|how)\s+(is|are|was|were|did)\s+(that|it|this)",
    r"^(and|also|what about)\s+",
    r"^(can you|could you)\s+(explain|clarify|elaborate)",
    r"^what\s+about\s+",
    r"^(which|what)\s+(one|ones)",
    r"^why$",
    r"^how$",
]


def _is_follow_up_query(query: str, conversation_history: list) -> bool:
    """
    Detect if the query is a follow-up to previous conversation.
    Returns True if the query references previous context.
    """
    if not conversation_history:
        return False

    query_lower = query.lower().strip()

    # Check explicit follow-up patterns
    for pattern in FOLLOW_UP_PATTERNS:
        if re.match(pattern, query_lower):
            return True

    # Check for pronouns that reference previous context
    pronoun_references = [
        "that", "this", "it", "they", "them", "those", "these",
        "the same", "similar", "like that", "mentioned"
    ]

    # Short queries with pronouns are likely follow-ups
    words = query_lower.split()
    if len(words) <= 8:  # Short query
        for ref in pronoun_references:
            if ref in query_lower:
                return True

    return False


def _resolve_follow_up_query(query: str, conversation_history: list) -> str:
    """
    Use LLM to resolve a follow-up query by incorporating context from conversation history.
    Returns an expanded, self-contained query.
    """
    if not conversation_history:
        return query

    try:
        llm = ChatBedrock(
            model_id=settings.supervisor_model,
            region_name=settings.aws_region
        )

        # Build conversation context (last 6 messages max)
        recent_history = conversation_history[-6:]
        history_text = ""
        for msg in recent_history:
            # Handle both dict format and LangChain message objects
            if hasattr(msg, 'type'):
                # LangChain message object (HumanMessage, AIMessage, etc.)
                role = msg.type  # 'human' or 'ai'
                content = msg.content if hasattr(msg, 'content') else str(msg)
            elif isinstance(msg, dict):
                role = msg.get("role", "user")
                content = msg.get("content", "")
            else:
                continue

            if isinstance(content, str):
                # Truncate long messages
                content = content[:500] + "..." if len(content) > 500 else content
                history_text += f"{role.upper()}: {content}\n\n"

        resolve_prompt = f"""You are analyzing a follow-up question in a manufacturing analytics conversation.

## Previous Conversation:
{history_text}

## Current User Query:
"{query}"

## Your Task:
The user's query references previous conversation context. Rewrite it as a complete, self-contained question that can be understood without the conversation history.

IMPORTANT:
- Keep the rewritten query concise (under 50 words)
- Preserve the user's original intent
- Include specific KPIs mentioned earlier if relevant
- If the user asks for a breakdown (e.g., "site wise", "by site", "by SKU", "month wise"), do NOT filter to a specific site/SKU - they want ALL sites/SKUs shown
- If the query asks for clarification about a concept, include what concept
- Return ONLY the rewritten query, nothing else

Rewritten query:"""

        response = llm.invoke([HumanMessage(content=resolve_prompt)])
        resolved_query = response.content.strip()

        # Clean up the response
        resolved_query = resolved_query.strip('"\'')

        # Validate it's reasonable
        if len(resolved_query) > 10 and len(resolved_query) < 500:
            return resolved_query
        else:
            return query

    except Exception as e:
        print(f"Follow-up resolution error: {e}")
        return query

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
2. **COMPLEX** - Any other manufacturing-related question (the Analyst will handle it or explain what data is available)
3. **CLARIFY** - Query is too vague to understand what the user wants

## Available KPIs (route to KPI agent):
{kpi_list}

## Foundation Data Products (route to COMPLEX/Analyst agent):
{fdp_list}

## IMPORTANT: Route generously to COMPLEX
- If unsure, route to COMPLEX - the Analyst agent is smart and can handle unknown queries gracefully
- The Analyst will either answer from available data OR explain what data exists
- Only use CLARIFY if the query is genuinely too vague to understand intent

## Manufacturing Terminology:
- "plant/plants" = manufacturing facilities/sites
- "site/sites" = manufacturing locations/factories

## Routing Rules:
- Single KPI questions (e.g., "What is the batch yield?") → KPI
- Everything else manufacturing-related → COMPLEX
- Genuinely ambiguous queries → CLARIFY

## Output Format (JSON):
{{
    "route_type": "KPI" | "COMPLEX" | "CLARIFY",
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
    """
    Check if query is CLEARLY complex requiring transaction-level data.

    MINIMAL hardcoding - only for cases that are unambiguously complex.
    Let the LLM decide for everything else via semantic matching + verification.
    """
    query_lower = query.lower()
    import re

    # Only truly unambiguous complex queries:
    # 1. Specific batch/order IDs (e.g., B2025-00007)
    has_batch_id = bool(re.search(r'b\d{4}-\d+', query_lower))

    # 2. Root cause / recommendation questions (clearly need analysis, not lookup)
    root_cause_patterns = [
        "why is", "why are", "why did",
        "root cause", "what's causing", "what is causing",
        "how can we improve", "how to improve",
        "recommendations", "suggest improvements"
    ]
    is_root_cause = any(p in query_lower for p in root_cause_patterns)

    # 3. Questions about specific batches in quarantine/QA
    qa_batch_queries = [
        "which batches are quarantined",
        "batches waiting for qa",
        "batches in quarantine",
        "list all quarantined",
        "batches with deviations"
    ]
    is_qa_batch_query = any(p in query_lower for p in qa_batch_queries)

    return has_batch_id or is_root_cause or is_qa_batch_query


def supervisor_agent(state: MIAState) -> dict:
    """
    Supervisor agent that routes queries using semantic embeddings.
    Supports conversational memory for follow-up questions.

    Args:
        state: Current MIA state with user query

    Returns:
        Updated state with routing decision
    """
    user_query = state["user_query"]
    conversation_history = state.get("conversation_history", [])

    # ==========================================
    # Step 0: Handle follow-up queries
    # ==========================================
    original_query = user_query
    is_follow_up = False

    if _is_follow_up_query(user_query, conversation_history):
        is_follow_up = True
        resolved_query = _resolve_follow_up_query(user_query, conversation_history)
        if resolved_query != user_query:
            print(f"[Supervisor] Resolved follow-up: '{user_query}' -> '{resolved_query}'")
            user_query = resolved_query

    # Build follow-up context for logging
    follow_up_context = ""
    if is_follow_up and user_query != original_query:
        follow_up_context = f" [Follow-up resolved: '{original_query}' -> '{user_query}']"

    # Check if this is clearly a complex query
    if _is_complex_query(user_query):
        log_entry = AgentLog(
            agent_name="Supervisor",
            input_summary=user_query[:100],
            output_summary="Routed to Analyst agent",
            reasoning_summary=f"Query requires complex analysis.{follow_up_context}",
            status="success",
            timestamp=datetime.now().isoformat()
        )
        return {
            "route_type": "COMPLEX",
            "route_reason": "Query requires multi-step analysis or comparison",
            "matched_kpi": None,
            "extracted_filters": _extract_filters(user_query),
            "agent_logs": [log_entry],
            "user_query": user_query  # Pass resolved query to downstream agents
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
            reasoning_summary=f"Hybrid semantic search matched '{kpi_name}' with {confidence*100:.0f}% confidence. Method: AWS Titan embeddings + keyword boosting.{follow_up_context}",
            status="success",
            timestamp=datetime.now().isoformat()
        )

        return {
            "route_type": "KPI",
            "route_reason": f"Semantic match for {KPI_CATALOGUE[matched_kpi]['name']} (confidence: {confidence:.2f})",
            "matched_kpi": matched_kpi,
            "extracted_filters": _extract_filters(user_query),
            "agent_logs": [log_entry],
            "user_query": user_query  # Pass resolved query to downstream agents
        }

    # Medium confidence - use LLM to verify
    if confidence > 0.4 and matched_kpi:
        # Use LLM to confirm the match
        llm = ChatBedrock(
            model_id=settings.supervisor_model,
            region_name=settings.aws_region
        )

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
                reasoning_summary=f"Hybrid search found '{kpi_name}' ({confidence*100:.0f}% confidence). LLM verification: {result.get('route_reason')}{follow_up_context}",
                status="success",
                timestamp=datetime.now().isoformat()
            )

            return {
                "route_type": result.get("route_type"),
                "route_reason": result.get("route_reason"),
                "matched_kpi": result.get("matched_kpi"),
                "extracted_filters": result.get("extracted_filters") or _extract_filters(user_query),
                "agent_logs": [log_entry],
                "user_query": user_query  # Pass resolved query to downstream agents
            }
        except Exception as e:
            # LLM failed, use embedding result
            kpi_name = KPI_CATALOGUE[matched_kpi]['name']
            log_entry = AgentLog(
                agent_name="Supervisor",
                input_summary=user_query[:100],
                output_summary=f"Routed to KPI agent for {matched_kpi}",
                reasoning_summary=f"Hybrid search matched '{kpi_name}' ({confidence*100:.0f}% confidence). LLM verification unavailable, using embedding result.{follow_up_context}",
                status="success",
                timestamp=datetime.now().isoformat()
            )

            return {
                "route_type": "KPI",
                "route_reason": f"Embedding match for {KPI_CATALOGUE[matched_kpi]['name']}",
                "matched_kpi": matched_kpi,
                "extracted_filters": _extract_filters(user_query),
                "agent_logs": [log_entry],
                "user_query": user_query  # Pass resolved query to downstream agents
            }

    # Low confidence - use LLM for full routing
    llm = ChatBedrock(
        model_id=settings.supervisor_model,
        region_name=settings.aws_region
    )

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

        reasoning = result.get("route_reason", "")
        if follow_up_context:
            reasoning = f"{reasoning}{follow_up_context}"

        log_entry = AgentLog(
            agent_name="Supervisor",
            input_summary=user_query[:100],
            output_summary=f"Routed to {result.get('route_type')}",
            reasoning_summary=reasoning,
            status="success",
            timestamp=datetime.now().isoformat()
        )

        return {
            "route_type": result.get("route_type"),
            "route_reason": result.get("route_reason"),
            "matched_kpi": result.get("matched_kpi"),
            "extracted_filters": result.get("extracted_filters") or _extract_filters(user_query),
            "agent_logs": [log_entry],
            "user_query": user_query  # Pass resolved query to downstream agents
        }

    except Exception as e:
        # Complete fallback
        log_entry = AgentLog(
            agent_name="Supervisor",
            input_summary=user_query[:100],
            output_summary="Routed to Analyst (fallback)",
            reasoning_summary=f"Routing error: {str(e)}{follow_up_context}",
            status="error",
            timestamp=datetime.now().isoformat()
        )

        return {
            "route_type": "COMPLEX",
            "route_reason": "Fallback routing due to error",
            "matched_kpi": None,
            "extracted_filters": _extract_filters(user_query),
            "agent_logs": [log_entry],
            "user_query": user_query  # Pass resolved query to downstream agents
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

    # Site filtering is handled by the SQL generation LLM based on user intent
    # No hardcoded extraction - LLM decides whether to filter or show all sites

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

"""
Supervisor Agent for DSA (Data Quality Lifecycle Agent)
Routes queries to KPI agent (single metrics) or lifecycle pipeline (multi-stage DQ analysis).
Uses AWS Bedrock Titan embeddings for semantic matching.
"""

import json
import re
import numpy as np
from datetime import datetime
from langchain_aws import ChatBedrock, BedrockEmbeddings
from langchain_core.messages import HumanMessage, SystemMessage


def cosine_similarity(X, Y):
    X_norm = X / np.linalg.norm(X, axis=1, keepdims=True)
    Y_norm = Y / np.linalg.norm(Y, axis=1, keepdims=True)
    return np.dot(X_norm, Y_norm.T)


from app.core.config import get_settings
from app.models.state import DSAState, AgentLog
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
    if not conversation_history:
        return False
    query_lower = query.lower().strip()
    for pattern in FOLLOW_UP_PATTERNS:
        if re.match(pattern, query_lower):
            return True
    pronoun_references = [
        "that", "this", "it", "they", "them", "those", "these",
        "the same", "similar", "like that", "mentioned"
    ]
    words = query_lower.split()
    if len(words) <= 8:
        for ref in pronoun_references:
            if ref in query_lower:
                return True
    return False


def _resolve_follow_up_query(query: str, conversation_history: list) -> str:
    if not conversation_history:
        return query
    try:
        llm = ChatBedrock(
            model_id=settings.supervisor_model,
            region_name=settings.aws_region
        )
        recent_history = conversation_history[-6:]
        history_text = ""
        for msg in recent_history:
            if hasattr(msg, 'type'):
                role = msg.type
                content = msg.content if hasattr(msg, 'content') else str(msg)
            elif isinstance(msg, dict):
                role = msg.get("role", "user")
                content = msg.get("content", "")
            else:
                continue
            if isinstance(content, str):
                content = content[:500] + "..." if len(content) > 500 else content
                history_text += f"{role.upper()}: {content}\n\n"

        resolve_prompt = f"""You are analyzing a follow-up question in a data quality lifecycle conversation.

## Previous Conversation:
{history_text}

## Current User Query:
"{query}"

## Your Task:
Rewrite it as a complete, self-contained question. Keep under 50 words. Return ONLY the rewritten query.

Rewritten query:"""

        response = llm.invoke([HumanMessage(content=resolve_prompt)])
        resolved_query = response.content.strip().strip('"\'')
        if 10 < len(resolved_query) < 500:
            return resolved_query
        return query
    except Exception as e:
        print(f"Follow-up resolution error: {e}")
        return query


# ==========================================
# Embeddings for KPI matching
# ==========================================

_embeddings_model = None


def get_embeddings_model():
    global _embeddings_model
    if _embeddings_model is None:
        _embeddings_model = BedrockEmbeddings(
            model_id="amazon.titan-embed-text-v2:0",
            region_name=settings.aws_region
        )
    return _embeddings_model


_kpi_embeddings_cache = None


def _build_kpi_descriptions() -> dict[str, str]:
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


# ==========================================
# Lifecycle Detection - which stages to run
# ==========================================

LIFECYCLE_PATTERNS = {
    "full_lifecycle": [
        "run full", "full lifecycle", "full dq lifecycle", "complete lifecycle",
        "run lifecycle", "lifecycle on", "full data quality", "end to end",
        "run all stages", "complete analysis"
    ],
    "discovery_only": [
        "discover", "scan tables", "what tables", "list tables",
        "catalogue", "catalog", "metadata", "schema"
    ],
    "profiling": [
        "profile", "profiling", "completeness", "accuracy", "distributions",
        "statistical summary", "data distributions", "outlier",
        "how complete", "how accurate", "data quality of"
    ],
    "rules_check": [
        "rule", "rules", "validation", "validate", "conformance",
        "compliance", "business rule", "check rules", "rule violation",
        "which rules", "failing rules"
    ],
    "scorecard": [
        "scorecard", "score card", "dq score", "quality score",
        "report", "dashboard", "summary", "overall quality",
        "data quality assessment", "dq assessment"
    ],
    "remediation": [
        "remediat", "fix", "root cause", "how to fix",
        "what's causing", "improve", "recommend", "action plan",
        "data cleanup", "priority fixes"
    ]
}


def _detect_lifecycle_stages(query: str) -> list[str] | None:
    """Determine which lifecycle stages to run based on query."""
    query_lower = query.lower()

    # Full lifecycle
    for pattern in LIFECYCLE_PATTERNS["full_lifecycle"]:
        if pattern in query_lower:
            return ["discovery", "profiling", "rules", "reporting", "remediation"]

    # Remediation needs full context
    for pattern in LIFECYCLE_PATTERNS["remediation"]:
        if pattern in query_lower:
            return ["discovery", "profiling", "rules", "reporting", "remediation"]

    # Scorecard needs profiling + rules
    for pattern in LIFECYCLE_PATTERNS["scorecard"]:
        if pattern in query_lower:
            return ["discovery", "profiling", "rules", "reporting"]

    # Rules check — discovery + rules only (distinct from scorecard)
    for pattern in LIFECYCLE_PATTERNS["rules_check"]:
        if pattern in query_lower:
            return ["discovery", "rules"]

    # Profiling — discovery + profiling only (distinct from scorecard)
    for pattern in LIFECYCLE_PATTERNS["profiling"]:
        if pattern in query_lower:
            return ["discovery", "profiling"]

    # Discovery only
    for pattern in LIFECYCLE_PATTERNS["discovery_only"]:
        if pattern in query_lower:
            return ["discovery"]

    return None


def _is_lifecycle_query(query: str) -> bool:
    """Check if query should route to lifecycle pipeline."""
    query_lower = query.lower()

    # Check for lifecycle-specific patterns
    lifecycle_keywords = [
        "profile", "profiling", "lifecycle", "discovery", "discover",
        "remediat", "scorecard", "score card", "rules", "rule violation",
        "business rule", "conformance", "scan table", "catalogue",
        "root cause", "how to fix", "data cleanup", "fix the data",
        "action plan", "dq assessment", "data quality assessment",
        "cross-system", "cross system", "reconciliation",
        "what tables", "list tables", "end to end"
    ]
    if any(kw in query_lower for kw in lifecycle_keywords):
        return True

    # Specific table references → lifecycle profiling
    if re.search(r'(mes_pasx|analytics_batch|lims_results|sap_orders|equipment_master|materials_master)', query_lower):
        return True

    return False


# ==========================================
# LLM Routing Prompt
# ==========================================

SUPERVISOR_SYSTEM_PROMPT = """You are a Data Quality Lifecycle Agent supervisor responsible for routing user queries.

## Your Role
You oversee a Data Quality Lifecycle platform with two paths:
1. **KPI** - Simple single-metric lookups (completeness %, accuracy %, freshness, consistency)
2. **LIFECYCLE** - Multi-stage DQ analysis: discovery → profiling → rules → reporting → remediation
3. **CLARIFY** - Query is too vague

## Available KPIs (route to KPI):
{kpi_list}

## Route to LIFECYCLE for:
- Any profiling, discovery, or scanning request
- Rule validation / conformance checks
- DQ scorecard / assessment requests
- Remediation / root cause / fix recommendations
- Cross-system reconciliation
- Specific table analysis
- "Run full lifecycle" or "end to end" requests

## Route to KPI for:
- Single data quality metric questions (e.g., "What is batch completeness?")
- Simple metric lookups

## Output Format (JSON):
{{
    "route_type": "KPI" | "LIFECYCLE" | "CLARIFY",
    "route_reason": "Brief explanation",
    "matched_kpi": "kpi_id if KPI route, else null",
    "extracted_filters": {{"table": "...", "system": "...", "dimension": "..."}} or null
}}

Respond ONLY with valid JSON."""


def _build_kpi_list() -> str:
    lines = []
    for kpi_id, info in KPI_CATALOGUE.items():
        aliases = ", ".join(info["aliases"])
        lines.append(f"- {kpi_id}: {info['name']} ({aliases})")
    return "\n".join(lines)


def _extract_filters(query: str) -> dict:
    filters = {}
    query_lower = query.lower()

    table_match = re.search(r'(mes_pasx_batches|mes_pasx_batch_steps|analytics_batch_status|analytics_order_status|lims_results|sap_orders|events_alarms|goods_receipts|inventory_snapshots|consumption_movements|procurement_pos|equipment_master|materials_master|vendors_master)', query_lower)
    if table_match:
        filters["table"] = table_match.group(1)

    system_keywords = {"mes": "MES", "pasx": "MES", "lims": "LIMS", "sap": "SAP", "analytics": "Analytics"}
    for keyword, system in system_keywords.items():
        if keyword in query_lower:
            filters["system"] = system
            break

    dimension_keywords = {
        "completeness": "completeness", "accuracy": "accuracy",
        "timeliness": "timeliness", "freshness": "timeliness",
        "consistency": "consistency", "uniqueness": "uniqueness"
    }
    for keyword, dimension in dimension_keywords.items():
        if keyword in query_lower:
            filters["dimension"] = dimension
            break

    return filters if filters else None


# ==========================================
# Main Supervisor Agent
# ==========================================

def supervisor_agent(state: DSAState) -> dict:
    """Routes queries to KPI agent or lifecycle pipeline."""
    user_query = state["user_query"]
    conversation_history = state.get("conversation_history", [])

    # Step 0: Handle follow-up queries
    original_query = user_query
    is_follow_up = False
    if _is_follow_up_query(user_query, conversation_history):
        is_follow_up = True
        resolved_query = _resolve_follow_up_query(user_query, conversation_history)
        if resolved_query != user_query:
            print(f"[Supervisor] Resolved follow-up: '{user_query}' -> '{resolved_query}'")
            user_query = resolved_query

    follow_up_context = ""
    if is_follow_up and user_query != original_query:
        follow_up_context = f" [Follow-up resolved: '{original_query}' -> '{user_query}']"

    # Step 1: Check if this is clearly a lifecycle query
    if _is_lifecycle_query(user_query):
        stages = _detect_lifecycle_stages(user_query) or ["discovery", "profiling", "rules", "reporting", "remediation"]
        log_entry = AgentLog(
            agent_name="Supervisor",
            input_summary=user_query[:100],
            output_summary=f"Routed to DQ Lifecycle: {' → '.join(stages)}",
            reasoning_summary=f"Query requires multi-stage DQ lifecycle analysis. Stages: {stages}.{follow_up_context}",
            status="success",
            timestamp=datetime.now().isoformat()
        )
        return {
            "route_type": "LIFECYCLE",
            "route_reason": f"DQ lifecycle analysis with stages: {', '.join(stages)}",
            "matched_kpi": None,
            "extracted_filters": _extract_filters(user_query),
            "lifecycle_stages": stages,
            "agent_logs": [log_entry],
            "user_query": user_query
        }

    # Step 2: Try semantic KPI matching
    matched_kpi, confidence = _semantic_match_kpi_with_embeddings(user_query)

    # High confidence KPI match
    if confidence > 0.6 and matched_kpi:
        kpi_name = KPI_CATALOGUE[matched_kpi]['name']
        log_entry = AgentLog(
            agent_name="Supervisor",
            input_summary=user_query[:100],
            output_summary=f"Routed to KPI agent for {matched_kpi}",
            reasoning_summary=f"Semantic match: '{kpi_name}' ({confidence*100:.0f}% confidence).{follow_up_context}",
            status="success",
            timestamp=datetime.now().isoformat()
        )
        return {
            "route_type": "KPI",
            "route_reason": f"Semantic match for {kpi_name} (confidence: {confidence:.2f})",
            "matched_kpi": matched_kpi,
            "extracted_filters": _extract_filters(user_query),
            "lifecycle_stages": None,
            "agent_logs": [log_entry],
            "user_query": user_query
        }

    # Medium confidence - LLM verification
    if confidence > 0.4 and matched_kpi:
        try:
            llm = ChatBedrock(model_id=settings.supervisor_model, region_name=settings.aws_region)
            system_prompt = SUPERVISOR_SYSTEM_PROMPT.format(kpi_list=_build_kpi_list())
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Route this query: {user_query}")
            ]
            response = llm.invoke(messages)
            result = json.loads(response.content)

            route_type = result.get("route_type", "LIFECYCLE")
            stages = None
            if route_type == "LIFECYCLE":
                stages = _detect_lifecycle_stages(user_query) or ["discovery", "profiling", "rules", "reporting", "remediation"]

            log_entry = AgentLog(
                agent_name="Supervisor",
                input_summary=user_query[:100],
                output_summary=f"Routed to {route_type} (LLM verified)",
                reasoning_summary=f"Semantic: '{KPI_CATALOGUE[matched_kpi]['name']}' ({confidence*100:.0f}%). LLM: {result.get('route_reason')}{follow_up_context}",
                status="success",
                timestamp=datetime.now().isoformat()
            )
            return {
                "route_type": route_type,
                "route_reason": result.get("route_reason"),
                "matched_kpi": result.get("matched_kpi") if route_type == "KPI" else None,
                "extracted_filters": result.get("extracted_filters") or _extract_filters(user_query),
                "lifecycle_stages": stages,
                "agent_logs": [log_entry],
                "user_query": user_query
            }
        except Exception:
            # Fallback to KPI
            kpi_name = KPI_CATALOGUE[matched_kpi]['name']
            log_entry = AgentLog(
                agent_name="Supervisor",
                input_summary=user_query[:100],
                output_summary=f"Routed to KPI agent for {matched_kpi}",
                reasoning_summary=f"Semantic match: '{kpi_name}' ({confidence*100:.0f}%). LLM verification unavailable.{follow_up_context}",
                status="success",
                timestamp=datetime.now().isoformat()
            )
            return {
                "route_type": "KPI",
                "route_reason": f"Embedding match for {kpi_name}",
                "matched_kpi": matched_kpi,
                "extracted_filters": _extract_filters(user_query),
                "lifecycle_stages": None,
                "agent_logs": [log_entry],
                "user_query": user_query
            }

    # Low confidence - full LLM routing
    try:
        llm = ChatBedrock(model_id=settings.supervisor_model, region_name=settings.aws_region)
        system_prompt = SUPERVISOR_SYSTEM_PROMPT.format(kpi_list=_build_kpi_list())
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Route this query: {user_query}")
        ]
        response = llm.invoke(messages)
        result = json.loads(response.content)

        route_type = result.get("route_type", "LIFECYCLE")
        stages = None
        if route_type == "LIFECYCLE":
            stages = _detect_lifecycle_stages(user_query) or ["discovery", "profiling", "rules", "reporting", "remediation"]

        log_entry = AgentLog(
            agent_name="Supervisor",
            input_summary=user_query[:100],
            output_summary=f"Routed to {route_type}",
            reasoning_summary=f"{result.get('route_reason', '')}{follow_up_context}",
            status="success",
            timestamp=datetime.now().isoformat()
        )
        return {
            "route_type": route_type,
            "route_reason": result.get("route_reason"),
            "matched_kpi": result.get("matched_kpi") if route_type == "KPI" else None,
            "extracted_filters": result.get("extracted_filters") or _extract_filters(user_query),
            "lifecycle_stages": stages,
            "agent_logs": [log_entry],
            "user_query": user_query
        }
    except Exception as e:
        # Complete fallback → lifecycle
        stages = _detect_lifecycle_stages(user_query) or ["discovery", "profiling", "rules", "reporting", "remediation"]
        log_entry = AgentLog(
            agent_name="Supervisor",
            input_summary=user_query[:100],
            output_summary=f"Routed to Lifecycle (fallback)",
            reasoning_summary=f"Routing error: {str(e)}{follow_up_context}",
            status="error",
            timestamp=datetime.now().isoformat()
        )
        return {
            "route_type": "LIFECYCLE",
            "route_reason": "Fallback routing due to error",
            "matched_kpi": None,
            "extracted_filters": _extract_filters(user_query),
            "lifecycle_stages": stages,
            "agent_logs": [log_entry],
            "user_query": user_query
        }

"""DynamoDB Trace Store for MIA LangGraph - Execution Traces & Query Cache"""

import boto3
import hashlib
import json
import time
from typing import Optional
from app.core.config import get_settings

settings = get_settings()

_table = None


def _get_table():
    """Get DynamoDB trace table reference"""
    global _table
    if _table is None:
        dynamodb = boto3.resource("dynamodb", region_name=settings.aws_region)
        _table = dynamodb.Table(settings.trace_table_name)
    return _table


def _normalize_query(query: str) -> str:
    """Normalize a query for cache matching (lowercase, strip whitespace)"""
    return " ".join(query.lower().strip().split())


def _query_hash(query: str) -> str:
    """Generate a hash key for a normalized query"""
    normalized = _normalize_query(query)
    return hashlib.sha256(normalized.encode()).hexdigest()[:16]


def lookup_cached_result(user_query: str, max_age_hours: int = 24) -> Optional[dict]:
    """
    Check if this query has been asked before and return cached result.
    Returns the cached response dict or None if no valid cache exists.
    """
    table = _get_table()
    query_key = _query_hash(user_query)

    try:
        response = table.get_item(Key={"query_hash": query_key})
        item = response.get("Item")
        if not item:
            return None

        # Check if cache is still fresh
        cached_at = item.get("created_at", 0)
        age_seconds = time.time() - cached_at
        if age_seconds > max_age_hours * 3600:
            return None

        return {
            "final_answer": item.get("final_answer"),
            "route_type": item.get("route_type"),
            "matched_kpi": item.get("matched_kpi"),
            "is_valid": item.get("is_valid", True),
            "validation_issues": json.loads(item.get("validation_issues", "[]")),
            "visualization_config": json.loads(item.get("visualization_config", "null")),
            "generated_sql": item.get("generated_sql"),
            "agent_logs": json.loads(item.get("agent_logs", "[]")),
            "cached": True,
        }
    except Exception as e:
        print(f"[TraceStore] Error looking up cache for query: {e}")
        return None


def save_trace(user_query: str, result: dict, agent_logs: list[dict]):
    """
    Save a LangGraph execution trace and cache the result for future lookups.
    """
    table = _get_table()
    query_key = _query_hash(user_query)
    now = int(time.time())
    ttl = now + (7 * 24 * 60 * 60)  # 7 days

    try:
        table.put_item(Item={
            "query_hash": query_key,
            "original_query": user_query,
            "normalized_query": _normalize_query(user_query),
            "route_type": result.get("route_type"),
            "matched_kpi": result.get("matched_kpi"),
            "final_answer": result.get("final_answer"),
            "generated_sql": result.get("generated_sql"),
            "is_valid": result.get("is_valid", True),
            "validation_issues": json.dumps(result.get("validation_issues", [])),
            "visualization_config": json.dumps(result.get("visualization_config")),
            "agent_logs": json.dumps(agent_logs),
            "created_at": now,
            "ttl": ttl,
        })
    except Exception as e:
        print(f"[TraceStore] Error saving trace: {e}")


def get_trace_telemetry(query_hash: str) -> Optional[dict]:
    """Retrieve a specific trace by query hash"""
    table = _get_table()
    try:
        response = table.get_item(Key={"query_hash": query_hash})
        return response.get("Item")
    except Exception as e:
        print(f"[TraceStore] Error reading trace {query_hash}: {e}")
        return None

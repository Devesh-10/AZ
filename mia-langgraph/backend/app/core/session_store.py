"""DynamoDB Session Store for MIA LangGraph - Chat History Only"""

import boto3
import json
import time
from app.core.config import get_settings

settings = get_settings()

_table = None


def _get_table():
    """Get DynamoDB session history table reference"""
    global _table
    if _table is None:
        dynamodb = boto3.resource("dynamodb", region_name=settings.aws_region)
        _table = dynamodb.Table(settings.session_table_name)
    return _table


def get_session_history(session_id: str) -> list[dict]:
    """Retrieve conversation history for a session"""
    table = _get_table()
    try:
        response = table.get_item(Key={"session_id": session_id})
        item = response.get("Item")
        if item:
            return json.loads(item.get("conversation_history", "[]"))
        return []
    except Exception as e:
        print(f"[SessionStore] Error reading session {session_id}: {e}")
        return []


def save_session_history(session_id: str, conversation_history: list[dict], max_messages: int = 20):
    """Save conversation history to DynamoDB with TTL"""
    table = _get_table()
    trimmed = conversation_history[-max_messages:]
    ttl = int(time.time()) + (30 * 24 * 60 * 60)  # 30 days

    try:
        table.put_item(Item={
            "session_id": session_id,
            "conversation_history": json.dumps(trimmed),
            "updated_at": int(time.time()),
            "ttl": ttl,
        })
    except Exception as e:
        print(f"[SessionStore] Error saving session {session_id}: {e}")


def delete_session(session_id: str):
    """Delete a session from DynamoDB"""
    table = _get_table()
    try:
        table.delete_item(Key={"session_id": session_id})
    except Exception as e:
        print(f"[SessionStore] Error deleting session {session_id}: {e}")

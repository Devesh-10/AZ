"""LangGraph State Models for MIA"""

from typing import TypedDict, Annotated, Literal
from langgraph.graph.message import add_messages
import operator


def add_logs(left: list, right: list) -> list:
    """Reducer to accumulate agent logs"""
    if left is None:
        left = []
    if right is None:
        right = []
    return left + right


class AgentLog(TypedDict):
    """Log entry for agent telemetry"""
    agent_name: str
    input_summary: str
    output_summary: str
    reasoning_summary: str | None
    status: Literal["success", "error"]
    timestamp: str


class KPIResult(TypedDict):
    """KPI query result"""
    kpi_name: str
    breakdown_by: str | None
    data_points: list[dict]
    explanation: str | None


class AnalystResult(TypedDict):
    """Analyst agent result"""
    narrative: str
    supporting_kpi_results: list[KPIResult]
    insights: list[str]


class MIAState(TypedDict):
    """
    Main state for the MIA LangGraph workflow.
    This state is shared across all agents in the graph.
    """
    # Input
    session_id: str
    user_query: str
    conversation_history: Annotated[list, add_messages]

    # Routing
    route_type: Literal["KPI", "COMPLEX", "REJECT", "CLARIFY"] | None
    route_reason: str | None
    matched_kpi: str | None
    extracted_filters: dict | None

    # KPI Agent Output
    kpi_results: list[KPIResult] | None
    generated_sql: str | None

    # Analyst Agent Output
    analyst_result: AnalystResult | None

    # Validation
    is_valid: bool
    validation_issues: list[str]
    follow_up_question: str | None

    # Final Output
    final_answer: str | None
    visualization_config: dict | None

    # Telemetry - uses reducer to accumulate logs from all agents
    agent_logs: Annotated[list[AgentLog], add_logs]

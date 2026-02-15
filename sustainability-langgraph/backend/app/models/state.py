"""
State models for Sustainability Insight Agent LangGraph workflow
"""

from typing import TypedDict, Literal, Annotated
from langgraph.graph.message import add_messages


def add_logs(left: list, right: list) -> list:
    """Reducer to accumulate agent logs"""
    if left is None:
        left = []
    if right is None:
        right = []
    return left + right


class AgentLog(TypedDict):
    """Log entry for agent execution"""
    agent_name: str
    input_summary: str
    output_summary: str
    reasoning_summary: str | None
    status: Literal["success", "error"]
    timestamp: str


class KPIResult(TypedDict):
    """Result from KPI Agent"""
    kpi_name: str
    breakdown_by: str | None
    data_points: list[dict]
    explanation: str | None


class AnalystResult(TypedDict):
    """Result from Analyst Agent"""
    narrative: str
    supporting_kpi_results: list[dict]
    insights: list[str]


class SIAState(TypedDict, total=False):
    """
    Sustainability Insight Agent State
    Flows through the LangGraph workflow
    """
    # Input
    user_query: str
    session_id: str
    conversation_history: Annotated[list, add_messages]

    # Routing
    route_type: Literal["KPI", "COMPLEX", "CLARIFY"]
    route_reason: str
    matched_kpi: str | None
    extracted_filters: dict | None

    # Results
    kpi_results: list[dict] | None
    analyst_result: AnalystResult | None

    # Validation
    validation_passed: bool
    validation_notes: str | None

    # Output
    final_answer: str
    generated_sql: str | None
    visualization_config: dict | None

    # Logging - uses reducer to accumulate logs from all agents
    agent_logs: Annotated[list[AgentLog], add_logs]

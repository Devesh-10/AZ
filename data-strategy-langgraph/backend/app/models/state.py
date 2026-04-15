"""LangGraph State Models for DSA (Data Strategy Agent) - DQ Lifecycle"""

from typing import TypedDict, Annotated, Literal
from langgraph.graph.message import add_messages


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


class DSAState(TypedDict):
    """
    Main state for the DSA LangGraph workflow.
    Supports both single-metric KPI queries and full DQ lifecycle execution.
    """
    # Input
    session_id: str
    user_query: str
    conversation_history: Annotated[list, add_messages]

    # Data Source (Collibra / SAP MDG / Excel / Demo)
    data_source: dict | None

    # Routing
    route_type: Literal["KPI", "LIFECYCLE", "CLARIFY"] | None
    route_reason: str | None
    matched_kpi: str | None
    extracted_filters: dict | None

    # Lifecycle stages to execute (set by supervisor)
    lifecycle_stages: list[str] | None

    # KPI Agent Output (single metric queries)
    kpi_results: list[KPIResult] | None
    generated_sql: str | None

    # Lifecycle Agent Outputs
    discovery_result: dict | None
    profiling_result: dict | None
    rules_result: list | None
    reporting_result: dict | None
    remediation_result: dict | None

    # Legacy (kept for compatibility)
    analyst_result: AnalystResult | None

    # Validation
    is_valid: bool
    validation_issues: list[str]
    follow_up_question: str | None

    # Final Output
    final_answer: str | None
    visualization_config: dict | None

    # Telemetry
    agent_logs: Annotated[list[AgentLog], add_logs]

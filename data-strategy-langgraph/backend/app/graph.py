"""
LangGraph Workflow for DSA - DQ Lifecycle Pipeline
Routes: supervisor → (lifecycle_pipeline | kpi_agent | clarify)
Lifecycle: discovery → profiling → rules → reporting → remediation
"""

from typing import Literal
from langgraph.graph import StateGraph, END

from app.models.state import DSAState
from app.agents.supervisor import supervisor_agent
from app.agents.kpi_agent import kpi_agent
from app.agents.discovery_agent import discovery_agent
from app.agents.profiling_agent import profiling_agent
from app.agents.rules_agent import rules_agent
from app.agents.reporting_agent import reporting_agent
from app.agents.remediation_agent import remediation_agent
from app.agents.validator_agent import validator_agent, handle_clarification
from app.agents.visualization_agent import visualization_agent


def route_after_supervisor(state: DSAState) -> Literal["kpi_agent", "discovery", "clarify"]:
    route_type = state.get("route_type")
    if route_type == "KPI":
        return "kpi_agent"
    elif route_type == "CLARIFY":
        return "clarify"
    else:
        return "discovery"


def should_run_profiling(state: DSAState) -> Literal["profiling", "rules", "reporting", "validator"]:
    stages = state.get("lifecycle_stages") or []
    if "profiling" in stages:
        return "profiling"
    if "rules" in stages:
        return "rules"
    if "reporting" in stages:
        return "reporting"
    return "validator"


def should_run_rules(state: DSAState) -> Literal["rules", "reporting", "validator"]:
    stages = state.get("lifecycle_stages") or []
    if "rules" in stages:
        return "rules"
    if "reporting" in stages:
        return "reporting"
    return "validator"


def should_run_reporting(state: DSAState) -> Literal["reporting", "validator"]:
    stages = state.get("lifecycle_stages") or []
    if "reporting" in stages:
        return "reporting"
    return "validator"


def should_run_remediation(state: DSAState) -> Literal["remediation", "validator"]:
    stages = state.get("lifecycle_stages") or []
    if "remediation" in stages:
        return "remediation"
    return "validator"


def route_after_validation(state: DSAState) -> Literal["visualization", "retry"]:
    return "visualization"


def create_dsa_graph() -> StateGraph:
    workflow = StateGraph(DSAState)

    workflow.add_node("supervisor", supervisor_agent)
    workflow.add_node("kpi_agent", kpi_agent)
    workflow.add_node("discovery", discovery_agent)
    workflow.add_node("profiling", profiling_agent)
    workflow.add_node("rules", rules_agent)
    workflow.add_node("reporting", reporting_agent)
    workflow.add_node("remediation", remediation_agent)
    workflow.add_node("validator", validator_agent)
    workflow.add_node("visualization", visualization_agent)
    workflow.add_node("clarify", handle_clarification)

    workflow.set_entry_point("supervisor")

    workflow.add_conditional_edges(
        "supervisor",
        route_after_supervisor,
        {
            "kpi_agent": "kpi_agent",
            "discovery": "discovery",
            "clarify": "clarify"
        }
    )

    workflow.add_edge("kpi_agent", "validator")

    workflow.add_conditional_edges(
        "discovery",
        should_run_profiling,
        {"profiling": "profiling", "rules": "rules", "reporting": "reporting", "validator": "validator"}
    )

    workflow.add_conditional_edges(
        "profiling",
        should_run_rules,
        {"rules": "rules", "reporting": "reporting", "validator": "validator"}
    )

    workflow.add_conditional_edges(
        "rules",
        should_run_reporting,
        {"reporting": "reporting", "validator": "validator"}
    )

    workflow.add_conditional_edges(
        "reporting",
        should_run_remediation,
        {"remediation": "remediation", "validator": "validator"}
    )

    workflow.add_edge("remediation", "validator")
    workflow.add_edge("clarify", END)

    workflow.add_conditional_edges(
        "validator",
        route_after_validation,
        {"visualization": "visualization", "retry": "supervisor"}
    )

    workflow.add_edge("visualization", END)

    return workflow


def get_compiled_graph():
    workflow = create_dsa_graph()
    return workflow.compile()


_compiled_graph = None


def get_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = get_compiled_graph()
    return _compiled_graph


async def run_query(session_id: str, user_query: str, conversation_history: list = None, data_source: dict = None) -> dict:
    from datetime import datetime

    graph = get_graph()

    initial_state: DSAState = {
        "session_id": session_id,
        "user_query": user_query,
        "conversation_history": conversation_history or [],
        "data_source": data_source,
        "route_type": None,
        "route_reason": None,
        "matched_kpi": None,
        "extracted_filters": None,
        "lifecycle_stages": None,
        "kpi_results": None,
        "generated_sql": None,
        "discovery_result": None,
        "profiling_result": None,
        "rules_result": None,
        "reporting_result": None,
        "remediation_result": None,
        "analyst_result": None,
        "is_valid": False,
        "validation_issues": [],
        "follow_up_question": None,
        "final_answer": None,
        "visualization_config": None,
        "agent_logs": []
    }

    try:
        final_state = await graph.ainvoke(initial_state)
        return final_state
    except Exception as e:
        return {
            **initial_state,
            "final_answer": f"An error occurred while processing your query: {str(e)}",
            "is_valid": False,
            "agent_logs": [{
                "agent_name": "System",
                "input_summary": user_query[:100],
                "output_summary": f"Error: {str(e)}",
                "reasoning_summary": None,
                "status": "error",
                "timestamp": datetime.now().isoformat()
            }]
        }

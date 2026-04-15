"""
LangGraph Workflow for MIA
Defines the state machine that orchestrates all agents.
"""

from typing import Literal
from langgraph.graph import StateGraph, END

from app.models.state import MIAState
from app.agents.supervisor import supervisor_agent
from app.agents.kpi_agent import kpi_agent
from app.agents.analyst_agent import analyst_agent
from app.agents.validator_agent import validator_agent, handle_clarification
from app.agents.visualization_agent import visualization_agent


def route_after_supervisor(state: MIAState) -> Literal["kpi_agent", "analyst_agent", "clarify"]:
    """
    Determine next node based on supervisor's routing decision.
    Note: REJECT is no longer used - unknown queries go to analyst who handles gracefully.
    """
    route_type = state.get("route_type")

    if route_type == "KPI":
        return "kpi_agent"
    elif route_type == "CLARIFY":
        return "clarify"
    else:
        # COMPLEX, REJECT, or any unknown -> analyst handles it
        return "analyst_agent"


def route_after_validation(state: MIAState) -> Literal["visualization", "retry"]:
    """
    Determine if response is ready for visualization or needs retry.
    For now, always go to visualization - retry logic can be added later.
    """
    is_valid = state.get("is_valid", False)

    # Could implement retry logic here
    # For now, always proceed to visualization
    return "visualization"


def create_mia_graph() -> StateGraph:
    """
    Create the MIA LangGraph workflow.

    Flow:
    1. Supervisor Agent - routes query
    2. KPI Agent OR Analyst Agent - processes query
    3. Validator Agent - validates response
    4. Visualization Agent - generates chart config
    5. Return to user

    Returns:
        Compiled StateGraph
    """
    # Create the graph with MIA state
    workflow = StateGraph(MIAState)

    # Add nodes for each agent
    workflow.add_node("supervisor", supervisor_agent)
    workflow.add_node("kpi_agent", kpi_agent)
    workflow.add_node("analyst_agent", analyst_agent)
    workflow.add_node("validator", validator_agent)
    workflow.add_node("visualization", visualization_agent)
    workflow.add_node("clarify", handle_clarification)

    # Set entry point
    workflow.set_entry_point("supervisor")

    # Add conditional routing after supervisor
    workflow.add_conditional_edges(
        "supervisor",
        route_after_supervisor,
        {
            "kpi_agent": "kpi_agent",
            "analyst_agent": "analyst_agent",
            "clarify": "clarify"
        }
    )

    # Route KPI and Analyst agents to validator
    workflow.add_edge("kpi_agent", "validator")
    workflow.add_edge("analyst_agent", "validator")

    # Clarify goes directly to end
    workflow.add_edge("clarify", END)

    # Validator goes to visualization (could add retry logic)
    workflow.add_conditional_edges(
        "validator",
        route_after_validation,
        {
            "visualization": "visualization",
            "retry": "supervisor"  # Could retry from supervisor
        }
    )

    # Visualization goes to end
    workflow.add_edge("visualization", END)

    return workflow


def get_compiled_graph():
    """
    Get the compiled MIA graph ready for execution.
    """
    workflow = create_mia_graph()
    return workflow.compile()


# Singleton compiled graph
_compiled_graph = None


def get_graph():
    """
    Get or create the compiled graph (singleton pattern).
    """
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = get_compiled_graph()
    return _compiled_graph


async def run_query(session_id: str, user_query: str, conversation_history: list = None) -> dict:
    """
    Run a user query through the MIA workflow.
    Checks trace cache first — returns cached result if same query was asked before.

    Args:
        session_id: Session identifier
        user_query: The user's question
        conversation_history: Previous messages (optional)

    Returns:
        Final state with answer
    """
    from datetime import datetime
    from app.core.trace_store import lookup_cached_result, save_trace

    # Check cache for repeated queries
    cached = lookup_cached_result(user_query)
    if cached:
        print(f"[Graph] Cache hit for query: {user_query[:80]}")
        return cached

    graph = get_graph()

    # Initialize state
    initial_state: MIAState = {
        "session_id": session_id,
        "user_query": user_query,
        "conversation_history": conversation_history or [],
        "route_type": None,
        "route_reason": None,
        "matched_kpi": None,
        "extracted_filters": None,
        "kpi_results": None,
        "generated_sql": None,
        "analyst_result": None,
        "is_valid": False,
        "validation_issues": [],
        "follow_up_question": None,
        "final_answer": None,
        "visualization_config": None,
        "agent_logs": []
    }

    # Run the graph
    try:
        final_state = await graph.ainvoke(initial_state)

        # Save trace for future cache hits
        agent_logs = [
            {
                "agent_name": log.get("agent_name", "Unknown"),
                "input_summary": log.get("input_summary", ""),
                "output_summary": log.get("output_summary", ""),
                "reasoning_summary": log.get("reasoning_summary"),
                "status": log.get("status", "unknown"),
                "timestamp": log.get("timestamp", ""),
            }
            for log in final_state.get("agent_logs", [])
        ]
        save_trace(user_query, final_state, agent_logs)

        return final_state
    except Exception as e:
        # Return error state
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

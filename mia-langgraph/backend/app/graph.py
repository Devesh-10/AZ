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
from app.agents.validator_agent import validator_agent, handle_clarification, handle_rejection


def route_after_supervisor(state: MIAState) -> Literal["kpi_agent", "analyst_agent", "clarify", "reject"]:
    """
    Determine next node based on supervisor's routing decision.
    """
    route_type = state.get("route_type")

    if route_type == "KPI":
        return "kpi_agent"
    elif route_type == "COMPLEX":
        return "analyst_agent"
    elif route_type == "CLARIFY":
        return "clarify"
    elif route_type == "REJECT":
        return "reject"
    else:
        # Default to analyst for unhandled cases
        return "analyst_agent"


def route_after_validation(state: MIAState) -> Literal["end", "retry"]:
    """
    Determine if response is ready to return or needs retry.
    For now, always end - retry logic can be added later.
    """
    is_valid = state.get("is_valid", False)

    # Could implement retry logic here
    # For now, always proceed to end
    return "end"


def create_mia_graph() -> StateGraph:
    """
    Create the MIA LangGraph workflow.

    Flow:
    1. Supervisor Agent - routes query
    2. KPI Agent OR Analyst Agent - processes query
    3. Validator Agent - validates response
    4. Return to user

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
    workflow.add_node("clarify", handle_clarification)
    workflow.add_node("reject", handle_rejection)

    # Set entry point
    workflow.set_entry_point("supervisor")

    # Add conditional routing after supervisor
    workflow.add_conditional_edges(
        "supervisor",
        route_after_supervisor,
        {
            "kpi_agent": "kpi_agent",
            "analyst_agent": "analyst_agent",
            "clarify": "clarify",
            "reject": "reject"
        }
    )

    # Route KPI and Analyst agents to validator
    workflow.add_edge("kpi_agent", "validator")
    workflow.add_edge("analyst_agent", "validator")

    # Clarify and reject go directly to end
    workflow.add_edge("clarify", END)
    workflow.add_edge("reject", END)

    # Validator goes to end (could add retry logic)
    workflow.add_conditional_edges(
        "validator",
        route_after_validation,
        {
            "end": END,
            "retry": "supervisor"  # Could retry from supervisor
        }
    )

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

    Args:
        session_id: Session identifier
        user_query: The user's question
        conversation_history: Previous messages (optional)

    Returns:
        Final state with answer
    """
    from datetime import datetime

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

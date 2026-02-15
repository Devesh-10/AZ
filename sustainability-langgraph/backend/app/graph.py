"""
LangGraph Workflow for Sustainability Insight Agent
Defines the agent orchestration graph.
"""

from typing import Literal
from datetime import datetime
from langgraph.graph import StateGraph, END

from app.models.state import SIAState
from app.agents.supervisor import supervisor_agent
from app.agents.kpi_agent import kpi_agent
from app.agents.analyst_agent import analyst_agent
from app.agents.validator_agent import validator_agent
from app.agents.visualization_agent import visualization_agent


def route_after_supervisor(state: SIAState) -> Literal["kpi_agent", "analyst_agent", "clarify"]:
    """Route to appropriate agent based on supervisor decision"""
    route_type = state.get("route_type", "COMPLEX")

    if route_type == "KPI":
        return "kpi_agent"
    elif route_type == "COMPLEX":
        return "analyst_agent"
    else:
        return "clarify"


def clarify_response(state: SIAState) -> dict:
    """Generate clarification response"""
    return {
        "final_answer": "I need more information to answer your question. Could you please clarify:\n\n"
                       "- What specific sustainability metric are you asking about? (energy, emissions, water, waste, EV fleet)\n"
                       "- Are you looking for current data or a trend analysis?\n"
                       "- Do you want data for a specific site, region, or time period?"
    }


def build_graph() -> StateGraph:
    """Build the LangGraph workflow"""
    workflow = StateGraph(SIAState)

    # Add nodes
    workflow.add_node("supervisor", supervisor_agent)
    workflow.add_node("kpi_agent", kpi_agent)
    workflow.add_node("analyst_agent", analyst_agent)
    workflow.add_node("validator", validator_agent)
    workflow.add_node("visualization", visualization_agent)
    workflow.add_node("clarify", clarify_response)

    # Set entry point
    workflow.set_entry_point("supervisor")

    # Add conditional edges from supervisor
    workflow.add_conditional_edges(
        "supervisor",
        route_after_supervisor,
        {
            "kpi_agent": "kpi_agent",
            "analyst_agent": "analyst_agent",
            "clarify": "clarify"
        }
    )

    # KPI agent -> Validator
    workflow.add_edge("kpi_agent", "validator")

    # Analyst agent -> Validator
    workflow.add_edge("analyst_agent", "validator")

    # Validator -> Visualization
    workflow.add_edge("validator", "visualization")

    # Visualization -> END
    workflow.add_edge("visualization", END)

    # Clarify -> END
    workflow.add_edge("clarify", END)

    return workflow.compile()


# Singleton compiled graph
_compiled_graph = None


def get_graph():
    """Get or create the compiled graph (singleton pattern)."""
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph()
    return _compiled_graph


async def run_query(query: str, session_id: str = None, conversation_history: list = None) -> dict:
    """
    Run a query through the SIA graph.

    Args:
        query: The user's question
        session_id: Session identifier
        conversation_history: Previous messages (optional)

    Returns:
        Final state with answer
    """
    import uuid

    if not session_id:
        session_id = str(uuid.uuid4())

    graph = get_graph()

    # Initialize state
    initial_state: SIAState = {
        "user_query": query,
        "session_id": session_id,
        "conversation_history": conversation_history or [],
        "route_type": None,
        "route_reason": None,
        "matched_kpi": None,
        "extracted_filters": None,
        "kpi_results": None,
        "analyst_result": None,
        "validation_passed": False,
        "validation_notes": None,
        "final_answer": None,
        "generated_sql": None,
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
            "validation_passed": False,
            "agent_logs": [{
                "agent_name": "System",
                "input_summary": query[:100],
                "output_summary": f"Error: {str(e)}",
                "reasoning_summary": None,
                "status": "error",
                "timestamp": datetime.now().isoformat()
            }]
        }

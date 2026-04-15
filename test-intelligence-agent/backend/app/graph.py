"""
LangGraph Workflow for Test Intelligence Agent
Defines the 7-step state machine with conditional branching.
"""

from typing import Literal, Callable, Awaitable
import asyncio
from langgraph.graph import StateGraph, END

from app.models.state import TIAState
from app.agents.orchestrator import orchestrator_agent
from app.agents.requirement_agent import requirement_agent
from app.agents.test_generation_agent import test_generation_agent
from app.agents.synthetic_data_agent import synthetic_data_agent
from app.agents.execution_agent import execution_agent
from app.agents.failure_analysis_agent import failure_analysis_agent
from app.agents.code_refactor_agent import code_refactor_agent
from app.agents.reporting_agent import reporting_agent


def handle_clarification(state: TIAState) -> dict:
    """Handle unclear queries by asking for clarification."""
    from app.tools.platform_catalogue import PLATFORM_CATALOGUE
    platform = state.get("selected_platform", "")
    config = PLATFORM_CATALOGUE.get(platform, {})
    platform_name = config.get("name", platform)
    sample_queries = config.get("sample_queries", [])

    samples = "\n".join(f"  - {q}" for q in sample_queries[:3])
    return {
        "final_answer": (
            f"I need a bit more detail about what you'd like to test on **{platform_name}**.\n\n"
            f"Try something like:\n{samples}\n\n"
            "Please specify the module, feature, or data pipeline you'd like to validate."
        )
    }


def route_after_orchestrator(state: TIAState) -> Literal["requirement_agent", "clarify"]:
    """Route based on whether orchestrator resolved the test scope."""
    if state.get("platform_config") and state.get("test_scope"):
        return "requirement_agent"
    return "clarify"


def route_after_test_generation(state: TIAState) -> Literal["synthetic_data_agent", "execution_agent"]:
    """Conditional: generate synthetic data only if needed."""
    if state.get("needs_synthetic_data", False):
        return "synthetic_data_agent"
    return "execution_agent"


def route_after_execution(state: TIAState) -> Literal["failure_analysis_agent", "reporting_agent"]:
    """Conditional: analyze failures only if tests failed."""
    if state.get("has_failures", False):
        return "failure_analysis_agent"
    return "reporting_agent"


def route_after_failure_analysis(state: TIAState) -> Literal["code_refactor_agent", "reporting_agent"]:
    """Conditional: suggest code fixes only for logic bugs."""
    if state.get("needs_code_refactor", False):
        return "code_refactor_agent"
    return "reporting_agent"


def create_tia_graph() -> StateGraph:
    """
    Create the TIA LangGraph workflow.

    Flow:
    Orchestrator -> Step 1: Requirement -> Step 2: TestGen
        -> [Step 3: Synthetic Data?] -> Step 4: Execution
        -> [Step 5: Failure Analysis?] -> [Step 6: Code Refactor?]
        -> Step 7: Reporting -> END
    """
    workflow = StateGraph(TIAState)

    # Add all nodes
    workflow.add_node("orchestrator", orchestrator_agent)
    workflow.add_node("requirement_agent", requirement_agent)
    workflow.add_node("test_generation_agent", test_generation_agent)
    workflow.add_node("synthetic_data_agent", synthetic_data_agent)
    workflow.add_node("execution_agent", execution_agent)
    workflow.add_node("failure_analysis_agent", failure_analysis_agent)
    workflow.add_node("code_refactor_agent", code_refactor_agent)
    workflow.add_node("reporting_agent", reporting_agent)
    workflow.add_node("clarify", handle_clarification)

    # Entry point
    workflow.set_entry_point("orchestrator")

    # Orchestrator -> Requirement OR Clarify
    workflow.add_conditional_edges(
        "orchestrator",
        route_after_orchestrator,
        {
            "requirement_agent": "requirement_agent",
            "clarify": "clarify"
        }
    )

    # Step 1 -> Step 2 (always)
    workflow.add_edge("requirement_agent", "test_generation_agent")

    # Step 2 -> Step 3 (conditional) OR Step 4
    workflow.add_conditional_edges(
        "test_generation_agent",
        route_after_test_generation,
        {
            "synthetic_data_agent": "synthetic_data_agent",
            "execution_agent": "execution_agent"
        }
    )

    # Step 3 -> Step 4 (always)
    workflow.add_edge("synthetic_data_agent", "execution_agent")

    # Step 4 -> Step 5 (conditional) OR Step 7
    workflow.add_conditional_edges(
        "execution_agent",
        route_after_execution,
        {
            "failure_analysis_agent": "failure_analysis_agent",
            "reporting_agent": "reporting_agent"
        }
    )

    # Step 5 -> Step 6 (conditional) OR Step 7
    workflow.add_conditional_edges(
        "failure_analysis_agent",
        route_after_failure_analysis,
        {
            "code_refactor_agent": "code_refactor_agent",
            "reporting_agent": "reporting_agent"
        }
    )

    # Step 6 -> Step 7 (always)
    workflow.add_edge("code_refactor_agent", "reporting_agent")

    # Step 7 -> END
    workflow.add_edge("reporting_agent", END)

    # Clarify -> END
    workflow.add_edge("clarify", END)

    return workflow


def get_compiled_graph():
    """Get the compiled TIA graph ready for execution."""
    workflow = create_tia_graph()
    return workflow.compile()


_compiled_graph = None


def get_graph():
    """Get or create the compiled graph (singleton)."""
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = get_compiled_graph()
    return _compiled_graph


def _build_initial_state(
    session_id: str,
    user_query: str,
    selected_platform: str,
    conversation_history: list | None = None,
    uploaded_document: str | None = None,
    uploaded_document_name: str | None = None,
) -> TIAState:
    """Build the initial state dict for the TIA pipeline."""
    return {
        "session_id": session_id,
        "user_query": user_query,
        "conversation_history": conversation_history or [],
        "selected_platform": selected_platform,
        "uploaded_document": uploaded_document,
        "uploaded_document_name": uploaded_document_name,
        "platform_config": None,
        "test_scope": None,
        "requirements": None,
        "requirement_summary": None,
        "test_cases": None,
        "test_generation_summary": None,
        "needs_synthetic_data": True,
        "synthetic_data": None,
        "test_results": None,
        "execution_summary": None,
        "has_failures": False,
        "failure_analyses": None,
        "needs_code_refactor": False,
        "refactor_suggestions": None,
        "compliance_report": None,
        "final_answer": None,
        "visualization_config": None,
        "timing_comparison": None,
        "agent_logs": []
    }


async def run_test_query(
    session_id: str,
    user_query: str,
    selected_platform: str,
    conversation_history: list = None,
    uploaded_document: str | None = None,
    uploaded_document_name: str | None = None,
) -> dict:
    """
    Run a test query through the TIA 7-step pipeline.
    """
    from datetime import datetime

    graph = get_graph()
    initial_state = _build_initial_state(
        session_id, user_query, selected_platform,
        conversation_history, uploaded_document, uploaded_document_name,
    )

    try:
        final_state = await graph.ainvoke(initial_state)
        return final_state
    except Exception as e:
        return {
            **initial_state,
            "final_answer": f"An error occurred during the test pipeline: {str(e)}",
            "agent_logs": [{
                "agent_name": "System",
                "step_number": 0,
                "input_summary": user_query[:100],
                "output_summary": f"Error: {str(e)}",
                "reasoning_summary": None,
                "status": "error",
                "timestamp": datetime.now().isoformat(),
                "duration_seconds": None,
                "is_conditional": False,
                "was_executed": True
            }]
        }


async def run_test_query_streaming(
    session_id: str,
    user_query: str,
    selected_platform: str,
    conversation_history: list | None = None,
    uploaded_document: str | None = None,
    uploaded_document_name: str | None = None,
    on_agent_complete: Callable[[dict], Awaitable[None]] | None = None,
) -> dict:
    """
    Run the TIA pipeline with streaming: emits an event after each agent node completes.
    Uses LangGraph's astream to iterate over node outputs.
    """
    from datetime import datetime

    graph = get_graph()
    initial_state = _build_initial_state(
        session_id, user_query, selected_platform,
        conversation_history, uploaded_document, uploaded_document_name,
    )

    final_state = dict(initial_state)

    try:
        async for event in graph.astream(initial_state, stream_mode="updates"):
            # event is a dict: {node_name: state_update}
            for node_name, state_update in event.items():
                # Merge updates into our running state
                if isinstance(state_update, dict):
                    for key, value in state_update.items():
                        if key == "agent_logs" and isinstance(value, list):
                            existing = final_state.get("agent_logs", [])
                            if existing is None:
                                existing = []
                            final_state["agent_logs"] = existing + value
                        elif key == "conversation_history":
                            pass  # managed by LangGraph reducer
                        else:
                            final_state[key] = value

                    # Emit the latest agent log if callback provided
                    if on_agent_complete and state_update.get("agent_logs"):
                        new_logs = state_update["agent_logs"]
                        for log in new_logs:
                            await on_agent_complete({
                                "type": "agent_complete",
                                "node": node_name,
                                "log": log,
                            })

        return final_state

    except Exception as e:
        error_log = {
            "agent_name": "System",
            "step_number": 0,
            "input_summary": user_query[:100],
            "output_summary": f"Error: {str(e)}",
            "reasoning_summary": None,
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": None,
            "is_conditional": False,
            "was_executed": True,
        }
        if on_agent_complete:
            await on_agent_complete({
                "type": "error",
                "node": "system",
                "log": error_log,
            })
        final_state["final_answer"] = f"An error occurred during the test pipeline: {str(e)}"
        existing_logs = final_state.get("agent_logs") or []
        final_state["agent_logs"] = existing_logs + [error_log]
        return final_state

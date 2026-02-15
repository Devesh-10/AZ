"""
Validator Agent for Sustainability Insight Agent
Validates responses before returning to user.
"""

from datetime import datetime

from app.models.state import SIAState, AgentLog


def validator_agent(state: SIAState) -> dict:
    """
    Validator Agent - performs basic validation on responses.

    Args:
        state: Current SIA state with results

    Returns:
        Updated state with validation status
    """
    final_answer = state.get("final_answer", "")
    kpi_results = state.get("kpi_results")
    analyst_result = state.get("analyst_result")

    validation_notes = []
    validation_passed = True

    # Check if we have any response
    if not final_answer:
        validation_passed = False
        validation_notes.append("No response generated")

    # Check response length
    if final_answer and len(final_answer) < 20:
        validation_passed = False
        validation_notes.append("Response too short")

    # Check for error indicators
    error_patterns = ["error", "failed", "could not", "unable to"]
    if any(pattern in final_answer.lower() for pattern in error_patterns):
        validation_notes.append("Response may contain error messages")

    # Verify data presence for KPI queries
    if kpi_results and len(kpi_results) > 0:
        for kpi in kpi_results:
            if not kpi.get("data_points"):
                validation_notes.append(f"KPI {kpi.get('kpi_name', 'Unknown')} has no data points")

    log_entry: AgentLog = {
        "agent_name": "Validator",
        "input_summary": f"Answer length: {len(final_answer)} chars",
        "output_summary": "Passed basic validation" if validation_passed else "Validation concerns found",
        "reasoning_summary": "; ".join(validation_notes) if validation_notes else "Quick validation passed",
        "status": "success" if validation_passed else "error",
        "timestamp": datetime.now().isoformat()
    }

    return {
        "validation_passed": validation_passed,
        "validation_notes": "; ".join(validation_notes) if validation_notes else None,
        "agent_logs": [log_entry]
    }

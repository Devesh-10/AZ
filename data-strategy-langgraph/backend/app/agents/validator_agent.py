"""
Validator Agent for DSA
Validates responses before returning to user.
"""

from datetime import datetime
from langchain_aws import ChatBedrock
from langchain_core.messages import HumanMessage, SystemMessage

from app.core.config import get_settings
from app.models.state import DSAState, AgentLog

settings = get_settings()

VALIDATOR_SYSTEM_PROMPT = """You are a Validator Agent for the Data Strategy Agent (DSA).
Your role is to validate data quality analysis responses before they are sent to users.

## Validation Criteria
1. **Accuracy**: Does the response correctly answer the user's data quality question?
2. **Completeness**: Does it include relevant metrics and percentages?
3. **Clarity**: Is the response clear and actionable?
4. **Data Integrity**: Are the numbers and calculations consistent?
5. **Professionalism**: Is the tone appropriate for data strategy leadership?

## Output Format (JSON)
{{
    "is_valid": true/false,
    "issues": ["issue1", "issue2"],
    "suggestions": ["suggestion1"],
    "confidence": 0.0-1.0
}}
"""


def validator_agent(state: DSAState) -> dict:
    import json

    final_answer = state.get("final_answer")
    user_query = state["user_query"]
    route_type = state.get("route_type")

    if not final_answer:
        log_entry = AgentLog(
            agent_name="Validator",
            input_summary="No answer to validate",
            output_summary="Validation failed - no answer",
            reasoning_summary=None,
            status="error",
            timestamp=datetime.now().isoformat()
        )
        return {
            "is_valid": False,
            "validation_issues": ["No answer was generated to validate"],
            "agent_logs": [log_entry]
        }

    issues = []

    if len(final_answer) < 20:
        issues.append("Response is too short to be meaningful")

    error_phrases = ["error", "failed", "couldn't", "unable to", "exception"]
    has_error = any(phrase in final_answer.lower() for phrase in error_phrases)

    if route_type == "KPI":
        has_numbers = any(char.isdigit() for char in final_answer)
        if not has_numbers:
            issues.append("DQ metric response should contain numerical data")

    placeholder_phrases = ["[insert", "[todo", "xxx", "placeholder"]
    has_placeholder = any(phrase in final_answer.lower() for phrase in placeholder_phrases)
    if has_placeholder:
        issues.append("Response contains placeholder text")

    if not issues and not has_error:
        log_entry = AgentLog(
            agent_name="Validator",
            input_summary=f"Validating {route_type} response",
            output_summary="Passed basic validation",
            reasoning_summary="Quick validation passed",
            status="success",
            timestamp=datetime.now().isoformat()
        )
        return {
            "is_valid": True,
            "validation_issues": [],
            "agent_logs": [log_entry]
        }

    try:
        llm = ChatBedrock(
            model_id=settings.kpi_model,
            region_name=settings.aws_region
        )

        messages = [
            SystemMessage(content=VALIDATOR_SYSTEM_PROMPT),
            HumanMessage(content=f"""Validate this response:

User Query: {user_query}
Route Type: {route_type}

Response to Validate:
{final_answer}

Initial Issues Found: {issues}

Provide validation result as JSON.""")
        ]

        response = llm.invoke(messages)

        try:
            result = json.loads(response.content)
            is_valid = result.get("is_valid", False)
            validation_issues = result.get("issues", []) + issues

            log_entry = AgentLog(
                agent_name="Validator",
                input_summary=f"Validating {route_type} response",
                output_summary=f"Valid: {is_valid}, Issues: {len(validation_issues)}",
                reasoning_summary=f"Confidence: {result.get('confidence', 'N/A')}",
                status="success" if is_valid else "error",
                timestamp=datetime.now().isoformat()
            )

            return {
                "is_valid": is_valid,
                "validation_issues": validation_issues,
                "agent_logs": [log_entry]
            }
        except json.JSONDecodeError:
            pass
    except Exception:
        pass

    is_valid = len(issues) == 0
    log_entry = AgentLog(
        agent_name="Validator",
        input_summary=f"Validating {route_type} response",
        output_summary=f"Fallback validation: Valid={is_valid}",
        reasoning_summary=f"Issues: {issues}",
        status="success" if is_valid else "error",
        timestamp=datetime.now().isoformat()
    )

    return {
        "is_valid": is_valid,
        "validation_issues": issues,
        "agent_logs": [log_entry]
    }


def handle_clarification(state: DSAState) -> dict:
    user_query = state["user_query"]

    clarification_response = f"""I'd like to help you better. Could you please clarify your question?

Your query: "{user_query}"

Here are some things I can help with:
- **Data Completeness**: "How complete is our batch data?" or "Missing values in LIMS"
- **Data Accuracy**: "Are yield values within valid range?" or "Equipment reference integrity"
- **Data Consistency**: "Do MES and analytics data match?" or "Cross-system reconciliation"
- **Data Profiling**: "Profile the batch status table" or "Show me data distributions"
- **Overall Quality**: "What is our overall data quality score?"

Please provide more details about what you'd like to know."""

    log_entry = AgentLog(
        agent_name="Validator",
        input_summary=f"Clarification needed for: {user_query[:50]}",
        output_summary="Generated clarification request",
        reasoning_summary=None,
        status="success",
        timestamp=datetime.now().isoformat()
    )

    return {
        "final_answer": clarification_response,
        "follow_up_question": clarification_response,
        "is_valid": True,
        "agent_logs": [log_entry]
    }

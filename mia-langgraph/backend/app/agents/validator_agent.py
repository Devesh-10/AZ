"""
Validator Agent for MIA
Validates responses before returning to user.
Ensures accuracy, completeness, and appropriate formatting.
"""

from datetime import datetime
from langchain_aws import ChatBedrock
from langchain_core.messages import HumanMessage, SystemMessage

from app.core.config import get_settings
from app.models.state import MIAState, AgentLog

settings = get_settings()

VALIDATOR_SYSTEM_PROMPT = """You are a Validator Agent for the Manufacturing Insight Agent (MIA).
Your role is to validate responses before they are sent to users.

## Validation Criteria
1. **Accuracy**: Does the response correctly answer the user's question?
2. **Completeness**: Does it include all relevant information?
3. **Clarity**: Is the response clear and easy to understand?
4. **Data Integrity**: Are the numbers and facts consistent?
5. **Professionalism**: Is the tone appropriate for manufacturing professionals?

## Validation Rules
- Responses should directly address the user's query
- Numbers should have appropriate units
- RAG status should be explained if mentioned
- Avoid vague or misleading statements
- Ensure manufacturing terminology is used correctly

## Output Format (JSON)
{{
    "is_valid": true/false,
    "issues": ["issue1", "issue2"],
    "suggestions": ["suggestion1"],
    "confidence": 0.0-1.0
}}

If is_valid is false, provide specific issues that need to be addressed.
"""


def validator_agent(state: MIAState) -> dict:
    """
    Validator Agent that validates responses before sending to user.

    Args:
        state: Current MIA state with final answer

    Returns:
        Updated state with validation results
    """
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

    # Basic validation checks (fast, no LLM needed)
    issues = []

    # Check minimum length
    if len(final_answer) < 20:
        issues.append("Response is too short to be meaningful")

    # Check for error indicators
    error_phrases = ["error", "failed", "couldn't", "unable to", "exception"]
    has_error = any(phrase in final_answer.lower() for phrase in error_phrases)

    # Check for data presence when expected
    if route_type == "KPI":
        has_numbers = any(char.isdigit() for char in final_answer)
        if not has_numbers:
            issues.append("KPI response should contain numerical data")

    # Check for placeholder text
    placeholder_phrases = ["[insert", "[todo", "xxx", "placeholder"]
    has_placeholder = any(phrase in final_answer.lower() for phrase in placeholder_phrases)
    if has_placeholder:
        issues.append("Response contains placeholder text")

    # If basic checks pass and no LLM validation needed, approve
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

    # Use LLM for deeper validation if issues detected
    try:
        llm = ChatBedrock(
            model_id=settings.kpi_model,  # Use lighter model for validation
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
            # LLM didn't return valid JSON, use basic validation result
            pass

    except Exception as e:
        # LLM error, fall back to basic validation
        pass

    # Fallback: if we have issues, mark as invalid; otherwise valid
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


def handle_clarification(state: MIAState) -> dict:
    """
    Handle queries that need clarification.
    """
    user_query = state["user_query"]

    clarification_response = f"""I'd like to help you better. Could you please clarify your question?

Your query: "{user_query}"

Here are some things I can help with:
- **KPI queries**: "What is the batch yield?", "Show me RFT performance"
- **Trend analysis**: "How has OEE changed over the last 3 months?"
- **Comparisons**: "Compare yield between SKU_123 and SKU_456"
- **Status checks**: "Which batches are quarantined?"

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


def handle_rejection(state: MIAState) -> dict:
    """
    Handle queries that are outside the manufacturing domain.
    """
    user_query = state["user_query"]

    rejection_response = f"""I'm sorry, but I can only help with manufacturing-related questions.

Your query "{user_query}" appears to be outside my area of expertise.

I can assist you with:
- Production KPIs (yield, RFT, OEE, cycle time)
- Batch and order status tracking
- Manufacturing trends and analysis
- Quality metrics and deviations

Please ask a manufacturing-related question, and I'll be happy to help!"""

    log_entry = AgentLog(
        agent_name="Validator",
        input_summary=f"Rejected query: {user_query[:50]}",
        output_summary="Generated rejection response",
        reasoning_summary="Query outside manufacturing domain",
        status="success",
        timestamp=datetime.now().isoformat()
    )

    return {
        "final_answer": rejection_response,
        "is_valid": True,
        "agent_logs": [log_entry]
    }

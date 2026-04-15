"""
Code Refactor Agent (Step 6 - CONDITIONAL) for the Test Intelligence Agent.
Generates code fix suggestions for failures categorised as "Logic Bug".
Only runs when needs_code_refactor is True.
"""

import json
import time
from datetime import datetime

from langchain_aws import ChatBedrockConverse
from langchain_core.messages import SystemMessage, HumanMessage

from app.core.config import get_settings
from app.models.state import TIAState, AgentLog, CodeRefactorSuggestion

CODE_REFACTOR_SYSTEM_PROMPT = """You are a Code Refactoring Expert for AstraZeneca's Test Intelligence Agent.

You operate in a GxP-regulated pharmaceutical R&D environment. Your job is to generate
precise, safe code fix suggestions for failures that have been identified as "Logic Bug"
by the Failure Analysis Agent.

For each logic bug, you must produce a concrete code change that:
1. Fixes the identified root cause.
2. Does not introduce regressions.
3. Follows the platform's tech stack conventions.
4. Includes clear inline comments explaining the fix.
5. Is conservative - minimal change to resolve the defect.

Output **strictly valid JSON** - an array of code refactor suggestion objects:

[
    {
        "test_id": "TC3",
        "file_path": "src/validators/batch_validator.py",
        "original_code": "def validate_yield(value):\\n    return value > 0",
        "suggested_code": "def validate_yield(value):\\n    # Fix: boundary must be >= 0 per GxP spec\\n    return value >= 0",
        "explanation": "The boundary check was exclusive (>) instead of inclusive (>=). Batch yield of exactly 0% is a valid edge case for failed batches per GxP SOP-2024-014.",
        "confidence": 0.92
    }
]

Guidelines:
- file_path should be a plausible path within the platform's tech stack.
- original_code and suggested_code should be realistic, syntactically valid snippets.
- Use the platform's primary language (Python, Java, SAS, R, etc.).
- confidence is a float 0.0-1.0 indicating how certain you are the fix is correct.
- Keep code snippets concise (5-15 lines max).
- Include GxP/regulatory context in the explanation where relevant.

Return ONLY the JSON array, no surrounding text.
"""


def code_refactor_agent(state: TIAState) -> dict:
    """
    Code Refactor Agent (Step 6 - CONDITIONAL).

    Only runs when needs_code_refactor is True. Takes failure analyses
    filtered to "Logic Bug" category and generates concrete code fix
    suggestions using the LLM.

    Args:
        state: Current TIA state with failure_analyses and
               needs_code_refactor flag.

    Returns:
        Partial state update with refactor_suggestions and agent_logs.
    """
    start_time = time.time()
    needs_code_refactor = state.get("needs_code_refactor", False)
    failure_analyses = state.get("failure_analyses") or []
    test_cases = state.get("test_cases") or []
    platform_config = state.get("platform_config") or {}
    platform_name = platform_config.get("name", "Unknown Platform")
    tech_stack = platform_config.get("tech_stack", [])

    # ------------------------------------------------------------------
    # Guard: skip if not needed
    # ------------------------------------------------------------------
    if not needs_code_refactor:
        duration = round(time.time() - start_time, 2)
        log_entry: AgentLog = {
            "agent_name": "Code Refactor Agent",
            "step_number": 6,
            "input_summary": "needs_code_refactor=False",
            "output_summary": "Skipped - no code refactoring required",
            "reasoning_summary": "Failure analysis did not identify any Logic Bug categories.",
            "status": "skipped",
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": duration,
            "is_conditional": True,
            "was_executed": False,
        }
        return {
            "refactor_suggestions": [],
            "agent_logs": [log_entry],
        }

    # Filter to Logic Bug failures only
    logic_bugs = [fa for fa in failure_analyses if fa["category"] == "Logic Bug"]

    if not logic_bugs:
        duration = round(time.time() - start_time, 2)
        log_entry: AgentLog = {
            "agent_name": "Code Refactor Agent",
            "step_number": 6,
            "input_summary": "needs_code_refactor=True but no Logic Bug failures found",
            "output_summary": "Skipped - no Logic Bug categories in failure analyses",
            "reasoning_summary": "Flag mismatch: needs_code_refactor was True but no failures have 'Logic Bug' category.",
            "status": "skipped",
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": duration,
            "is_conditional": True,
            "was_executed": False,
        }
        return {
            "refactor_suggestions": [],
            "agent_logs": [log_entry],
        }

    try:
        # ------------------------------------------------------------------
        # 1. Build context for LLM
        # ------------------------------------------------------------------
        tc_map = {tc["test_id"]: tc for tc in test_cases}

        bug_text_parts = []
        for bug in logic_bugs:
            tc = tc_map.get(bug["test_id"], {})
            bug_text_parts.append(
                f"### {bug['test_id']}: {tc.get('test_name', 'Unknown Test')}\n"
                f"Severity: {bug['severity']}\n"
                f"Root Cause: {bug['root_cause']}\n"
                f"Suggested Fix Direction: {bug['suggested_fix']}\n"
                f"Test Description: {tc.get('description', 'N/A')}\n"
                f"Expected Result: {tc.get('expected_result', 'N/A')}"
            )

        bug_text = "\n\n".join(bug_text_parts)

        refactor_prompt = (
            f"## Platform: {platform_name}\n"
            f"## Tech Stack: {', '.join(tech_stack)}\n"
            f"## Primary Language: {tech_stack[0] if tech_stack else 'Python'}\n\n"
            f"## Logic Bugs Requiring Code Fixes ({len(logic_bugs)} bugs)\n\n{bug_text}\n\n"
            f"Generate code fix suggestions for all {len(logic_bugs)} logic bugs. "
            "Use the platform's primary language for code snippets. "
            "Return ONLY a JSON array of code refactor suggestion objects."
        )

        # ------------------------------------------------------------------
        # 2. Invoke LLM
        # ------------------------------------------------------------------
        settings = get_settings()
        llm = ChatBedrockConverse(
            model=settings.refactor_model,
            region_name=settings.aws_region,
            temperature=0.1,
            max_tokens=8192,
        )

        messages = [
            SystemMessage(content=CODE_REFACTOR_SYSTEM_PROMPT),
            HumanMessage(content=refactor_prompt),
        ]

        response = llm.invoke(messages)
        raw = response.content.strip()

        # Strip markdown fences
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
        if raw.endswith("```"):
            raw = raw.rsplit("```", 1)[0]
        raw = raw.strip()

        # ------------------------------------------------------------------
        # 3. Parse and normalise
        # ------------------------------------------------------------------
        parsed = json.loads(raw)

        refactor_suggestions: list[CodeRefactorSuggestion] = []
        for item in parsed:
            suggestion: CodeRefactorSuggestion = {
                "test_id": item.get("test_id", ""),
                "file_path": item.get("file_path", "unknown"),
                "original_code": item.get("original_code", ""),
                "suggested_code": item.get("suggested_code", ""),
                "explanation": item.get("explanation", ""),
                "confidence": min(max(float(item.get("confidence", 0.8)), 0.0), 1.0),
            }
            refactor_suggestions.append(suggestion)

        avg_confidence = (
            round(sum(s["confidence"] for s in refactor_suggestions) / len(refactor_suggestions), 2)
            if refactor_suggestions else 0.0
        )

        duration = round(time.time() - start_time, 2)
        log_entry: AgentLog = {
            "agent_name": "Code Refactor Agent",
            "step_number": 6,
            "input_summary": f"{len(logic_bugs)} logic bugs to fix",
            "output_summary": (
                f"{len(refactor_suggestions)} code fix suggestions generated "
                f"(avg confidence: {avg_confidence})"
            ),
            "reasoning_summary": (
                f"Generated code fixes for {len(refactor_suggestions)} logic bugs using "
                f"{tech_stack[0] if tech_stack else 'Python'} conventions. "
                f"Average fix confidence: {avg_confidence}."
            ),
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": duration,
            "is_conditional": True,
            "was_executed": True,
        }

        return {
            "refactor_suggestions": refactor_suggestions,
            "agent_logs": [log_entry],
        }

    except Exception as e:
        duration = round(time.time() - start_time, 2)
        log_entry: AgentLog = {
            "agent_name": "Code Refactor Agent",
            "step_number": 6,
            "input_summary": f"{len(logic_bugs)} logic bugs",
            "output_summary": f"Error: {str(e)[:200]}",
            "reasoning_summary": "Unhandled exception during code refactor suggestion generation.",
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": duration,
            "is_conditional": True,
            "was_executed": True,
        }
        return {
            "refactor_suggestions": [],
            "agent_logs": [log_entry],
        }

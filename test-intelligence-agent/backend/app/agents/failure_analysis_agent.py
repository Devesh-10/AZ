"""
Failure Analysis Agent (Step 5 - CONDITIONAL) for the Test Intelligence Agent.
Analyses failed test results to determine root cause, severity, and category.
Only runs when has_failures is True.
"""

import json
import time
from datetime import datetime

from langchain_aws import ChatBedrockConverse
from langchain_core.messages import SystemMessage, HumanMessage

from app.core.config import get_settings
from app.models.state import TIAState, AgentLog, FailureAnalysis

FAILURE_ANALYSIS_SYSTEM_PROMPT = """You are a Failure Analysis Expert for AstraZeneca's Test Intelligence Agent.

You operate in a GxP-regulated pharmaceutical R&D environment. Your job is to perform
root cause analysis (RCA) on failed test cases. For each failure you must determine:

1. **root_cause** - A detailed, technical explanation of why the test failed.
2. **category** - Classify the root cause into exactly one of:
   - "Logic Bug"       - Code-level defect in business logic (can be fixed by code change)
   - "Data Issue"      - Incorrect, missing, or corrupted test/source data
   - "Configuration"   - Misconfigured setting, threshold, or parameter
   - "Environment"     - Infrastructure, dependency, or runtime environment issue
   - "Integration"     - Interface mismatch between systems/modules
3. **severity** - Impact classification:
   - "Critical" - Patient safety or regulatory compliance risk
   - "High"     - Core functionality broken, no workaround
   - "Medium"   - Functionality impaired but workaround exists
   - "Low"      - Minor cosmetic or edge-case issue
4. **suggested_fix** - A concrete recommendation for remediation.

IMPORTANT: At least one failure should be categorised as "Logic Bug" so that the
downstream Code Refactor Agent can generate a code fix suggestion.

Output **strictly valid JSON** - an array of failure analysis objects:

[
    {
        "test_id": "TC3",
        "root_cause": "Detailed technical root cause explanation",
        "category": "Logic Bug",
        "severity": "High",
        "suggested_fix": "Concrete fix recommendation"
    }
]

Return ONLY the JSON array, no surrounding text.
"""


def failure_analysis_agent(state: TIAState) -> dict:
    """
    Failure Analysis Agent (Step 5 - CONDITIONAL).

    Only runs when has_failures is True. Analyses each failed test result
    to determine root cause, severity, category, and suggested fix.
    Sets needs_code_refactor = True if any failure is categorised as
    "Logic Bug".

    Args:
        state: Current TIA state with test_results and has_failures flag.

    Returns:
        Partial state update with failure_analyses, needs_code_refactor,
        and agent_logs.
    """
    start_time = time.time()
    has_failures = state.get("has_failures", False)
    test_results = state.get("test_results") or []
    test_cases = state.get("test_cases") or []
    platform_config = state.get("platform_config") or {}
    platform_name = platform_config.get("name", "Unknown Platform")

    # ------------------------------------------------------------------
    # Guard: skip if no failures
    # ------------------------------------------------------------------
    if not has_failures:
        duration = round(time.time() - start_time, 2)
        log_entry: AgentLog = {
            "agent_name": "Failure Analysis Agent",
            "step_number": 5,
            "input_summary": "has_failures=False",
            "output_summary": "Skipped - no failures to analyse",
            "reasoning_summary": "All tests passed; failure analysis not required.",
            "status": "skipped",
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": duration,
            "is_conditional": True,
            "was_executed": False,
        }
        return {
            "failure_analyses": [],
            "needs_code_refactor": False,
            "agent_logs": [log_entry],
        }

    # Filter to only FAIL results
    failed_results = [r for r in test_results if r["status"] == "FAIL"]

    if not failed_results:
        duration = round(time.time() - start_time, 2)
        log_entry: AgentLog = {
            "agent_name": "Failure Analysis Agent",
            "step_number": 5,
            "input_summary": "has_failures=True but no FAIL results found",
            "output_summary": "Skipped - no FAIL status results in test_results",
            "reasoning_summary": "Flag mismatch: has_failures was True but no test results have FAIL status.",
            "status": "skipped",
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": duration,
            "is_conditional": True,
            "was_executed": False,
        }
        return {
            "failure_analyses": [],
            "needs_code_refactor": False,
            "agent_logs": [log_entry],
        }

    try:
        # ------------------------------------------------------------------
        # 1. Build context for LLM
        # ------------------------------------------------------------------
        # Map test cases by test_id for cross-reference
        tc_map = {tc["test_id"]: tc for tc in test_cases}

        failure_text_parts = []
        for result in failed_results:
            tc = tc_map.get(result["test_id"], {})
            failure_text_parts.append(
                f"### {result['test_id']}: {result['test_name']}\n"
                f"Category: {tc.get('category', 'Unknown')} | "
                f"Priority: {tc.get('priority', 'Unknown')}\n"
                f"Expected: {tc.get('expected_result', 'N/A')}\n"
                f"Actual: {result['actual_result']}\n"
                f"Error: {result['error_message'] or 'No error message'}"
            )

        failure_text = "\n\n".join(failure_text_parts)

        analysis_prompt = (
            f"## Platform: {platform_name}\n"
            f"## Platform Description: {platform_config.get('description', 'N/A')}\n\n"
            f"## Failed Test Cases ({len(failed_results)} failures)\n\n{failure_text}\n\n"
            "Perform root cause analysis on each failed test. "
            "Ensure at least one failure is categorised as 'Logic Bug'. "
            "Return ONLY a JSON array of failure analysis objects."
        )

        # ------------------------------------------------------------------
        # 2. Invoke LLM
        # ------------------------------------------------------------------
        settings = get_settings()
        llm = ChatBedrockConverse(
            model=settings.analysis_model,
            region_name=settings.aws_region,
            temperature=0.1,
            max_tokens=4096,
        )

        messages = [
            SystemMessage(content=FAILURE_ANALYSIS_SYSTEM_PROMPT),
            HumanMessage(content=analysis_prompt),
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

        failure_analyses: list[FailureAnalysis] = []
        for item in parsed:
            analysis: FailureAnalysis = {
                "test_id": item.get("test_id", ""),
                "root_cause": item.get("root_cause", "Unknown root cause"),
                "category": item.get("category", "Data Issue"),
                "severity": item.get("severity", "Medium"),
                "suggested_fix": item.get("suggested_fix", "Further investigation required"),
            }
            failure_analyses.append(analysis)

        # ------------------------------------------------------------------
        # 4. Determine if code refactor is needed
        # ------------------------------------------------------------------
        logic_bugs = [fa for fa in failure_analyses if fa["category"] == "Logic Bug"]
        needs_code_refactor = len(logic_bugs) > 0

        severity_breakdown = {}
        for fa in failure_analyses:
            severity_breakdown[fa["severity"]] = severity_breakdown.get(fa["severity"], 0) + 1
        severity_text = ", ".join(f"{count} {sev}" for sev, count in sorted(severity_breakdown.items()))

        category_breakdown = {}
        for fa in failure_analyses:
            category_breakdown[fa["category"]] = category_breakdown.get(fa["category"], 0) + 1
        category_text = ", ".join(f"{count} {cat}" for cat, count in sorted(category_breakdown.items()))

        duration = round(time.time() - start_time, 2)
        log_entry: AgentLog = {
            "agent_name": "Failure Analysis Agent",
            "step_number": 5,
            "input_summary": f"{len(failed_results)} failed tests to analyse",
            "output_summary": (
                f"Analysed {len(failure_analyses)} failures. "
                f"Categories: {category_text}. Severities: {severity_text}. "
                f"Code refactor needed: {needs_code_refactor}"
            ),
            "reasoning_summary": (
                f"Root cause analysis complete. {len(logic_bugs)} logic bug(s) identified "
                f"requiring code refactor. {category_text}."
            ),
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": duration,
            "is_conditional": True,
            "was_executed": True,
        }

        return {
            "failure_analyses": failure_analyses,
            "needs_code_refactor": needs_code_refactor,
            "agent_logs": [log_entry],
        }

    except Exception as e:
        duration = round(time.time() - start_time, 2)
        log_entry: AgentLog = {
            "agent_name": "Failure Analysis Agent",
            "step_number": 5,
            "input_summary": f"{len(failed_results)} failed tests",
            "output_summary": f"Error: {str(e)[:200]}",
            "reasoning_summary": "Unhandled exception during failure analysis.",
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": duration,
            "is_conditional": True,
            "was_executed": True,
        }
        return {
            "failure_analyses": [],
            "needs_code_refactor": False,
            "agent_logs": [log_entry],
        }

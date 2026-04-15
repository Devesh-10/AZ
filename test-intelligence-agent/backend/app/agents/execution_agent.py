"""
Execution Agent (Step 4) for the Test Intelligence Agent.
Simulates test execution for each test case using LLM evaluation.
Manual equivalent: ~2 days  |  Agent time: ~2 minutes
"""

import json
import time
from datetime import datetime

from langchain_aws import ChatBedrockConverse
from langchain_core.messages import SystemMessage, HumanMessage

from app.core.config import get_settings
from app.models.state import TIAState, AgentLog, TestResult

EXECUTION_SYSTEM_PROMPT = """You are a Test Execution Engine for AstraZeneca's Test Intelligence Agent.

You operate in a GxP-regulated pharmaceutical R&D environment. Your job is to simulate
the execution of test cases against a platform, evaluating each test case with its
associated synthetic data (if any) and determining PASS/FAIL outcomes.

IMPORTANT FOR REALISTIC DEMO RESULTS:
- Aim for 70-85% of tests to PASS.
- Make 1-2 tests FAIL to demonstrate the failure analysis and code refactor pipeline.
- At least one failure should be a "Logic Bug" (code-level issue that can be fixed).
- Failures should be plausible and specific to the platform domain.
- PASS results should include brief confirmation of what was validated.
- FAIL results should include a specific, technical error_message.

For each test case, simulate execution and produce a result.

Output **strictly valid JSON** - an array of test result objects:

[
    {
        "test_id": "TC1",
        "test_name": "Name from the test case",
        "status": "PASS",
        "execution_time_seconds": 1.2,
        "actual_result": "Brief description of what happened",
        "error_message": null
    },
    {
        "test_id": "TC3",
        "test_name": "Name from the test case",
        "status": "FAIL",
        "execution_time_seconds": 2.8,
        "actual_result": "What actually happened (the defect)",
        "error_message": "Specific technical error message"
    }
]

Guidelines:
- execution_time_seconds: realistic simulation times (0.5-5.0 seconds per test).
- For PASS: actual_result should describe successful validation; error_message is null.
- For FAIL: actual_result describes the observed defect; error_message gives the technical error.
- status must be one of: "PASS", "FAIL", "SKIP", "ERROR".
- Make failures interesting and domain-specific (e.g. "MedDRA PT code maps to wrong SOC",
  "Batch yield calculation rounds incorrectly at boundary", "SDTM domain DM missing
  required RFSTDTC variable").

Return ONLY the JSON array, no surrounding text.
"""


def execution_agent(state: TIAState) -> dict:
    """
    Execution Agent (Step 4).

    Simulates test execution for each test case. Uses LLM to evaluate test
    cases against synthetic data and produce realistic PASS/FAIL outcomes.
    Ensures ~70-85% pass rate with 1-2 failures to trigger downstream agents.

    Args:
        state: Current TIA state with test_cases and synthetic_data.

    Returns:
        Partial state update with test_results, execution_summary,
        has_failures, needs_code_refactor, visualization_config,
        and agent_logs.
    """
    start_time = time.time()
    test_cases = state.get("test_cases") or []
    synthetic_data = state.get("synthetic_data") or []
    platform_config = state.get("platform_config") or {}
    platform_name = platform_config.get("name", "Unknown Platform")
    test_scope = state.get("test_scope", "")

    if not test_cases:
        duration = round(time.time() - start_time, 2)
        log_entry: AgentLog = {
            "agent_name": "Execution Agent",
            "step_number": 4,
            "input_summary": "No test cases to execute",
            "output_summary": "Skipped - no test cases provided",
            "reasoning_summary": "Upstream test generation produced no test cases.",
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": duration,
            "is_conditional": False,
            "was_executed": True,
        }
        return {
            "test_results": [],
            "execution_summary": "No test cases to execute.",
            "has_failures": False,
            "needs_code_refactor": False,
            "visualization_config": None,
            "agent_logs": [log_entry],
        }

    try:
        # ------------------------------------------------------------------
        # 1. Build test context for LLM
        # ------------------------------------------------------------------
        # Map synthetic data by test_id for easy lookup
        data_map = {sd["test_id"]: sd["data_payload"] for sd in synthetic_data}

        tc_text_parts = []
        for tc in test_cases:
            data_snippet = data_map.get(tc["test_id"])
            data_str = json.dumps(data_snippet, indent=2)[:500] if data_snippet else "No synthetic data"
            tc_text_parts.append(
                f"### {tc['test_id']}: {tc['test_name']}\n"
                f"Category: {tc['category']} | Priority: {tc['priority']}\n"
                f"Description: {tc['description']}\n"
                f"Expected Result: {tc['expected_result']}\n"
                f"Test Data:\n```json\n{data_str}\n```"
            )

        tc_text = "\n\n".join(tc_text_parts)

        execution_prompt = (
            f"## Platform: {platform_name}\n"
            f"## Test Scope: {test_scope}\n\n"
            f"## Test Cases to Execute ({len(test_cases)} total)\n\n{tc_text}\n\n"
            f"Execute all {len(test_cases)} test cases. "
            f"Target ~70-85% pass rate. Make 1-2 tests FAIL with realistic, "
            f"domain-specific defects (at least one should be a code logic bug). "
            "Return ONLY a JSON array of test result objects."
        )

        # ------------------------------------------------------------------
        # 2. Invoke LLM
        # ------------------------------------------------------------------
        settings = get_settings()
        llm = ChatBedrockConverse(
            model=settings.execution_model,
            region_name=settings.aws_region,
            temperature=0.3,
            max_tokens=8192,
        )

        messages = [
            SystemMessage(content=EXECUTION_SYSTEM_PROMPT),
            HumanMessage(content=execution_prompt),
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
        # 3. Parse and normalise test results
        # ------------------------------------------------------------------
        parsed = json.loads(raw)

        test_results: list[TestResult] = []
        for item in parsed:
            result: TestResult = {
                "test_id": item.get("test_id", ""),
                "test_name": item.get("test_name", ""),
                "status": item.get("status", "ERROR"),
                "execution_time_seconds": float(item.get("execution_time_seconds", 1.0)),
                "actual_result": item.get("actual_result", ""),
                "error_message": item.get("error_message"),
            }
            test_results.append(result)

        # ------------------------------------------------------------------
        # 4. Compute outcome flags
        # ------------------------------------------------------------------
        pass_count = sum(1 for r in test_results if r["status"] == "PASS")
        fail_count = sum(1 for r in test_results if r["status"] == "FAIL")
        skip_count = sum(1 for r in test_results if r["status"] == "SKIP")
        error_count = sum(1 for r in test_results if r["status"] == "ERROR")
        total = len(test_results)
        pass_rate = round((pass_count / total) * 100, 1) if total > 0 else 0.0

        has_failures = fail_count > 0
        # Assume code refactor needed if there are failures (failure analysis will refine this)
        needs_code_refactor = has_failures

        total_exec_time = round(sum(r["execution_time_seconds"] for r in test_results), 2)

        execution_summary = (
            f"Executed {total} test cases on {platform_name}. "
            f"Results: {pass_count} PASS, {fail_count} FAIL"
            f"{f', {skip_count} SKIP' if skip_count else ''}"
            f"{f', {error_count} ERROR' if error_count else ''}. "
            f"Pass rate: {pass_rate}%. "
            f"Total simulated execution time: {total_exec_time}s."
        )

        # ------------------------------------------------------------------
        # 5. Build visualization config (pass/fail pie chart)
        # ------------------------------------------------------------------
        viz_series = []
        if pass_count > 0:
            viz_series.append({"x": "PASS", "y": pass_count})
        if fail_count > 0:
            viz_series.append({"x": "FAIL", "y": fail_count})
        if skip_count > 0:
            viz_series.append({"x": "SKIP", "y": skip_count})
        if error_count > 0:
            viz_series.append({"x": "ERROR", "y": error_count})

        visualization_config = {
            "chartType": "pie",
            "title": f"Test Execution Results - {platform_name}",
            "xLabel": "Status",
            "yLabel": "Count",
            "series": [
                {
                    "name": "Test Results",
                    "data": viz_series,
                }
            ],
        }

        duration = round(time.time() - start_time, 2)
        log_entry: AgentLog = {
            "agent_name": "Execution Agent",
            "step_number": 4,
            "input_summary": f"{len(test_cases)} test cases, {len(synthetic_data)} data records",
            "output_summary": (
                f"{total} executed: {pass_count} PASS, {fail_count} FAIL "
                f"({pass_rate}% pass rate)"
            ),
            "reasoning_summary": (
                f"Simulated execution of {total} test cases via LLM evaluation. "
                f"has_failures={has_failures}, needs_code_refactor={needs_code_refactor}."
            ),
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": duration,
            "is_conditional": False,
            "was_executed": True,
        }

        return {
            "test_results": test_results,
            "execution_summary": execution_summary,
            "has_failures": has_failures,
            "needs_code_refactor": needs_code_refactor,
            "visualization_config": visualization_config,
            "agent_logs": [log_entry],
        }

    except Exception as e:
        duration = round(time.time() - start_time, 2)
        log_entry: AgentLog = {
            "agent_name": "Execution Agent",
            "step_number": 4,
            "input_summary": f"{len(test_cases)} test cases",
            "output_summary": f"Error: {str(e)[:200]}",
            "reasoning_summary": "Unhandled exception during test execution simulation.",
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": duration,
            "is_conditional": False,
            "was_executed": True,
        }
        return {
            "test_results": [],
            "execution_summary": f"Test execution failed: {str(e)[:200]}",
            "has_failures": False,
            "needs_code_refactor": False,
            "visualization_config": None,
            "agent_logs": [log_entry],
        }

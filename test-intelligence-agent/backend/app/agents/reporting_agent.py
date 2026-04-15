"""
Reporting Agent (Step 7 - ALWAYS) for the Test Intelligence Agent.
Aggregates all state into a GxP compliance report, final markdown answer,
and manual-vs-agent timing comparison.
Manual equivalent: ~1 day  |  Agent time: ~15 seconds
"""

import json
import time
import uuid
from datetime import datetime

from langchain_aws import ChatBedrockConverse
from langchain_core.messages import SystemMessage, HumanMessage

from app.core.config import get_settings
from app.models.state import (
    TIAState,
    AgentLog,
    ComplianceReport,
    ReportSection,
)

REPORTING_SYSTEM_PROMPT = """You are a GxP Compliance Report Writer for AstraZeneca's Test Intelligence Agent.

You operate in a GxP-regulated pharmaceutical R&D environment. Your job is to produce a
comprehensive compliance report that aggregates test intelligence findings into a format
suitable for regulatory inspection, internal quality assurance review, and integration
into Xray test management and CI/CD pipeline workflows.

Given the full test execution context (requirements, test cases, results, failure analyses,
and code refactor suggestions), generate:

1. **report_sections** - An array of report section objects, each with a "title" and
   "content" (markdown-formatted text). Include these sections IN ORDER:
   - Executive Summary
   - Requirements Coverage
   - Test Execution Results (including metadata-scenario and environment-level checks)
   - Failure Analysis (only if there are failures)
   - Remediation Plan (only if there are code refactor suggestions)
   - Compliance Determination
   - Evidence Artifacts & Integration (include Xray export format, CI/CD pipeline
     attachment points, and ReFrame test suite cross-references where applicable)

2. **compliance_status** - One of: "Compliant", "Non-Compliant", "Partially Compliant"
   Based on: pass rate >= 95% = Compliant, 80-94% = Partially Compliant, <80% = Non-Compliant

3. **final_answer** - A markdown-formatted summary suitable for display in a chat interface.
   This should be a user-friendly narrative (not just raw data). Include:
   - A brief headline result
   - Key metrics (pass rate, total tests, failures)
   - Any critical findings (including metadata-scenario inconsistencies if detected)
   - Compliance determination
   - Next steps / recommendations (mention CI/CD integration and Xray sync where relevant)
   Use markdown headers (##), bold, bullet points, and tables where appropriate.

Output **strictly valid JSON**:

{
    "report_sections": [
        {"title": "Executive Summary", "content": "..."},
        {"title": "Requirements Coverage", "content": "..."}
    ],
    "compliance_status": "Partially Compliant",
    "final_answer": "## Test Intelligence Report\\n\\n..."
}

Return ONLY the JSON object, no surrounding text.
"""


def _build_timing_comparison(agent_logs: list[AgentLog]) -> dict:
    """
    Build a manual-vs-agent timing comparison based on agent execution logs.

    Manual time estimates (in hours) per step:
    - Step 0 (Orchestrator):       2h    (planning, scoping meetings)
    - Step 1 (Requirements):       24h   (3 days requirement analysis)
    - Step 2 (Test Generation):    24h   (3 days test case writing)
    - Step 3 (Synthetic Data):     8h    (1 day data preparation)
    - Step 4 (Execution):          16h   (2 days manual test execution)
    - Step 5 (Failure Analysis):   8h    (1 day defect triage)
    - Step 6 (Code Refactor):      8h    (1 day code review & fix)
    - Step 7 (Reporting):          8h    (1 day report writing)
    """
    manual_hours = {
        "Orchestrator": 2,
        "Requirement Agent": 24,
        "Test Generation Agent": 24,
        "Synthetic Data Agent": 8,
        "Execution Agent": 16,
        "Failure Analysis Agent": 8,
        "Code Refactor Agent": 8,
        "Reporting Agent": 8,
    }

    steps = []
    total_manual_hours = 0
    total_agent_seconds = 0

    for log in agent_logs:
        agent_name = log.get("agent_name", "Unknown")
        duration = log.get("duration_seconds", 0) or 0
        was_executed = log.get("was_executed", True)
        manual_h = manual_hours.get(agent_name, 4)

        if was_executed:
            total_manual_hours += manual_h
            total_agent_seconds += duration

        steps.append({
            "step_name": agent_name,
            "manual_time": f"{manual_h}h" if was_executed else "Skipped",
            "agent_time": f"{duration}s" if was_executed else "Skipped",
            "was_executed": was_executed,
        })

    savings_percent = (
        round((1 - (total_agent_seconds / 3600) / total_manual_hours) * 100, 1)
        if total_manual_hours > 0 else 99.0
    )

    return {
        "manual_total_hours": total_manual_hours,
        "agent_total_seconds": round(total_agent_seconds, 1),
        "savings_percent": savings_percent,
        "steps": steps,
    }


def reporting_agent(state: TIAState) -> dict:
    """
    Reporting Agent (Step 7 - ALWAYS).

    Aggregates all state into a GxP compliance report with sections,
    generates a user-friendly final_answer in markdown, and computes
    manual-vs-agent timing comparison.

    Args:
        state: Full TIA state after all previous agents have run.

    Returns:
        Partial state update with compliance_report, final_answer,
        timing_comparison, and agent_logs.
    """
    start_time = time.time()

    # Collect state
    platform_config = state.get("platform_config") or {}
    platform_name = platform_config.get("name", "Unknown Platform")
    test_scope = state.get("test_scope", "")
    requirements = state.get("requirements") or []
    test_cases = state.get("test_cases") or []
    test_results = state.get("test_results") or []
    failure_analyses = state.get("failure_analyses") or []
    refactor_suggestions = state.get("refactor_suggestions") or []
    existing_logs = state.get("agent_logs") or []

    # Compute metrics
    total_tests = len(test_results)
    passed = sum(1 for r in test_results if r["status"] == "PASS")
    failed = sum(1 for r in test_results if r["status"] == "FAIL")
    pass_rate = round((passed / total_tests) * 100, 1) if total_tests > 0 else 0.0

    try:
        # ------------------------------------------------------------------
        # 1. Build comprehensive context for LLM
        # ------------------------------------------------------------------
        req_summary = f"{len(requirements)} requirements extracted"
        if requirements:
            req_summary += ":\n" + "\n".join(
                f"  - {r['field_id']}: {r['field_name']} (mandatory={r['mandatory']})"
                for r in requirements[:10]
            )

        tc_summary = f"{len(test_cases)} test cases generated"
        if test_cases:
            category_counts = {}
            for tc in test_cases:
                category_counts[tc["category"]] = category_counts.get(tc["category"], 0) + 1
            tc_summary += f" ({', '.join(f'{v} {k}' for k, v in category_counts.items())})"

        results_summary = f"{total_tests} tests executed: {passed} PASS, {failed} FAIL, pass rate {pass_rate}%"
        if test_results:
            results_summary += "\n" + "\n".join(
                f"  - {r['test_id']}: {r['test_name']} = {r['status']}"
                + (f" ({r['error_message'][:80]})" if r.get('error_message') else "")
                for r in test_results
            )

        failure_summary = ""
        if failure_analyses:
            failure_summary = f"\n{len(failure_analyses)} failure analyses:\n" + "\n".join(
                f"  - {fa['test_id']}: {fa['category']} ({fa['severity']}) - {fa['root_cause'][:100]}"
                for fa in failure_analyses
            )

        refactor_summary = ""
        if refactor_suggestions:
            refactor_summary = f"\n{len(refactor_suggestions)} code fix suggestions:\n" + "\n".join(
                f"  - {s['test_id']}: {s['file_path']} (confidence: {s['confidence']})"
                for s in refactor_suggestions
            )

        report_prompt = (
            f"## Platform: {platform_name}\n"
            f"## Test Scope: {test_scope}\n\n"
            f"## Requirements\n{req_summary}\n\n"
            f"## Test Cases\n{tc_summary}\n\n"
            f"## Execution Results\n{results_summary}\n"
            f"{failure_summary}\n"
            f"{refactor_summary}\n\n"
            f"## Pass Rate: {pass_rate}%\n\n"
            "Generate the compliance report sections and final_answer. "
            "Return ONLY a JSON object with report_sections, compliance_status, and final_answer."
        )

        # ------------------------------------------------------------------
        # 2. Invoke LLM
        # ------------------------------------------------------------------
        settings = get_settings()
        llm = ChatBedrockConverse(
            model=settings.reporting_model,
            region_name=settings.aws_region,
            temperature=0.1,
            max_tokens=8192,
        )

        messages = [
            SystemMessage(content=REPORTING_SYSTEM_PROMPT),
            HumanMessage(content=report_prompt),
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
        # 3. Parse LLM response
        # ------------------------------------------------------------------
        parsed = json.loads(raw)

        # Build report sections
        sections: list[ReportSection] = []
        for s in parsed.get("report_sections", []):
            section: ReportSection = {
                "title": s.get("title", "Untitled Section"),
                "content": s.get("content", ""),
            }
            sections.append(section)

        # Determine compliance status
        compliance_status = parsed.get("compliance_status", "Partially Compliant")
        # Validate against allowed values
        if compliance_status not in ("Compliant", "Non-Compliant", "Partially Compliant"):
            if pass_rate >= 95:
                compliance_status = "Compliant"
            elif pass_rate >= 80:
                compliance_status = "Partially Compliant"
            else:
                compliance_status = "Non-Compliant"

        # Build ComplianceReport
        report_id = f"TIA-RPT-{uuid.uuid4().hex[:8].upper()}"
        compliance_report: ComplianceReport = {
            "report_id": report_id,
            "platform": platform_name,
            "generated_at": datetime.now().isoformat(),
            "total_tests": total_tests,
            "passed": passed,
            "failed": failed,
            "pass_rate": pass_rate,
            "compliance_status": compliance_status,
            "sections": sections,
        }

        # Get final_answer from LLM
        final_answer = parsed.get("final_answer", "")
        if not final_answer:
            # Fallback: build a basic final answer
            final_answer = (
                f"## Test Intelligence Report - {platform_name}\n\n"
                f"**Test Scope:** {test_scope}\n\n"
                f"### Results Summary\n"
                f"| Metric | Value |\n|--------|-------|\n"
                f"| Total Tests | {total_tests} |\n"
                f"| Passed | {passed} |\n"
                f"| Failed | {failed} |\n"
                f"| Pass Rate | {pass_rate}% |\n"
                f"| Compliance | **{compliance_status}** |\n\n"
                f"**Report ID:** `{report_id}`\n"
            )

        # ------------------------------------------------------------------
        # 4. Build timing comparison
        # ------------------------------------------------------------------
        # Include the current reporting agent's duration in the timing calc
        reporting_duration = round(time.time() - start_time, 2)

        # Create a temporary log for this agent to include in timing
        current_log: AgentLog = {
            "agent_name": "Reporting Agent",
            "step_number": 7,
            "input_summary": f"Full state aggregation for {platform_name}",
            "output_summary": f"Report {report_id}: {compliance_status}, {pass_rate}% pass rate",
            "reasoning_summary": (
                f"Generated GxP compliance report with {len(sections)} sections. "
                f"Compliance determination: {compliance_status} based on {pass_rate}% pass rate."
            ),
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": reporting_duration,
            "is_conditional": False,
            "was_executed": True,
        }

        all_logs = existing_logs + [current_log]
        timing_comparison = _build_timing_comparison(all_logs)

        return {
            "compliance_report": compliance_report,
            "final_answer": final_answer,
            "timing_comparison": timing_comparison,
            "agent_logs": [current_log],
        }

    except Exception as e:
        duration = round(time.time() - start_time, 2)

        # Fallback: build minimal report without LLM
        if pass_rate >= 95:
            compliance_status = "Compliant"
        elif pass_rate >= 80:
            compliance_status = "Partially Compliant"
        else:
            compliance_status = "Non-Compliant"

        report_id = f"TIA-RPT-{uuid.uuid4().hex[:8].upper()}"

        fallback_sections: list[ReportSection] = [
            {
                "title": "Executive Summary",
                "content": (
                    f"Automated test intelligence run for {platform_name}. "
                    f"Scope: {test_scope}. "
                    f"{total_tests} tests executed with {pass_rate}% pass rate. "
                    f"Compliance status: {compliance_status}."
                ),
            },
            {
                "title": "Test Execution Results",
                "content": (
                    f"- Total tests: {total_tests}\n"
                    f"- Passed: {passed}\n"
                    f"- Failed: {failed}\n"
                    f"- Pass rate: {pass_rate}%"
                ),
            },
        ]

        if failure_analyses:
            fallback_sections.append({
                "title": "Failure Analysis",
                "content": "\n".join(
                    f"- {fa['test_id']}: {fa['category']} ({fa['severity']}) - {fa['root_cause'][:150]}"
                    for fa in failure_analyses
                ),
            })

        if refactor_suggestions:
            fallback_sections.append({
                "title": "Remediation Plan",
                "content": "\n".join(
                    f"- {s['test_id']}: Fix in `{s['file_path']}` (confidence: {s['confidence']})"
                    for s in refactor_suggestions
                ),
            })

        compliance_report: ComplianceReport = {
            "report_id": report_id,
            "platform": platform_name,
            "generated_at": datetime.now().isoformat(),
            "total_tests": total_tests,
            "passed": passed,
            "failed": failed,
            "pass_rate": pass_rate,
            "compliance_status": compliance_status,
            "sections": fallback_sections,
        }

        final_answer = (
            f"## Test Intelligence Report - {platform_name}\n\n"
            f"**Test Scope:** {test_scope}\n\n"
            f"### Results\n"
            f"- **{passed}/{total_tests}** tests passed ({pass_rate}%)\n"
            f"- **{failed}** failures detected\n"
            f"- **Compliance:** {compliance_status}\n\n"
            f"*Report generation encountered an error ({str(e)[:100]}). "
            f"Fallback report generated.*\n\n"
            f"**Report ID:** `{report_id}`"
        )

        current_log: AgentLog = {
            "agent_name": "Reporting Agent",
            "step_number": 7,
            "input_summary": f"Full state aggregation for {platform_name}",
            "output_summary": f"Fallback report {report_id}: {str(e)[:100]}",
            "reasoning_summary": f"LLM-based report generation failed. Fallback report produced. Error: {str(e)[:200]}",
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": duration,
            "is_conditional": False,
            "was_executed": True,
        }

        all_logs = existing_logs + [current_log]
        timing_comparison = _build_timing_comparison(all_logs)

        return {
            "compliance_report": compliance_report,
            "final_answer": final_answer,
            "timing_comparison": timing_comparison,
            "agent_logs": [current_log],
        }

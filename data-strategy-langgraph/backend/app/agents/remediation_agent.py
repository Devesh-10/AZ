"""
Remediation Agent for DSA - Data Quality Lifecycle
Analyzes DQ issues from profiling and rules results, prioritizes them by
severity-weighted violation count, and uses LLM (Claude Opus 4) to generate
specific, actionable remediation recommendations with pharmaceutical context.
"""

from datetime import datetime
from pathlib import Path
from langchain_aws import ChatBedrock
from langchain_core.messages import HumanMessage, SystemMessage

from app.core.config import get_settings
from app.models.state import DSAState, AgentLog

settings = get_settings()

DATA_DIR = Path(__file__).parent.parent.parent / "data"

# Severity weights for prioritisation
SEVERITY_WEIGHTS = {
    "critical": 4,
    "high": 3,
    "medium": 2,
    "low": 1,
}

# DQ dimension severity defaults when issues are found
DIMENSION_SEVERITY = {
    "completeness": "high",
    "accuracy": "critical",
    "uniqueness": "critical",
    "consistency": "high",
    "timeliness": "medium",
}

REMEDIATION_SYSTEM_PROMPT = """You are a Senior Data Quality Remediation Specialist at a pharmaceutical manufacturing company operating under GxP regulations.

Your job is to analyze data quality issues and generate specific, actionable remediation plans.

For each issue, you must provide:
1. **Root Cause Analysis**: Why this issue likely exists (data entry error, system integration gap, ETL failure, missing validation, etc.)
2. **Business Impact**: What business processes or compliance areas are affected
3. **Remediation Action**: A specific, executable fix (not generic advice)
4. **Prevention**: What validation or monitoring should be added to prevent recurrence
5. **Priority**: P1 (immediate, within 24h), P2 (within 1 week), P3 (within 1 month)
6. **Owner**: Suggested owner role (Data Steward, IT/ETL Team, Business SME, QA Team)

## Response Format

### Remediation Plan

#### Issue 1: [Specific issue title]
- **Priority**: P1/P2/P3
- **Dimension**: Completeness/Accuracy/Uniqueness/Consistency/Timeliness
- **Impact**: [Table.column] - X violations out of Y records
- **Root Cause**: Specific root cause analysis
- **Action**: "Fix 234 null batch_ids in mes_pasx_batches by running backfill from MES source system"
- **Prevention**: Add NOT NULL constraint + pre-load validation check
- **Owner**: Data Steward / IT Team / QA

#### Issue 2: ...
(continue for all prioritized issues)

### Implementation Roadmap
| Phase | Actions | Timeline | Owner |
|:------|:--------|:---------|:------|
| Immediate (P1) | ... | 24 hours | ... |
| Short-term (P2) | ... | 1 week | ... |
| Long-term (P3) | ... | 1 month | ... |

### Monitoring Recommendations
- List of DQ rules/alerts to add for ongoing monitoring
- Recommended check frequency
- Escalation thresholds

## Guidelines:
- Be SPECIFIC: "Fix 234 null batch_ids" not "Fix null values"
- Reference exact table names, column names, and violation counts
- Use pharmaceutical context (GxP, ALCOA+, 21 CFR Part 11, batch record integrity)
- Prioritize by: business impact * violation count * severity
- For cross-system inconsistencies, identify the system of record
- For referential integrity issues, specify which master data needs updating
"""


def _collect_issues(profiling_result: dict, rules_result: list) -> list[dict]:
    """Collect and prioritize all DQ issues from profiling and rules results.

    Args:
        profiling_result: Dict of table_name -> dimension scores
        rules_result: List of rule execution results

    Returns:
        Sorted list of issue dicts (highest priority first)
    """
    issues = []

    # Issues from profiling: dimensions with scores below threshold
    if profiling_result:
        for table_name, profile in profiling_result.items():
            if not isinstance(profile, dict) or "dimensions" not in profile:
                continue

            row_count = profile.get("row_count", 0)

            for dim_name, dim_data in profile["dimensions"].items():
                score = dim_data.get("score", 100)
                if score < 95:  # Below target threshold
                    gap = 100 - score
                    estimated_violations = int(row_count * gap / 100)
                    severity = DIMENSION_SEVERITY.get(dim_name, "medium")
                    weight = SEVERITY_WEIGHTS.get(severity, 1)

                    issues.append({
                        "source": "profiling",
                        "table": table_name,
                        "dimension": dim_name,
                        "score": score,
                        "gap": round(gap, 2),
                        "estimated_violations": estimated_violations,
                        "row_count": row_count,
                        "severity": severity,
                        "priority_score": estimated_violations * weight,
                        "description": (
                            f"{dim_name.title()} score of {score}% in {table_name} "
                            f"(~{estimated_violations} affected records out of {row_count})"
                        ),
                    })

    # Issues from rules: failed rules with violations
    if rules_result:
        for rule in rules_result:
            if rule.get("status") == "fail" and rule.get("violations", 0) > 0:
                severity = rule.get("severity", "medium")
                weight = SEVERITY_WEIGHTS.get(severity, 1)
                violations = rule.get("violations", 0)

                issues.append({
                    "source": "rules",
                    "rule_id": rule.get("rule_id", "N/A"),
                    "rule_name": rule.get("name", "Unknown rule"),
                    "table": rule.get("table", "N/A"),
                    "dimension": rule.get("dimension", "unknown"),
                    "violations": violations,
                    "total": rule.get("total", 0),
                    "pass_pct": rule.get("pass_pct", 0),
                    "severity": severity,
                    "priority_score": violations * weight,
                    "examples": rule.get("examples", [])[:5],
                    "description": (
                        f"Rule {rule.get('rule_id', 'N/A')}: {rule.get('name', 'Unknown')} - "
                        f"{violations} violations out of {rule.get('total', 0)} records "
                        f"[{severity}]"
                    ),
                })

    # Sort by priority score (highest first)
    issues.sort(key=lambda i: i.get("priority_score", 0), reverse=True)

    return issues


def _build_issues_context(issues: list[dict]) -> str:
    """Build a formatted text context of all issues for the LLM.

    Args:
        issues: Sorted list of issue dicts

    Returns:
        Formatted string describing all issues
    """
    if not issues:
        return "No data quality issues found. All dimensions meet the 95% target threshold."

    context_parts = [f"Total issues found: {len(issues)}\n"]

    for i, issue in enumerate(issues, 1):
        context_parts.append(f"--- Issue {i} (Priority Score: {issue['priority_score']}) ---")
        context_parts.append(f"Source: {issue['source']}")
        context_parts.append(f"Table: {issue['table']}")
        context_parts.append(f"Dimension: {issue['dimension']}")
        context_parts.append(f"Severity: {issue['severity']}")
        context_parts.append(f"Description: {issue['description']}")

        if issue["source"] == "profiling":
            context_parts.append(f"Score: {issue['score']}%")
            context_parts.append(f"Gap from 100%: {issue['gap']}%")
            context_parts.append(f"Estimated affected records: {issue['estimated_violations']}")
            context_parts.append(f"Total records: {issue['row_count']}")

        elif issue["source"] == "rules":
            context_parts.append(f"Rule ID: {issue.get('rule_id', 'N/A')}")
            context_parts.append(f"Rule: {issue.get('rule_name', 'N/A')}")
            context_parts.append(f"Violations: {issue.get('violations', 0)}")
            context_parts.append(f"Total checked: {issue.get('total', 0)}")
            context_parts.append(f"Pass rate: {issue.get('pass_pct', 0)}%")
            examples = issue.get("examples", [])
            if examples:
                context_parts.append(f"Sample violations: {examples[:3]}")

        context_parts.append("")

    return "\n".join(context_parts)


def _generate_remediation_plan(issues: list[dict]) -> str:
    """Use LLM to analyze issues and generate a remediation plan.

    Args:
        issues: Sorted list of issue dicts

    Returns:
        Remediation plan markdown string
    """
    llm = ChatBedrock(
        model_id=settings.kpi_model,  # Use Sonnet for speed
        region_name=settings.aws_region,
    )

    # Limit to top 15 issues to keep context manageable
    top_issues = issues[:15]
    issues_context = _build_issues_context(top_issues)

    try:
        messages = [
            SystemMessage(content=REMEDIATION_SYSTEM_PROMPT),
            HumanMessage(content=(
                f"Analyze these data quality issues and generate a prioritized remediation plan.\n\n"
                f"{issues_context}\n\n"
                f"Provide specific, actionable remediation steps for each issue, "
                f"prioritized by business impact. Include an implementation roadmap "
                f"and monitoring recommendations. Be concise."
            )),
        ]
        response = llm.invoke(messages)
        return response.content
    except Exception as e:
        print(f"[Remediation Agent] LLM error: {e}")
        return _fallback_remediation(issues)


def _fallback_remediation(issues: list[dict]) -> str:
    """Generate a basic remediation plan if LLM is unavailable.

    Args:
        issues: Sorted list of issue dicts

    Returns:
        Basic markdown remediation plan
    """
    plan = "## Remediation Plan\n\n"

    if not issues:
        plan += "No data quality issues requiring remediation.\n"
        return plan

    # Group by priority
    p1_issues = [i for i in issues if i.get("severity") in ("critical",)]
    p2_issues = [i for i in issues if i.get("severity") in ("high",)]
    p3_issues = [i for i in issues if i.get("severity") in ("medium", "low")]

    if p1_issues:
        plan += "### P1 - Immediate (within 24 hours)\n\n"
        for issue in p1_issues[:5]:
            if issue["source"] == "rules":
                plan += (
                    f"- **{issue.get('rule_name', 'Unknown')}** in `{issue['table']}`: "
                    f"Fix {issue.get('violations', 0)} violations. "
                    f"Rule: {issue.get('rule_id', 'N/A')}\n"
                )
            else:
                plan += (
                    f"- **{issue['dimension'].title()}** in `{issue['table']}`: "
                    f"Score {issue.get('score', 0)}%, ~{issue.get('estimated_violations', 0)} "
                    f"affected records\n"
                )
        plan += "\n"

    if p2_issues:
        plan += "### P2 - Short-term (within 1 week)\n\n"
        for issue in p2_issues[:5]:
            if issue["source"] == "rules":
                plan += (
                    f"- **{issue.get('rule_name', 'Unknown')}** in `{issue['table']}`: "
                    f"Fix {issue.get('violations', 0)} violations\n"
                )
            else:
                plan += (
                    f"- **{issue['dimension'].title()}** in `{issue['table']}`: "
                    f"Score {issue.get('score', 0)}%\n"
                )
        plan += "\n"

    if p3_issues:
        plan += "### P3 - Long-term (within 1 month)\n\n"
        for issue in p3_issues[:5]:
            plan += f"- **{issue['dimension'].title()}** in `{issue['table']}`: {issue['description']}\n"
        plan += "\n"

    plan += "### Monitoring Recommendations\n\n"
    plan += "- Run DQ profiling weekly to track dimension score trends\n"
    plan += "- Execute rule validation daily on transactional tables\n"
    plan += "- Set alerts for any dimension dropping below 90%\n"
    plan += "- Review remediation progress in weekly data governance meeting\n"

    return plan


def remediation_agent(state: DSAState) -> dict:
    """Remediation Agent - analyzes DQ issues and generates actionable fix recommendations.

    Takes profiling_result and rules_result from state, collects and prioritizes
    all issues by severity-weighted violation count, then uses Claude Opus 4
    to generate specific remediation actions with pharmaceutical/GxP context.
    Appends the remediation section to final_answer.

    Args:
        state: Current DSA workflow state with profiling_result and rules_result

    Returns:
        Dict with remediation_result, final_answer (appended), and agent_logs
    """
    start_time = datetime.now()

    profiling_result = state.get("profiling_result")
    rules_result = state.get("rules_result")

    if not profiling_result and not rules_result:
        log_entry = AgentLog(
            agent_name="Remediation",
            input_summary="No profiling_result or rules_result in state",
            output_summary="Skipped - no issues to remediate",
            reasoning_summary=None,
            status="error",
            timestamp=datetime.now().isoformat(),
        )
        return {
            "remediation_result": None,
            "agent_logs": [log_entry],
        }

    # Step 1: Collect and prioritize issues
    issues = _collect_issues(profiling_result or {}, rules_result or [])
    print(f"[Remediation Agent] Collected {len(issues)} issues")

    if not issues:
        elapsed = (datetime.now() - start_time).total_seconds()
        no_issues_msg = (
            "\n\n---\n\n## Remediation\n\n"
            "No data quality issues requiring remediation. "
            "All dimension scores meet the 95% target threshold and all rules passed."
        )
        existing_answer = state.get("final_answer") or ""
        log_entry = AgentLog(
            agent_name="Remediation",
            input_summary=(
                f"Profiling: {len(profiling_result or {})} tables, "
                f"Rules: {len(rules_result or [])} rules"
            ),
            output_summary="No issues found - all dimensions above 95% and all rules passed",
            reasoning_summary=f"Analyzed profiling and rule results. No violations detected. Elapsed: {elapsed:.2f}s.",
            status="success",
            timestamp=datetime.now().isoformat(),
        )
        return {
            "remediation_result": {
                "issues_count": 0,
                "issues": [],
                "plan": "No remediation needed",
                "elapsed_sec": round(elapsed, 2),
            },
            "final_answer": existing_answer + no_issues_msg,
            "agent_logs": [log_entry],
        }

    # Step 2: Generate remediation plan via LLM
    remediation_plan = _generate_remediation_plan(issues)
    print(f"[Remediation Agent] Remediation plan generated ({len(remediation_plan)} chars)")

    elapsed = (datetime.now() - start_time).total_seconds()

    # Build issue summary for logging
    critical_count = sum(1 for i in issues if i.get("severity") == "critical")
    high_count = sum(1 for i in issues if i.get("severity") == "high")
    total_violations = sum(
        i.get("violations", i.get("estimated_violations", 0)) for i in issues
    )
    top_issue = issues[0] if issues else None

    remediation_result = {
        "issues_count": len(issues),
        "issues": issues,
        "plan": remediation_plan,
        "summary": {
            "critical": critical_count,
            "high": high_count,
            "total_violations": total_violations,
            "top_issue": top_issue["description"] if top_issue else "N/A",
        },
        "elapsed_sec": round(elapsed, 2),
    }

    # Append remediation to existing final_answer
    existing_answer = state.get("final_answer") or ""
    remediation_section = f"\n\n---\n\n{remediation_plan}"
    updated_answer = existing_answer + remediation_section

    log_entry = AgentLog(
        agent_name="Remediation",
        input_summary=(
            f"Issues: {len(issues)} (critical={critical_count}, high={high_count}), "
            f"Total violations: {total_violations}"
        ),
        output_summary=(
            f"Generated remediation plan for {len(issues)} issues. "
            f"Top issue: {top_issue['description'][:80] if top_issue else 'N/A'}. "
            f"Elapsed: {elapsed:.2f}s."
        ),
        reasoning_summary=(
            f"Collected issues from profiling ({len(profiling_result or {})} tables) "
            f"and rules ({len(rules_result or [])} rules). Prioritized by "
            f"severity_weight * violation_count. Generated remediation plan via "
            f"Claude Sonnet 4 ({settings.kpi_model}). "
            f"Critical: {critical_count}, High: {high_count}, "
            f"Total violations: {total_violations}."
        ),
        status="success",
        timestamp=datetime.now().isoformat(),
    )

    # Build visualization for sidebar — issues by severity
    severity_counts = {}
    for issue in issues:
        sev = issue.get("severity", "medium")
        severity_counts[sev] = severity_counts.get(sev, 0) + 1

    viz_labels = list(severity_counts.keys())
    viz_values = list(severity_counts.values())

    # Also build issues-by-table chart data
    table_issues: dict[str, int] = {}
    for issue in issues:
        tbl = issue.get("table", "Unknown")
        table_issues[tbl] = table_issues.get(tbl, 0) + 1

    visualization_config = {
        "chartType": "bar",
        "title": "Root Cause Analysis — Issues by Severity & Table",
        "charts": [
            {
                "chartType": "bar",
                "title": "Issues by Severity",
                "labels": viz_labels,
                "values": viz_values,
            },
            {
                "chartType": "bar",
                "title": "Issues by Table",
                "labels": list(table_issues.keys())[:10],
                "values": list(table_issues.values())[:10],
            },
        ],
        "labels": viz_labels,
        "values": viz_values,
    }

    return {
        "remediation_result": remediation_result,
        "final_answer": updated_answer,
        "visualization_config": visualization_config,
        "agent_logs": [log_entry],
    }

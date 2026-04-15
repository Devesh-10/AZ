"""
Reporting Agent for DSA - Data Quality Lifecycle
Builds a DQ scorecard from profiling and rules results, generates an executive
summary narrative using LLM (Claude Sonnet 4), and configures visualization
charts for the frontend (dimension bar charts, table heatmaps).
"""

from datetime import datetime
from pathlib import Path
from langchain_aws import ChatBedrock
from langchain_core.messages import HumanMessage, SystemMessage

from app.core.config import get_settings
from app.models.state import DSAState, AgentLog

settings = get_settings()

DATA_DIR = Path(__file__).parent.parent.parent / "data"

# Dimension display names and colors for the frontend
DIMENSION_CONFIG = {
    "completeness": {"label": "Completeness", "color": "#4CAF50"},
    "accuracy": {"label": "Accuracy", "color": "#2196F3"},
    "uniqueness": {"label": "Uniqueness", "color": "#FF9800"},
    "consistency": {"label": "Consistency", "color": "#9C27B0"},
    "timeliness": {"label": "Timeliness", "color": "#F44336"},
}

# Scorecard weight defaults (same as profiling agent)
DIMENSION_WEIGHTS = {
    "completeness": 0.25,
    "accuracy": 0.25,
    "uniqueness": 0.20,
    "consistency": 0.15,
    "timeliness": 0.15,
}

EXECUTIVE_SUMMARY_PROMPT = """You are a Data Quality Executive Reporting Agent for a pharmaceutical manufacturing company.
Your job is to generate a clear, professional executive summary of a data quality assessment.

You will receive:
1. A DQ scorecard with per-table and per-dimension scores
2. Rule validation results with pass/fail counts and violations

Generate a concise executive summary using this exact format:

## Data Quality Assessment - Executive Summary

### Overall Score: {score}% ({rating})

### Dimension Scores
| Dimension | Score | Status |
|:----------|:------|:-------|
| Completeness | XX% | Pass/Warning/Fail |
| Accuracy | XX% | Pass/Warning/Fail |
| Uniqueness | XX% | Pass/Warning/Fail |
| Consistency | XX% | Pass/Warning/Fail |
| Timeliness | XX% | Pass/Warning/Fail |

### Key Findings
- **Finding 1**: Most critical issue with impact statement
- **Finding 2**: Second most important finding
- **Finding 3**: Notable observation

### Rule Validation Summary
- **X of Y rules passed** (Z% pass rate)
- **Critical failures**: List any critical rule failures
- **Top violations**: Describe the highest-priority violations

### Risk Assessment
Provide a 2-3 sentence risk assessment based on the scores and rule results.
Use pharmaceutical/GxP context (batch record integrity, LIMS compliance, etc.).

### Recommendations
1. **Immediate**: Action needed within 24 hours
2. **Short-term**: Action needed within 1 week
3. **Long-term**: Systemic improvement

Guidelines:
- Use **bold** for key numbers and severity levels
- Status thresholds: Pass >= 95%, Warning >= 80%, Fail < 80%
- Overall rating: Excellent >= 95%, Good >= 90%, Acceptable >= 80%, At Risk >= 70%, Critical < 70%
- Be specific about affected tables, columns, and record counts
- Use pharmaceutical terminology (GxP, batch records, OOS, deviations, ALCOA+)
"""


def _build_scorecard(profiling_result: dict, rules_result: list) -> dict:
    """Build a comprehensive DQ scorecard from profiling and rules results.

    Args:
        profiling_result: Dict of table_name -> dimension scores from Profiling Agent
        rules_result: List of rule execution results from Rules Agent

    Returns:
        Scorecard dict with overall, per-table, and per-dimension scores
    """
    scorecard = {
        "overall_score": 0.0,
        "overall_rating": "Unknown",
        "per_table": {},
        "per_dimension": {},
        "rules_summary": {},
    }

    if not profiling_result:
        return scorecard

    # Per-table scores (from profiling)
    table_scores = []
    for table_name, profile in profiling_result.items():
        if isinstance(profile, dict) and "dimensions" in profile:
            table_entry = {
                "table_name": table_name,
                "row_count": profile.get("row_count", 0),
                "overall_score": profile.get("overall_score", 0),
                "dimensions": {},
            }
            for dim_name, dim_data in profile["dimensions"].items():
                table_entry["dimensions"][dim_name] = dim_data.get("score", 0)
            scorecard["per_table"][table_name] = table_entry
            table_scores.append(profile.get("overall_score", 0))

    # Overall score (weighted average across tables, weighted by row count)
    if table_scores:
        total_rows = sum(
            p.get("row_count", 1)
            for p in profiling_result.values()
            if isinstance(p, dict) and "dimensions" in p
        )
        if total_rows > 0:
            weighted_sum = sum(
                p.get("overall_score", 0) * p.get("row_count", 1)
                for p in profiling_result.values()
                if isinstance(p, dict) and "dimensions" in p
            )
            scorecard["overall_score"] = round(weighted_sum / total_rows, 2)
        else:
            scorecard["overall_score"] = round(sum(table_scores) / len(table_scores), 2)

    # Per-dimension scores (average across all tables)
    dimension_totals = {}
    dimension_counts = {}
    for table_name, profile in profiling_result.items():
        if not isinstance(profile, dict) or "dimensions" not in profile:
            continue
        for dim_name, dim_data in profile["dimensions"].items():
            score = dim_data.get("score", 0)
            dimension_totals[dim_name] = dimension_totals.get(dim_name, 0) + score
            dimension_counts[dim_name] = dimension_counts.get(dim_name, 0) + 1

    for dim_name in dimension_totals:
        count = dimension_counts.get(dim_name, 1)
        avg_score = round(dimension_totals[dim_name] / count, 2)
        status = "Pass" if avg_score >= 95 else ("Warning" if avg_score >= 80 else "Fail")
        scorecard["per_dimension"][dim_name] = {
            "score": avg_score,
            "status": status,
            "label": DIMENSION_CONFIG.get(dim_name, {}).get("label", dim_name.title()),
        }

    # Overall rating
    overall = scorecard["overall_score"]
    if overall >= 95:
        scorecard["overall_rating"] = "Excellent"
    elif overall >= 90:
        scorecard["overall_rating"] = "Good"
    elif overall >= 80:
        scorecard["overall_rating"] = "Acceptable"
    elif overall >= 70:
        scorecard["overall_rating"] = "At Risk"
    else:
        scorecard["overall_rating"] = "Critical"

    # Rules summary
    if rules_result:
        total_rules = len(rules_result)
        passed = sum(1 for r in rules_result if r.get("status") == "pass")
        failed = sum(1 for r in rules_result if r.get("status") == "fail")
        errored = sum(1 for r in rules_result if r.get("status") == "error")
        total_violations = sum(r.get("violations", 0) for r in rules_result)
        critical_failures = [
            r for r in rules_result
            if r.get("status") == "fail" and r.get("severity") == "critical"
        ]
        top_violations = sorted(
            [r for r in rules_result if r.get("violations", 0) > 0],
            key=lambda r: r.get("priority_score", r.get("violations", 0)),
            reverse=True,
        )[:5]

        scorecard["rules_summary"] = {
            "total_rules": total_rules,
            "passed": passed,
            "failed": failed,
            "errored": errored,
            "pass_rate": round(passed * 100.0 / total_rules, 2) if total_rules > 0 else 0,
            "total_violations": total_violations,
            "critical_failures": [
                {"rule_id": r["rule_id"], "name": r["name"], "violations": r["violations"]}
                for r in critical_failures
            ],
            "top_violations": [
                {
                    "rule_id": r["rule_id"],
                    "name": r["name"],
                    "severity": r["severity"],
                    "violations": r["violations"],
                    "table": r.get("table", "N/A"),
                }
                for r in top_violations
            ],
        }

    return scorecard


def _build_visualization_config(scorecard: dict) -> dict:
    """Build visualization config for the frontend chart components.

    Generates:
    1. Bar chart of dimension scores
    2. Table heatmap of per-table x per-dimension scores

    Args:
        scorecard: The DQ scorecard dict

    Returns:
        Visualization config dict for the frontend
    """
    viz_config = {"charts": []}

    # Chart 1: Dimension scores bar chart
    dimension_data = []
    for dim_name, dim_info in scorecard.get("per_dimension", {}).items():
        config = DIMENSION_CONFIG.get(dim_name, {})
        dimension_data.append({
            "x": config.get("label", dim_name.title()),
            "y": dim_info["score"],
            "color": config.get("color", "#666"),
        })

    if dimension_data:
        viz_config["charts"].append({
            "chartType": "bar",
            "title": f"DQ Dimension Scores (Overall: {scorecard['overall_score']}%)",
            "xLabel": "Dimension",
            "yLabel": "Score (%)",
            "series": [
                {
                    "name": "DQ Score",
                    "data": dimension_data,
                }
            ],
            "referenceLine": {
                "y": 95,
                "label": "Target: 95%",
            },
        })

    # Chart 2: Per-table overall scores bar chart
    table_data = []
    for table_name, table_info in scorecard.get("per_table", {}).items():
        # Shorten table name for display
        display_name = table_name.replace("_", " ").title()
        if len(display_name) > 25:
            display_name = display_name[:22] + "..."
        table_data.append({
            "x": display_name,
            "y": table_info["overall_score"],
        })

    if table_data:
        # Sort by score ascending so worst tables are visible first
        table_data.sort(key=lambda d: d["y"])
        viz_config["charts"].append({
            "chartType": "bar",
            "title": "DQ Scores by Table",
            "xLabel": "Table",
            "yLabel": "Overall DQ Score (%)",
            "series": [
                {
                    "name": "Table DQ Score",
                    "data": table_data,
                }
            ],
            "referenceLine": {
                "y": 80,
                "label": "Minimum: 80%",
            },
        })

    # Chart 3: Table x Dimension heatmap data
    heatmap_rows = []
    for table_name, table_info in scorecard.get("per_table", {}).items():
        row = {"table": table_name}
        for dim_name, score in table_info.get("dimensions", {}).items():
            row[dim_name] = score
        row["overall"] = table_info.get("overall_score", 0)
        heatmap_rows.append(row)

    if heatmap_rows:
        viz_config["heatmap"] = {
            "title": "DQ Heatmap: Tables x Dimensions",
            "rows": heatmap_rows,
            "dimensions": list(DIMENSION_CONFIG.keys()),
            "thresholds": {"pass": 95, "warning": 80, "fail": 0},
        }

    # Chart 4: Rules pass/fail pie data
    rules_summary = scorecard.get("rules_summary", {})
    if rules_summary:
        viz_config["charts"].append({
            "chartType": "bar",
            "title": "DQ Rule Validation Results",
            "xLabel": "Status",
            "yLabel": "Count",
            "series": [
                {
                    "name": "Rules",
                    "data": [
                        {"x": "Passed", "y": rules_summary.get("passed", 0), "color": "#4CAF50"},
                        {"x": "Failed", "y": rules_summary.get("failed", 0), "color": "#F44336"},
                        {"x": "Errors", "y": rules_summary.get("errored", 0), "color": "#FF9800"},
                    ],
                }
            ],
        })

    # Use the first chart as the primary visualization_config for compatibility
    if viz_config["charts"]:
        primary_chart = viz_config["charts"][0]
        viz_config.update(primary_chart)

    return viz_config


def _generate_executive_summary(scorecard: dict) -> str:
    """Use LLM to generate an executive summary narrative.

    Args:
        scorecard: The DQ scorecard dict

    Returns:
        Executive summary markdown string
    """
    llm = ChatBedrock(
        model_id=settings.kpi_model,
        region_name=settings.aws_region,
    )

    # Build scorecard text for the LLM
    scorecard_text = f"Overall DQ Score: {scorecard['overall_score']}% ({scorecard['overall_rating']})\n\n"

    scorecard_text += "Per-Dimension Scores:\n"
    for dim_name, dim_info in scorecard.get("per_dimension", {}).items():
        scorecard_text += f"  - {dim_info['label']}: {dim_info['score']}% [{dim_info['status']}]\n"

    scorecard_text += "\nPer-Table Scores:\n"
    for table_name, table_info in scorecard.get("per_table", {}).items():
        scorecard_text += f"  - {table_name}: {table_info['overall_score']}% ({table_info['row_count']} rows)\n"
        for dim_name, score in table_info.get("dimensions", {}).items():
            scorecard_text += f"      {dim_name}: {score}%\n"

    rules_summary = scorecard.get("rules_summary", {})
    if rules_summary:
        scorecard_text += f"\nRule Validation:\n"
        scorecard_text += f"  - Total rules: {rules_summary.get('total_rules', 0)}\n"
        scorecard_text += f"  - Passed: {rules_summary.get('passed', 0)}\n"
        scorecard_text += f"  - Failed: {rules_summary.get('failed', 0)}\n"
        scorecard_text += f"  - Pass rate: {rules_summary.get('pass_rate', 0)}%\n"
        scorecard_text += f"  - Total violations: {rules_summary.get('total_violations', 0)}\n"

        critical = rules_summary.get("critical_failures", [])
        if critical:
            scorecard_text += "  - Critical failures:\n"
            for cf in critical:
                scorecard_text += f"      {cf['rule_id']}: {cf['name']} ({cf['violations']} violations)\n"

        top_v = rules_summary.get("top_violations", [])
        if top_v:
            scorecard_text += "  - Top violations:\n"
            for tv in top_v:
                scorecard_text += (
                    f"      {tv['rule_id']}: {tv['name']} "
                    f"[{tv['severity']}] - {tv['violations']} violations in {tv['table']}\n"
                )

    try:
        messages = [
            SystemMessage(content=EXECUTIVE_SUMMARY_PROMPT),
            HumanMessage(content=f"Generate an executive summary for this DQ assessment:\n\n{scorecard_text}"),
        ]
        response = llm.invoke(messages)
        return response.content
    except Exception as e:
        print(f"[Reporting Agent] LLM error: {e}")
        # Fallback: generate a basic summary without LLM
        return _fallback_summary(scorecard)


def _fallback_summary(scorecard: dict) -> str:
    """Generate a basic summary if LLM is unavailable.

    Args:
        scorecard: The DQ scorecard dict

    Returns:
        Basic markdown summary string
    """
    overall = scorecard["overall_score"]
    rating = scorecard["overall_rating"]

    summary = f"## Data Quality Assessment - Executive Summary\n\n"
    summary += f"### Overall Score: {overall}% ({rating})\n\n"

    summary += "### Dimension Scores\n"
    summary += "| Dimension | Score | Status |\n"
    summary += "|:----------|:------|:-------|\n"
    for dim_name, dim_info in scorecard.get("per_dimension", {}).items():
        summary += f"| {dim_info['label']} | {dim_info['score']}% | {dim_info['status']} |\n"

    summary += "\n### Per-Table Scores\n"
    summary += "| Table | Score | Rows |\n"
    summary += "|:------|:------|:-----|\n"
    for table_name, table_info in scorecard.get("per_table", {}).items():
        summary += f"| {table_name} | {table_info['overall_score']}% | {table_info['row_count']} |\n"

    rules_summary = scorecard.get("rules_summary", {})
    if rules_summary:
        summary += f"\n### Rule Validation\n"
        summary += (
            f"- **{rules_summary.get('passed', 0)} of {rules_summary.get('total_rules', 0)} "
            f"rules passed** ({rules_summary.get('pass_rate', 0)}%)\n"
        )
        summary += f"- Total violations: **{rules_summary.get('total_violations', 0)}**\n"

        critical = rules_summary.get("critical_failures", [])
        if critical:
            summary += f"- **Critical failures ({len(critical)}):**\n"
            for cf in critical:
                summary += f"  - {cf['rule_id']}: {cf['name']} ({cf['violations']} violations)\n"

    return summary


def reporting_agent(state: DSAState) -> dict:
    """Reporting Agent - builds DQ scorecard, generates executive summary, configures charts.

    Takes profiling_result and rules_result from state, builds a weighted
    scorecard, uses LLM to generate an executive summary narrative, and
    configures visualization charts for the frontend.

    Args:
        state: Current DSA workflow state with profiling_result and rules_result

    Returns:
        Dict with reporting_result, final_answer, visualization_config, and agent_logs
    """
    start_time = datetime.now()

    profiling_result = state.get("profiling_result")
    rules_result = state.get("rules_result")

    if not profiling_result and not rules_result:
        log_entry = AgentLog(
            agent_name="Reporting",
            input_summary="No profiling_result or rules_result in state",
            output_summary="Skipped - no data to report on",
            reasoning_summary=None,
            status="error",
            timestamp=datetime.now().isoformat(),
        )
        return {
            "reporting_result": None,
            "final_answer": "No data quality profiling or rule results available to generate a report.",
            "agent_logs": [log_entry],
        }

    # Handle rules-only reports (no profiling data)
    if not profiling_result and rules_result:
        print(f"[Reporting Agent] Rules-only report ({len(rules_result)} rules, no profiling data)")

    # Step 1: Build the DQ scorecard
    scorecard = _build_scorecard(profiling_result or {}, rules_result or [])
    print(
        f"[Reporting Agent] Scorecard built: "
        f"Overall={scorecard['overall_score']}% ({scorecard['overall_rating']})"
    )

    # Step 2: Generate executive summary narrative via LLM
    executive_summary = _generate_executive_summary(scorecard)
    print(f"[Reporting Agent] Executive summary generated ({len(executive_summary)} chars)")

    # Step 3: Build visualization config
    viz_config = _build_visualization_config(scorecard)
    print(f"[Reporting Agent] Visualization config built ({len(viz_config.get('charts', []))} charts)")

    elapsed = (datetime.now() - start_time).total_seconds()

    reporting_result = {
        "scorecard": scorecard,
        "executive_summary": executive_summary,
        "generated_at": datetime.now().isoformat(),
        "elapsed_sec": round(elapsed, 2),
    }

    log_entry = AgentLog(
        agent_name="Reporting",
        input_summary=(
            f"Profiling: {len(profiling_result or {})} tables, "
            f"Rules: {len(rules_result or [])} rules"
        ),
        output_summary=(
            f"Overall DQ: {scorecard['overall_score']}% ({scorecard['overall_rating']}). "
            "Dimensions: "
            + ", ".join(
                f"{d}={i['score']}%"
                for d, i in scorecard.get("per_dimension", {}).items()
            )
            + ". "
            + f"Rules: {scorecard.get('rules_summary', {}).get('passed', 0)}/{scorecard.get('rules_summary', {}).get('total_rules', 0)} passed."
        ),
        reasoning_summary=(
            f"Built weighted scorecard (C=25%, A=25%, U=20%, Co=15%, T=15%), "
            f"row-count-weighted across tables. Generated executive summary via "
            f"Claude Sonnet 4 ({settings.kpi_model}). Built {len(viz_config.get('charts', []))} "
            f"chart configs and heatmap for frontend. Elapsed: {elapsed:.2f}s."
        ),
        status="success",
        timestamp=datetime.now().isoformat(),
    )

    return {
        "reporting_result": reporting_result,
        "final_answer": executive_summary,
        "visualization_config": viz_config,
        "agent_logs": [log_entry],
    }

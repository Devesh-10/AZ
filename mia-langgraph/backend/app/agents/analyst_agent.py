"""
Analyst Agent for MIA
Handles complex queries requiring deep analysis, chain-of-thought reasoning,
and potentially querying multiple data sources.
Uses Claude Opus 4.6 for advanced reasoning capabilities.
"""

from datetime import datetime
from pathlib import Path
import pandas as pd
from langchain_aws import ChatBedrock
from langchain_core.messages import HumanMessage, SystemMessage

from app.core.config import get_settings
from app.models.state import MIAState, AgentLog, AnalystResult, KPIResult
from app.tools.data_catalogue import KPI_CATALOGUE, FOUNDATION_DATA_PRODUCTS

settings = get_settings()

# Analyst Agent system prompt - clean output format
ANALYST_SYSTEM_PROMPT = """You are an expert Manufacturing Analyst for MIA (Manufacturing Insight Agent).
Your role is to analyze manufacturing data and provide clear, actionable insights.

## Your Capabilities
- Multi-KPI analysis and correlation
- Trend identification and pattern recognition
- Root cause analysis for performance issues
- Data-driven recommendations

## Available KPIs:
{kpi_list}

## Response Guidelines
IMPORTANT: Provide a CLEAN, PROFESSIONAL response directly to the user. Do NOT show your thinking process, planning steps, or internal reasoning.

Structure your response as:

## Summary
[2-3 sentences directly answering the user's question]

## Key Findings
[Bullet points with specific data values and metrics]

## Recommendations
[Actionable next steps based on the analysis]

Keep responses concise and focused. Use specific numbers from the data. Do not include headers like "Understand", "Plan", "Execute", "Analyze", or "Synthesize".
"""


def _load_all_kpi_data() -> dict[str, pd.DataFrame]:
    """Load all KPI data files"""
    data_dir = Path(__file__).parent.parent.parent / "data" / "KPI"
    data = {}

    weekly_path = data_dir / "kpi_store_weekly.csv"
    if weekly_path.exists():
        data["weekly"] = pd.read_csv(weekly_path)

    monthly_path = data_dir / "kpi_store_monthly.csv"
    if monthly_path.exists():
        data["monthly"] = pd.read_csv(monthly_path)

    return data


def _analyze_trend(df: pd.DataFrame, kpi_column: str, date_column: str) -> dict:
    """Analyze trend for a specific KPI"""
    if df.empty or kpi_column not in df.columns:
        return {"trend": "unknown", "change": 0}

    df_sorted = df.sort_values(date_column)
    values = df_sorted[kpi_column].dropna().tolist()

    if len(values) < 2:
        return {"trend": "insufficient_data", "change": 0}

    first_val = values[0]
    last_val = values[-1]

    if first_val == 0:
        change_pct = 0
    else:
        change_pct = ((last_val - first_val) / first_val) * 100

    if change_pct > 5:
        trend = "improving"
    elif change_pct < -5:
        trend = "declining"
    else:
        trend = "stable"

    return {
        "trend": trend,
        "change_pct": round(change_pct, 2),
        "start_value": round(first_val, 2),
        "end_value": round(last_val, 2),
        "data_points": len(values)
    }


def _get_rag_summary(df: pd.DataFrame) -> dict:
    """Summarize RAG status across KPIs"""
    rag_columns = [col for col in df.columns if col.endswith("_RAG")]
    summary = {}

    for col in rag_columns:
        kpi_name = col.replace("_RAG", "")
        counts = df[col].value_counts().to_dict()
        summary[kpi_name] = counts

    return summary


def _build_data_context(data: dict[str, pd.DataFrame], query: str) -> str:
    """Build context string from data for LLM"""
    context_parts = []

    for name, df in data.items():
        if df.empty:
            continue

        context_parts.append(f"\n### {name.upper()} Data Summary:")
        context_parts.append(f"Records: {len(df)}")

        # Add recent data summary
        date_col = "week_end_date" if "week_end_date" in df.columns else "month"
        if date_col in df.columns:
            df_sorted = df.sort_values(date_col, ascending=False)
            latest = df_sorted.head(5)

            context_parts.append(f"\nLatest {len(latest)} records:")
            for _, row in latest.iterrows():
                row_summary = []
                for col in ["SKU", "site_id", date_col, "batch_yield_avg_pct", "rft_pct", "oee_packaging_pct"]:
                    if col in row.index and pd.notna(row[col]):
                        row_summary.append(f"{col}: {row[col]}")
                context_parts.append("  - " + ", ".join(row_summary))

        # Add RAG summary
        rag_summary = _get_rag_summary(df)
        if rag_summary:
            context_parts.append("\nRAG Status Summary:")
            for kpi, counts in rag_summary.items():
                context_parts.append(f"  - {kpi}: {counts}")

        # Add trend for key KPIs
        for kpi_col in ["batch_yield_avg_pct", "rft_pct", "oee_packaging_pct"]:
            if kpi_col in df.columns:
                trend = _analyze_trend(df, kpi_col, date_col)
                context_parts.append(f"\n{kpi_col} Trend: {trend['trend']} ({trend.get('change_pct', 0):+.1f}%)")

    return "\n".join(context_parts)


def analyst_agent(state: MIAState) -> dict:
    """
    Analyst Agent that performs deep analysis on manufacturing data.

    Args:
        state: Current MIA state with user query

    Returns:
        Updated state with analyst results
    """
    user_query = state["user_query"]
    filters = state.get("extracted_filters")

    # Load all available data
    data = _load_all_kpi_data()

    if not any(not df.empty for df in data.values()):
        log_entry = AgentLog(
            agent_name="Analyst Agent",
            input_summary=user_query[:100],
            output_summary="No data available for analysis",
            reasoning_summary=None,
            status="error",
            timestamp=datetime.now().isoformat()
        )
        return {
            "analyst_result": None,
            "final_answer": "I apologize, but I couldn't find any data to analyze. Please check that the data files are properly configured.",
            "agent_logs": [log_entry]
        }

    # Build KPI and FDP lists for prompt
    kpi_list = "\n".join([
        f"- {kpi_id}: {info['name']} - {info['description']}"
        for kpi_id, info in KPI_CATALOGUE.items()
    ])

    fdp_list = "\n".join([
        f"- {fdp_id}: {info['name']} - {info['description']}"
        for fdp_id, info in FOUNDATION_DATA_PRODUCTS.items()
    ])

    # Build data context
    data_context = _build_data_context(data, user_query)

    # Use Opus for deep analysis
    llm = ChatBedrock(
        model_id=settings.analyst_model,
        region_name=settings.aws_region
    )

    system_prompt = ANALYST_SYSTEM_PROMPT.format(
        kpi_list=kpi_list,
        fdp_list=fdp_list
    )

    try:
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"""Question: {user_query}

Data Available:
{data_context}

Provide a clear, professional analysis. Start directly with the Summary section - do NOT include any thinking process or planning steps.""")
        ]

        response = llm.invoke(messages)
        analysis = response.content

        # Extract insights (simple heuristic - in production would use structured output)
        insights = []
        if "insight" in analysis.lower():
            # Try to extract bullet points after "Insights" section
            lines = analysis.split("\n")
            in_insights = False
            for line in lines:
                if "insight" in line.lower() and ":" in line:
                    in_insights = True
                    continue
                if in_insights and line.strip().startswith(("-", "*", "•")):
                    insights.append(line.strip().lstrip("-*• "))
                elif in_insights and line.strip() and not line.strip().startswith(("-", "*", "•")):
                    if line.strip().startswith("#") or line.strip().startswith("**"):
                        in_insights = False

        analyst_result = AnalystResult(
            narrative=analysis,
            supporting_kpi_results=[],  # Would populate from data
            insights=insights[:5]  # Top 5 insights
        )

        log_entry = AgentLog(
            agent_name="Analyst Agent",
            input_summary=user_query[:100],
            output_summary=f"Generated analysis with {len(insights)} insights",
            reasoning_summary="Used chain-of-thought analysis with Opus model",
            status="success",
            timestamp=datetime.now().isoformat()
        )

        return {
            "analyst_result": analyst_result,
            "final_answer": analysis,
            "visualization_config": {
                "type": "analysis_report",
                "has_insights": len(insights) > 0
            },
            "agent_logs": [log_entry]
        }

    except Exception as e:
        # Fallback to simple data summary
        log_entry = AgentLog(
            agent_name="Analyst Agent",
            input_summary=user_query[:100],
            output_summary=f"LLM error: {str(e)}",
            reasoning_summary=None,
            status="error",
            timestamp=datetime.now().isoformat()
        )

        fallback_response = f"""I encountered an issue generating the full analysis, but here's what I found in the data:

{data_context}

Please try rephrasing your question or contact support if the issue persists."""

        return {
            "analyst_result": AnalystResult(
                narrative=fallback_response,
                supporting_kpi_results=[],
                insights=[]
            ),
            "final_answer": fallback_response,
            "agent_logs": [log_entry]
        }

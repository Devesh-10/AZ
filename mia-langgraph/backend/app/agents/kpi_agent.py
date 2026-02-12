"""
KPI Agent for MIA
Handles simple KPI queries using pre-computed data products.
Uses Claude Sonnet 4.5 for SQL generation and DuckDB for execution.
"""

from datetime import datetime
from pathlib import Path
import duckdb
from langchain_aws import ChatBedrock
from langchain_core.messages import HumanMessage, SystemMessage

from app.core.config import get_settings
from app.models.state import MIAState, AgentLog, KPIResult
from app.tools.data_catalogue import KPI_CATALOGUE

settings = get_settings()

# Data directory
DATA_DIR = Path(__file__).parent.parent.parent / "data" / "KPI"

# SQL Generation system prompt
SQL_GENERATION_PROMPT = """You are a SQL expert for a Manufacturing Insight Agent.
Your job is to generate SQL queries to retrieve KPI data from pre-computed data products.

## Available Tables

### KPI_STORE_MONTHLY (use this for most queries)
Columns: SKU, month, site_id, production_volume, batch_count, batch_yield_avg_pct, rft_pct,
schedule_adherence_pct, avg_cycle_time_hr, formulation_lead_time_hr, deviations_per_100_batches,
oee_packaging_pct, OTIF_RAG, RFT_RAG, OEE_RAG

### KPI_STORE_WEEKLY (use only when user asks for weekly data)
Columns: iso_week, site_id, production_volume, batch_count, batch_yield_avg_pct, rft_pct,
schedule_adherence_pct, avg_cycle_time_hr, deviations_per_100_batches, oee_packaging_pct, month
Note: Weekly table does NOT have SKU column

## KPI Column Mapping
{kpi_column_mapping}

## Rules
1. Return ONLY the SQL query, no explanations or markdown
2. Use the exact column names provided above
3. TABLE SELECTION IS CRITICAL:
   - Use KPI_STORE_MONTHLY when user mentions "months", "monthly", or a specific number of months (e.g., "3 months", "last 6 months")
   - Use KPI_STORE_WEEKLY ONLY when user explicitly says "week", "weekly", or "weeks"
   - Default to KPI_STORE_MONTHLY if unclear
4. For monthly data: ORDER BY month DESC
5. For weekly data: ORDER BY iso_week DESC
6. Always include site_id in SELECT
7. For monthly data, include SKU; for weekly data, do NOT include SKU
8. Use standard SQL syntax compatible with DuckDB
9. IMPORTANT: Always add WHERE clause to exclude NULL values for the KPI column (e.g., WHERE kpi_column IS NOT NULL)
10. When user says "last N months", use LIMIT N with KPI_STORE_MONTHLY to get N distinct months

## Examples
- "What is the batch yield?" -> SELECT SKU, site_id, month, batch_yield_avg_pct FROM KPI_STORE_MONTHLY WHERE batch_yield_avg_pct IS NOT NULL ORDER BY month DESC LIMIT 5
- "Show RFT for past 3 months" -> SELECT SKU, site_id, month, rft_pct FROM KPI_STORE_MONTHLY WHERE rft_pct IS NOT NULL ORDER BY month DESC LIMIT 3
- "OEE performance for last 3 months" -> SELECT SKU, site_id, month, oee_packaging_pct FROM KPI_STORE_MONTHLY WHERE oee_packaging_pct IS NOT NULL ORDER BY month DESC LIMIT 3
- "Weekly OEE trend" -> SELECT site_id, iso_week, oee_packaging_pct FROM KPI_STORE_WEEKLY WHERE oee_packaging_pct IS NOT NULL ORDER BY iso_week DESC LIMIT 10
- "Show yield for past 4 weeks" -> SELECT site_id, iso_week, batch_yield_avg_pct FROM KPI_STORE_WEEKLY WHERE batch_yield_avg_pct IS NOT NULL ORDER BY iso_week DESC LIMIT 4
"""

# Response generation prompt
RESPONSE_PROMPT = """You are a KPI Agent for the Manufacturing Insight Agent (MIA).
Generate a clear, professional response explaining the KPI data.

## KPI Details
Name: {kpi_name}
Description: {kpi_description}
Unit: {kpi_unit}
Target: {kpi_target}

## Response Format
1. State the current value(s) clearly
2. Compare to target if applicable
3. Indicate RAG status (Green/Amber/Red) if available
4. Note any trends if multiple data points

Be concise and manufacturing-focused. Use proper units.
"""


def _get_kpi_column_mapping() -> str:
    """Generate KPI to column mapping for SQL prompt"""
    mappings = []
    for kpi_id, info in KPI_CATALOGUE.items():
        mappings.append(f"- {info['name']}: column={kpi_id}, table={info['table']}")
    return "\n".join(mappings)


def _generate_sql(user_query: str, kpi_id: str, kpi_info: dict, filters: dict | None) -> str:
    """Use LLM to generate SQL query"""
    llm = ChatBedrock(
        model_id=settings.kpi_model,
        region_name=settings.aws_region
    )

    prompt = SQL_GENERATION_PROMPT.format(kpi_column_mapping=_get_kpi_column_mapping())

    # Determine table based on time period filter
    table = kpi_info['table']
    if filters:
        time_period = filters.get("time_period", "")
        # Override to MONTHLY if user asks for month-based data or specific SKU (weekly has no SKU)
        if time_period in ["current_month", "last_month"] or filters.get("month") or filters.get("sku"):
            table = "KPI_STORE_MONTHLY"
        elif time_period in ["current_week", "last_week"]:
            table = "KPI_STORE_WEEKLY"

    filter_context = ""
    if filters:
        if filters.get("sku"):
            filter_context += f"\nIMPORTANT: Filter by SKU = '{filters['sku']}' (add WHERE SKU = '{filters['sku']}')"
        if filters.get("site"):
            filter_context += f"\nFilter by site_id = '{filters['site']}'"
        if filters.get("time_period"):
            if filters["time_period"] == "current_month":
                filter_context += "\nTime period: current month only (use WHERE month = (SELECT MAX(month) FROM table))"
            elif filters["time_period"] == "last_month":
                filter_context += "\nTime period: last month"
            elif filters["time_period"] == "current_week":
                filter_context += "\nTime period: current week (use WHERE iso_week = (SELECT MAX(iso_week) FROM table))"
            elif filters["time_period"] == "last_week":
                filter_context += "\nTime period: last week"

    messages = [
        SystemMessage(content=prompt),
        HumanMessage(content=f"""Generate a SQL query for this request:

User question: {user_query}

Target KPI: {kpi_info['name']} (column: {kpi_id})
Table: {table}
{filter_context}

Return ONLY the SQL query.""")
    ]

    response = llm.invoke(messages)
    sql = response.content.strip()

    # Clean up SQL (remove markdown code blocks if present)
    if sql.startswith("```"):
        sql = sql.split("\n", 1)[1] if "\n" in sql else sql[3:]
    if sql.endswith("```"):
        sql = sql.rsplit("```", 1)[0]
    sql = sql.strip()

    return sql


def _execute_sql(sql: str, kpi_info: dict) -> tuple[list[dict], str | None]:
    """Execute SQL using DuckDB and return results"""
    try:
        conn = duckdb.connect(":memory:")

        # Load CSV files as tables
        monthly_path = DATA_DIR / "kpi_store_monthly.csv"
        weekly_path = DATA_DIR / "kpi_store_weekly.csv"

        if monthly_path.exists():
            conn.execute(f"CREATE TABLE KPI_STORE_MONTHLY AS SELECT * FROM read_csv_auto('{monthly_path}')")
        if weekly_path.exists():
            conn.execute(f"CREATE TABLE KPI_STORE_WEEKLY AS SELECT * FROM read_csv_auto('{weekly_path}')")

        # Execute the query
        result = conn.execute(sql).fetchdf()
        conn.close()

        if result.empty:
            return [], None

        # Convert to list of dicts with standardized format
        data_points = []
        for _, row in result.iterrows():
            dp = {
                "sku": str(row.get("SKU", "All SKUs")),
                "site": str(row.get("site_id", "Unknown")),
                "value": None,
                "unit": kpi_info["unit"]
            }

            # Find the period column
            if "month" in row.index:
                dp["period"] = str(row["month"])
            elif "week_end_date" in row.index:
                dp["period"] = str(row["week_end_date"])
            elif "iso_week" in row.index:
                dp["period"] = f"Week {row['iso_week']}"
            else:
                dp["period"] = "N/A"

            # Find the KPI value column (look for columns ending in _pct or _hr)
            for col in result.columns:
                if col.endswith("_pct") or col.endswith("_hr") or col == "deviations_per_100_batches":
                    if col not in ["site_id", "SKU", "month", "week_end_date", "iso_week"]:
                        val = row.get(col)
                        if val is not None and str(val) != "nan":
                            dp["value"] = float(val)
                            break

            # Check for RAG status
            for col in result.columns:
                if "_RAG" in col:
                    rag_val = row.get(col)
                    if rag_val and str(rag_val) != "nan":
                        dp["rag_status"] = str(rag_val)
                        break

            if dp["value"] is not None:
                data_points.append(dp)

        # Sort by period
        data_points.sort(key=lambda x: x["period"])

        return data_points[:20], None

    except Exception as e:
        return [], str(e)


def kpi_agent(state: MIAState) -> dict:
    """
    KPI Agent that generates SQL, executes it, and explains KPI data.

    Args:
        state: Current MIA state with matched KPI

    Returns:
        Updated state with KPI results and generated SQL
    """
    matched_kpi = state.get("matched_kpi")
    filters = state.get("extracted_filters")
    user_query = state["user_query"]

    if not matched_kpi or matched_kpi not in KPI_CATALOGUE:
        log_entry = AgentLog(
            agent_name="KPI Agent",
            input_summary=f"KPI: {matched_kpi}",
            output_summary="KPI not found in catalogue",
            reasoning_summary=None,
            status="error",
            timestamp=datetime.now().isoformat()
        )
        return {
            "kpi_results": None,
            "final_answer": f"I couldn't find information about the requested KPI: {matched_kpi}",
            "agent_logs": [log_entry]
        }

    kpi_info = KPI_CATALOGUE[matched_kpi]

    # Step 1: Generate SQL using LLM
    try:
        generated_sql = _generate_sql(user_query, matched_kpi, kpi_info, filters)
    except Exception as e:
        return {
            "kpi_results": None,
            "final_answer": f"Error generating SQL query: {str(e)}",
            "agent_logs": [AgentLog(
                agent_name="KPI Agent",
                input_summary=f"KPI: {kpi_info['name']}",
                output_summary=f"SQL generation failed: {str(e)}",
                reasoning_summary=None,
                status="error",
                timestamp=datetime.now().isoformat()
            )]
        }

    # Step 2: Execute SQL using DuckDB
    data_points, exec_error = _execute_sql(generated_sql, kpi_info)

    if exec_error:
        error_msg = f"## Query Error\n\n"
        error_msg += f"I encountered an issue while retrieving **{kpi_info['name']}** data.\n\n"
        error_msg += f"**Error:** {exec_error}\n\n"
        error_msg += "Please try rephrasing your question or contact support if the issue persists."

        return {
            "kpi_results": None,
            "generated_sql": generated_sql,
            "final_answer": error_msg,
            "agent_logs": [AgentLog(
                agent_name="KPI Agent",
                input_summary=f"KPI: {kpi_info['name']}",
                output_summary=f"SQL execution failed: {exec_error}",
                reasoning_summary=f"Generated SQL: {generated_sql[:100]}...",
                status="error",
                timestamp=datetime.now().isoformat()
            )]
        }

    if not data_points:
        # Build a helpful no-data message
        no_data_msg = f"## No Data Available\n\n"
        no_data_msg += f"I searched for **{kpi_info['name']}** data but didn't find any matching records.\n\n"

        # Add context about filters
        if filters:
            no_data_msg += "**Applied Filters:**\n"
            if filters.get("sku"):
                no_data_msg += f"- SKU: {filters['sku']}\n"
            if filters.get("site"):
                no_data_msg += f"- Site: {filters['site']}\n"
            if filters.get("time_period"):
                period_map = {
                    "current_month": "Current month",
                    "last_month": "Last month",
                    "current_week": "Current week",
                    "last_week": "Last week"
                }
                no_data_msg += f"- Time Period: {period_map.get(filters['time_period'], filters['time_period'])}\n"
            no_data_msg += "\n"

        no_data_msg += "**Suggestions:**\n"
        no_data_msg += "- Try a different time period (e.g., 'last 3 months' or 'October 2025')\n"
        no_data_msg += "- Check if the SKU exists in the dataset\n"
        no_data_msg += "- Remove filters to see all available data\n"

        return {
            "kpi_results": None,
            "generated_sql": generated_sql,
            "final_answer": no_data_msg,
            "agent_logs": [AgentLog(
                agent_name="KPI Agent",
                input_summary=f"KPI: {kpi_info['name']}",
                output_summary="No data returned from query",
                reasoning_summary=f"SQL: {generated_sql[:100]}...",
                status="error",
                timestamp=datetime.now().isoformat()
            )]
        }

    # Build KPI result
    kpi_result = KPIResult(
        kpi_name=kpi_info["name"],
        breakdown_by="SKU/Site",
        data_points=data_points,
        explanation=None
    )

    # Step 3: Generate explanation using LLM
    llm = ChatBedrock(
        model_id=settings.kpi_model,
        region_name=settings.aws_region
    )

    response_prompt = RESPONSE_PROMPT.format(
        kpi_name=kpi_info["name"],
        kpi_description=kpi_info["description"],
        kpi_unit=kpi_info["unit"],
        kpi_target=kpi_info.get("target", "Not defined")
    )

    data_summary = "\n".join([
        f"- {dp['sku']} at {dp['site']}: {dp['value']}{dp['unit']} ({dp['period']})"
        + (f" - RAG: {dp.get('rag_status', 'N/A')}" if 'rag_status' in dp else "")
        for dp in data_points
    ])

    try:
        messages = [
            SystemMessage(content=response_prompt),
            HumanMessage(content=f"""User asked: {user_query}

SQL Query executed:
```sql
{generated_sql}
```

Results:
{data_summary}

Target: {kpi_info.get('target', 'Not defined')}{kpi_info['unit']}

Provide a clear, concise response to the user's question.""")
        ]

        response = llm.invoke(messages)
        explanation = response.content

        log_entry = AgentLog(
            agent_name="KPI Agent",
            input_summary=f"KPI: {kpi_info['name']}, Filters: {filters}",
            output_summary=f"Retrieved {len(data_points)} data points via SQL",
            reasoning_summary=f"Generated SQL using Claude Sonnet 4.5 → Executed on DuckDB ({kpi_info['table']}). Query: {generated_sql[:100]}...",
            status="success",
            timestamp=datetime.now().isoformat()
        )

        kpi_result["explanation"] = explanation

        return {
            "kpi_results": [kpi_result],
            "generated_sql": generated_sql,
            "final_answer": explanation,
            "visualization_config": {
                "type": "kpi_card",
                "kpi_name": kpi_info["name"],
                "data": data_points,
                "target": kpi_info.get("target")
            },
            "agent_logs": [log_entry]
        }

    except Exception as e:
        # Fallback to simple response without LLM explanation
        simple_response = f"**{kpi_info['name']}**\n\n"
        for dp in data_points:
            simple_response += f"- {dp['sku']} ({dp['site']}): **{dp['value']}{dp['unit']}** ({dp['period']})\n"
        if kpi_info.get("target"):
            simple_response += f"\nTarget: {kpi_info['target']}{kpi_info['unit']}"
        simple_response += f"\n\n**Generated SQL:**\n```sql\n{generated_sql}\n```"

        return {
            "kpi_results": [kpi_result],
            "generated_sql": generated_sql,
            "final_answer": simple_response,
            "agent_logs": [AgentLog(
                agent_name="KPI Agent",
                input_summary=f"KPI: {kpi_info['name']}",
                output_summary=f"LLM error, using fallback: {str(e)}",
                reasoning_summary=f"SQL generated and executed on DuckDB ({kpi_info['table']}). Response generation fallback used. Query: {generated_sql[:100]}...",
                status="success",
                timestamp=datetime.now().isoformat()
            )]
        }

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

IMPORTANT: This table has multiple rows per month (one per site/plant). There are 3 plants:
- FCTN-PLANT-01 (Frederick)
- MCLS-PLANT-02 (Macclesfield)
- SODR-PLANT-03 (Södertälje)

### KPI_STORE_WEEKLY (use only when user asks for weekly data)
Columns: iso_week, site_id, production_volume, batch_count, batch_yield_avg_pct, rft_pct,
schedule_adherence_pct, avg_cycle_time_hr, deviations_per_100_batches, oee_packaging_pct, month
Note: Weekly table does NOT have SKU column

## KPI Column Mapping
{kpi_column_mapping}

## Rules
1. Return ONLY the SQL query, no explanations or markdown
2. Use the exact column names provided above
3. Use standard SQL syntax compatible with DuckDB
4. Always add WHERE clause to exclude NULL values for the KPI column
5. CRITICAL - WHEN TO USE AGGREGATIONS:
   - If user asks for "total", "sum", "overall", "across sites", "by site" -> USE SUM() with GROUP BY
   - If user asks for "average", "mean", "avg" -> USE AVG() with GROUP BY
   - When aggregating, alias result to ORIGINAL column name: SUM(production_volume) as production_volume
6. TABLE SELECTION:
   - Use KPI_STORE_MONTHLY by default
   - Use KPI_STORE_WEEKLY only when user says "week" or "weekly"
7. For "last N months": Use subquery for DISTINCT months, not just LIMIT N

## Examples
- "What is the batch yield?" -> SELECT SKU, site_id, month, batch_yield_avg_pct FROM KPI_STORE_MONTHLY WHERE batch_yield_avg_pct IS NOT NULL ORDER BY month DESC LIMIT 9
- "Show RFT for SKU_123 for past 3 months" -> SELECT SKU, site_id, month, rft_pct FROM KPI_STORE_MONTHLY WHERE SKU = 'SKU_123' AND rft_pct IS NOT NULL AND month IN (SELECT DISTINCT month FROM KPI_STORE_MONTHLY WHERE SKU = 'SKU_123' ORDER BY month DESC LIMIT 3) ORDER BY month DESC, site_id
- "Total production volume by site" -> SELECT site_id, SUM(production_volume) as production_volume FROM KPI_STORE_MONTHLY WHERE production_volume IS NOT NULL GROUP BY site_id ORDER BY site_id
- "Total production across sites" -> SELECT site_id, SUM(production_volume) as production_volume FROM KPI_STORE_MONTHLY WHERE production_volume IS NOT NULL GROUP BY site_id ORDER BY site_id
- "What is total production" -> SELECT site_id, SUM(production_volume) as production_volume FROM KPI_STORE_MONTHLY WHERE production_volume IS NOT NULL GROUP BY site_id ORDER BY site_id
- "Production volume by site" -> SELECT site_id, SUM(production_volume) as production_volume FROM KPI_STORE_MONTHLY WHERE production_volume IS NOT NULL GROUP BY site_id ORDER BY site_id
- "Weekly OEE trend" -> SELECT site_id, iso_week, oee_packaging_pct FROM KPI_STORE_WEEKLY WHERE oee_packaging_pct IS NOT NULL ORDER BY iso_week DESC LIMIT 10
"""

# Response generation prompt - minimal to let Claude be intelligent
RESPONSE_PROMPT = """You are a manufacturing analytics assistant. Answer the user's question based on the provided data.

KPI: {kpi_name} ({kpi_unit})
Target: {kpi_target}
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

    # Let LLM decide table based on user query
    # Only force table selection if user explicitly mentioned time granularity
    query_lower = user_query.lower()
    if "week" in query_lower:
        table = "KPI_STORE_WEEKLY"
    elif "month" in query_lower or (filters and filters.get("sku")):
        # Use monthly for month queries or when SKU is specified (weekly has no SKU)
        table = "KPI_STORE_MONTHLY"
    else:
        # Default to monthly as it has more complete data (all plants, all SKUs)
        table = "KPI_STORE_MONTHLY"

    filter_context = ""
    if filters:
        if filters.get("sku"):
            filter_context += f"\nIMPORTANT: Filter by SKU = '{filters['sku']}' (add WHERE SKU = '{filters['sku']}')"
        if filters.get("site"):
            filter_context += f"\nFilter by site_id = '{filters['site']}'"

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

    print(f"[KPI Agent] Generated SQL: {sql}")
    return sql


def _execute_sql(sql: str, kpi_id: str, kpi_info: dict) -> tuple[list[dict], str | None]:
    """Execute SQL using DuckDB and return results

    Args:
        sql: The SQL query to execute
        kpi_id: The KPI column name from catalogue (e.g., 'production_volume', 'batch_yield_avg_pct')
        kpi_info: The KPI metadata from catalogue
    """
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
            print(f"[KPI Agent] SQL returned empty result")
            return [], None

        print(f"[KPI Agent] SQL result columns: {list(result.columns)}")
        print(f"[KPI Agent] Looking for kpi_id: {kpi_id}")
        print(f"[KPI Agent] Result shape: {result.shape}")

        # Convert to list of dicts with standardized format
        data_points = []
        for _, row in result.iterrows():
            dp = {
                "sku": str(row.get("SKU", "All SKUs")),
                "site": str(row.get("site_id", "Unknown")),
                "value": None,
                "unit": kpi_info["unit"]
            }

            # Find the period column - if no time column, use site_id as x-axis label
            if "month" in row.index:
                dp["period"] = str(row["month"])
            elif "week_end_date" in row.index:
                dp["period"] = str(row["week_end_date"])
            elif "iso_week" in row.index:
                dp["period"] = f"Week {row['iso_week']}"
            else:
                # No time period - this is likely an aggregation by site only
                # Use the site as the period for chart x-axis
                dp["period"] = str(row.get("site_id", "Total"))

            # Get KPI value from the result - let the SQL decide what column to return
            # Find the first numeric column that's not a metadata column (site_id, SKU, month, etc.)
            metadata_cols = {'sku', 'site_id', 'month', 'iso_week', 'week_end_date'}
            val = None
            for col in row.index:
                col_lower = col.lower()
                if col_lower not in metadata_cols and '_rag' not in col_lower:
                    candidate = row.get(col)
                    if candidate is not None and str(candidate) != "nan":
                        try:
                            val = float(candidate)
                            break
                        except (ValueError, TypeError):
                            continue

            if val is not None:
                dp["value"] = val

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
    data_points, exec_error = _execute_sql(generated_sql, matched_kpi, kpi_info)

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

    # Check if filtering by specific SKU
    sku_filter = filters.get("sku") if filters else None

    data_summary = "\n".join([
        f"- SKU: {dp['sku']}, Site: {dp['site']}, Period: {dp['period']}, Value: {dp['value']}{dp['unit']}"
        + (f", RAG Status: {dp.get('rag_status', 'N/A')}" if 'rag_status' in dp else "")
        for dp in data_points
    ])

    try:
        messages = [
            SystemMessage(content=response_prompt),
            HumanMessage(content=f"""User question: {user_query}

Data retrieved:
{data_summary}

Target: {kpi_info.get('target', 'Not defined')}{kpi_info['unit']}

Answer the user's question based on the data above.""")
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

        # Build visualization config in the correct format for frontend
        # Group data by site to create multiple series (one per plant)
        sites = list(set(d["site"] for d in data_points))
        periods = sorted(list(set(d["period"] for d in data_points)))

        if len(sites) > 1:
            # Multiple sites - create one series per site, x-axis is period
            series_list = []
            for site in sorted(sites):
                site_data = [dp for dp in data_points if dp["site"] == site]
                series_list.append({
                    "name": site[:4],  # Short site name (FCTN, MCLS, SODR)
                    "data": [{"x": dp["period"], "y": float(dp["value"])} for dp in sorted(site_data, key=lambda x: x["period"])]
                })

            # Use bar chart for <= 4 periods, line for more
            chart_type = "bar" if len(periods) <= 4 else "line"
        else:
            # Single site - simple series
            series_list = [{
                "name": kpi_info["name"],
                "data": [{"x": dp["period"], "y": float(dp["value"])} for dp in sorted(data_points, key=lambda x: x["period"])]
            }]
            chart_type = "bar" if len(data_points) <= 6 else "line"

        viz_config = {
            "chartType": chart_type,
            "title": kpi_info["name"],
            "xLabel": "Period",
            "yLabel": kpi_info["unit"],
            "series": series_list
        }

        return {
            "kpi_results": [kpi_result],
            "generated_sql": generated_sql,
            "final_answer": explanation,
            "visualization_config": viz_config,
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

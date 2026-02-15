"""
KPI Agent for Sustainability Insight Agent
Handles simple sustainability KPI queries using pre-computed data.
Uses Claude Sonnet for SQL generation and DuckDB for execution.
"""

from datetime import datetime
from pathlib import Path
import duckdb
from langchain_aws import ChatBedrock
from langchain_core.messages import HumanMessage, SystemMessage

from app.core.config import get_settings
from app.models.state import SIAState, AgentLog, KPIResult
from app.tools.data_catalogue import KPI_CATALOGUE

settings = get_settings()

DATA_DIR = Path(__file__).parent.parent.parent / "data" / "KPI"

SQL_GENERATION_PROMPT = """You are a SQL expert for a Sustainability Insight Agent.
Your job is to generate SQL queries to retrieve sustainability KPI data.

## Available Tables

### ENERGY_MONTHLY_SUMMARY
Columns: REPORTING_YEAR_NUMBER, REPORTING_QUARTER_NUMBER, REPORTING_MONTH_NUMBER, SHE_SITE_NAME,
REPORTING_SCOPE_NAME, ENERGY_SITE_MWH_QUANTITY, ENERGY_RENEWABLE_ELECTRICITY_HEAT_MWH_QUANTITY,
ENERGY_RENEWABLE_INDIRECT_MWH_QUANTITY, ENERGY_INDIRECT_MWH_QUANTITY,
ENERGY_ONSITE_GENERATED_RENEWABLE_SOLAR_MWH_QUANTITY, ENERGY_ONSITE_GENERATED_NON_RENEWABLE_MWH_QUANTITY,
ENERGY_IMPORTED_RENEWABLE_MWH_QUANTITY, ENERGY_IMPORTED_MWH_QUANTITY

### GREENHOUSE_GAS_EMISSIONS_MONTHLY_SUMMARY
Columns: REPORTING_YEAR_NUMBER, REPORTING_MONTH_NUMBER, REPORTING_QUARTER_NUMBER, SHE_SITE_NAME,
REPORTING_SCOPE_NAME, SCOPE1_F_GASES_TCO2_QUANTITY, SCOPE1_SOLVENTS_TCO2_QUANTITY,
SCOPE1_SITE_ENERGY_TCO2_QUANTITY, SCOPE1_SITE_NON_ENERGY_TCO2_QUANTITY,
SCOPE2_MARKET_BASED_EV_CHARGING_TCO2_QUANTITY, SCOPE2_TOTAL_MARKET_BASED_TCO2_QUANTITY,
SCOPE1_SCOPE2_TOTAL_SITE_ENERGY_TCO2_QUANTITY, SCOPE1_SCOPE2_TOTAL_SITE_TCO2_QUANTITY,
SCOPE2_TOTAL_LOCATION_BASED_TCO2_QUANTITY

### WATER_MONTHLY_SUMMARY
Columns: REPORTING_YEAR_NUMBER, REPORTING_MONTH_NUMBER, REPORTING_QUARTER_NUMBER, SHE_SITE_NAME,
GROUNDWATER_MILLION_M3_QUANTITY, MUNICIPAL_SUPPLY_MILLION_M3_QUANTITY,
RAINWATER_HARVESTING_MILLION_M3_QUANTITY, TOTAL_WATER_WITHDRAWN_MILLION_M3_QUANTITY,
DIRECT_FROM_FRESH_SURFACE_MILLION_M3_QUANTITY, CHEMICAL_OXYGEN_DEMAND_EFFLUENT_TONNES_QUANTITY

### WASTE_MONTHLY_SUMMARY
Columns: REPORTING_YEAR_NUMBER, REPORTING_MONTH_NUMBER, REPORTING_QUARTER_NUMBER, SHE_SITE_NAME,
WASTE_TOTAL_TONNES_QUANTITY, WASTE_HAZARDOUS_TONNES_QUANTITY, WASTE_NON_HAZARDOUS_TONNES_QUANTITY,
WASTE_RECYCLED_TONNES_QUANTITY, WASTE_LANDFILL_TONNES_QUANTITY, WASTE_INCINERATED_TONNES_QUANTITY

### ELECTRIC_VEHICLE_TRANSITION_QUARTERLY_SUMMARY
Columns: REPORTING_YEAR_NUMBER, REPORTING_QUARTER_NUMBER, SHE_MARKET_NAME, SHE_GEOGRAPHY_NAME,
TOTAL_BEV_COUNT, TOTAL_FLEET_ASSET_COUNT

## KPI Column Mapping
{kpi_column_mapping}

## Rules
1. Return ONLY the SQL query, no explanations
2. Use exact column names from above
3. Always include site/market name and period in SELECT
4. ORDER BY year DESC, month/quarter DESC for recent data
5. Use WHERE clause to exclude NULL values for the KPI column
6. For "last N months", ORDER BY year DESC, month DESC and LIMIT N
7. For quarterly data (EV), use ORDER BY year DESC, quarter DESC

## Examples
- "Total energy consumption" -> SELECT SHE_SITE_NAME, REPORTING_YEAR_NUMBER, REPORTING_MONTH_NUMBER, ENERGY_SITE_MWH_QUANTITY FROM ENERGY_MONTHLY_SUMMARY WHERE ENERGY_SITE_MWH_QUANTITY IS NOT NULL ORDER BY REPORTING_YEAR_NUMBER DESC, REPORTING_MONTH_NUMBER DESC LIMIT 10
- "GHG emissions" -> SELECT SHE_SITE_NAME, REPORTING_YEAR_NUMBER, REPORTING_MONTH_NUMBER, SCOPE1_SCOPE2_TOTAL_SITE_TCO2_QUANTITY FROM GREENHOUSE_GAS_EMISSIONS_MONTHLY_SUMMARY WHERE SCOPE1_SCOPE2_TOTAL_SITE_TCO2_QUANTITY IS NOT NULL ORDER BY REPORTING_YEAR_NUMBER DESC, REPORTING_MONTH_NUMBER DESC LIMIT 10
- "EV count by region" -> SELECT SHE_MARKET_NAME, SHE_GEOGRAPHY_NAME, REPORTING_YEAR_NUMBER, REPORTING_QUARTER_NUMBER, TOTAL_BEV_COUNT, TOTAL_FLEET_ASSET_COUNT FROM ELECTRIC_VEHICLE_TRANSITION_QUARTERLY_SUMMARY ORDER BY REPORTING_YEAR_NUMBER DESC, REPORTING_QUARTER_NUMBER DESC LIMIT 10
"""

RESPONSE_PROMPT = """You are a KPI Agent for the Sustainability Insight Agent (SIA).
Generate a clear, professionally formatted response with excellent structure.

## KPI Details
Name: {kpi_name}
Description: {kpi_description}
Unit: {kpi_unit}
Target: {kpi_target}

## REQUIRED RESPONSE FORMAT (follow EXACTLY):

**{kpi_name}** is **[current value with unit]** for [context/period] at [location].

**Status:** [observation about the value]

### Recent Data
| Period | Site/Region | Value |
|:-------|:------------|------:|
| [Period] | [Site] | XX.X |
| [Period] | [Site] | XX.X |

### Key Observations
- **[Observation 1]**: Brief insight with specific numbers
- **[Observation 2]**: Trend direction or notable pattern
- **[Observation 3]**: Recommendation if applicable

## FORMATTING RULES:
1. First line MUST be a clear statement with the current value in **bold**
2. Tables MUST have proper markdown with right-aligned numbers
3. Include 3-5 data points in the table
4. Key Observations should provide actionable insights
5. Be concise - sustainability professionals need quick insights
"""


def _get_kpi_column_mapping() -> str:
    """Generate KPI to column mapping for SQL prompt"""
    mappings = []
    for kpi_id, info in KPI_CATALOGUE.items():
        mappings.append(f"- {info['name']}: column={info.get('column', kpi_id)}, table={info['table']}")
    return "\n".join(mappings)


def _generate_sql(user_query: str, kpi_id: str, kpi_info: dict, filters: dict | None) -> str:
    """Use LLM to generate SQL query"""
    llm = ChatBedrock(
        model_id=settings.kpi_model,
        region_name=settings.aws_region
    )

    prompt = SQL_GENERATION_PROMPT.format(kpi_column_mapping=_get_kpi_column_mapping())

    filter_context = ""
    if filters:
        if filters.get("year"):
            filter_context += f"\nFilter by REPORTING_YEAR_NUMBER = {filters['year']}"
        if filters.get("quarter"):
            filter_context += f"\nFilter by REPORTING_QUARTER_NUMBER = {filters['quarter']}"
        if filters.get("site"):
            # For EV data, use SHE_GEOGRAPHY_NAME; for other data use SHE_SITE_NAME
            if "ELECTRIC_VEHICLE" in kpi_info['table']:
                filter_context += f"\nFilter by SHE_GEOGRAPHY_NAME LIKE '%{filters['site']}%'"
            else:
                filter_context += f"\nFilter by SHE_SITE_NAME LIKE '%{filters['site']}%'"
        if filters.get("market"):
            filter_context += f"\nFilter by SHE_MARKET_NAME = '{filters['market']}'"

    messages = [
        SystemMessage(content=prompt),
        HumanMessage(content=f"""Generate a SQL query for this request:

User question: {user_query}

Target KPI: {kpi_info['name']} (column: {kpi_info.get('column', kpi_id)})
Table: {kpi_info['table']}
{filter_context}

Return ONLY the SQL query.""")
    ]

    response = llm.invoke(messages)
    sql = response.content.strip()

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

        # Load CSV files
        table_files = {
            "ENERGY_MONTHLY_SUMMARY": "energy_monthly_summary.csv",
            "ENERGY_QUARTERLY_SUMMARY": "energy_quarterly_summary.csv",
            "GREENHOUSE_GAS_EMISSIONS_MONTHLY_SUMMARY": "greenhouse_gas_emissions_monthly_summary.csv",
            "GREENHOUSE_GAS_EMISSIONS_QUARTERLY_SUMMARY": "greenhouse_gas_emissions_quarterly_summary.csv",
            "WATER_MONTHLY_SUMMARY": "water_monthly_summary.csv",
            "WASTE_MONTHLY_SUMMARY": "waste_monthly_summary.csv",
            "ELECTRIC_VEHICLE_TRANSITION_QUARTERLY_SUMMARY": "electric_vehicle_transition_quarterly_summary.csv"
        }

        for table_name, file_name in table_files.items():
            file_path = DATA_DIR / file_name
            if file_path.exists():
                conn.execute(f"CREATE TABLE {table_name} AS SELECT * FROM read_csv_auto('{file_path}')")

        result = conn.execute(sql).fetchdf()
        conn.close()

        if result.empty:
            return [], None

        data_points = []
        for _, row in result.iterrows():
            dp = {
                "site": str(row.get("SHE_SITE_NAME", row.get("SHE_MARKET_NAME", "Unknown"))),
                "value": None,
                "unit": kpi_info["unit"]
            }

            # Get period
            year = row.get("REPORTING_YEAR_NUMBER")
            month = row.get("REPORTING_MONTH_NUMBER")
            quarter = row.get("REPORTING_QUARTER_NUMBER")

            if month and year:
                dp["period"] = f"{int(year)}-{int(month):02d}"
            elif quarter and year:
                dp["period"] = f"{int(year)} Q{int(quarter)}"
            else:
                dp["period"] = str(year) if year else "N/A"

            # Get geography for EV data
            if "SHE_GEOGRAPHY_NAME" in row.index:
                dp["geography"] = str(row["SHE_GEOGRAPHY_NAME"])

            # Find KPI value - check standard columns first, then any numeric column
            value_found = False
            for col in result.columns:
                if col.endswith("_QUANTITY") or col.endswith("_COUNT"):
                    val = row.get(col)
                    if val is not None and str(val) != "nan":
                        dp["value"] = float(val)
                        dp["column"] = col
                        value_found = True
                        break

            # If no standard column found, look for any numeric column (handles aliased columns)
            if not value_found:
                skip_cols = {"SHE_SITE_NAME", "SHE_MARKET_NAME", "SHE_GEOGRAPHY_NAME",
                            "REPORTING_YEAR_NUMBER", "REPORTING_MONTH_NUMBER", "REPORTING_QUARTER_NUMBER",
                            "REPORTING_SCOPE_NAME", "SRC_SYS_NM"}
                for col in result.columns:
                    if col not in skip_cols:
                        val = row.get(col)
                        if val is not None and str(val) != "nan":
                            try:
                                dp["value"] = float(val)
                                dp["column"] = col
                                break
                            except (ValueError, TypeError):
                                continue

            if dp["value"] is not None:
                data_points.append(dp)

        data_points.sort(key=lambda x: x["period"], reverse=True)
        return data_points[:20], None

    except Exception as e:
        return [], str(e)


def kpi_agent(state: SIAState) -> dict:
    """KPI Agent that generates SQL, executes it, and explains sustainability data."""
    matched_kpi = state.get("matched_kpi")
    filters = state.get("extracted_filters")
    user_query = state["user_query"]

    if not matched_kpi or matched_kpi not in KPI_CATALOGUE:
        log_entry: AgentLog = {
            "agent_name": "KPI Agent",
            "input_summary": f"KPI: {matched_kpi}",
            "output_summary": "KPI not found in catalogue",
            "reasoning_summary": None,
            "status": "error",
            "timestamp": datetime.now().isoformat()
        }
        return {
            "kpi_results": None,
            "final_answer": f"I couldn't find information about the requested KPI: {matched_kpi}",
            "agent_logs": [log_entry]
        }

    kpi_info = KPI_CATALOGUE[matched_kpi]

    # Generate SQL
    try:
        generated_sql = _generate_sql(user_query, matched_kpi, kpi_info, filters)
    except Exception as e:
        return {
            "kpi_results": None,
            "final_answer": f"Error generating SQL query: {str(e)}",
            "agent_logs": [{
                "agent_name": "KPI Agent",
                "input_summary": f"KPI: {kpi_info['name']}",
                "output_summary": f"SQL generation failed: {str(e)}",
                "reasoning_summary": None,
                "status": "error",
                "timestamp": datetime.now().isoformat()
            }]
        }

    # Execute SQL
    data_points, exec_error = _execute_sql(generated_sql, kpi_info)

    if exec_error:
        error_msg = f"## Query Error\n\n"
        error_msg += f"I encountered an issue while retrieving **{kpi_info['name']}** data.\n\n"
        error_msg += f"**Error:** {exec_error}"

        return {
            "kpi_results": None,
            "generated_sql": generated_sql,
            "final_answer": error_msg,
            "agent_logs": [{
                "agent_name": "KPI Agent",
                "input_summary": f"KPI: {kpi_info['name']}",
                "output_summary": "SQL execution failed",
                "reasoning_summary": f"Generated SQL: {generated_sql[:100]}...",
                "status": "error",
                "timestamp": datetime.now().isoformat()
            }]
        }

    if not data_points:
        no_data_msg = f"## No Data Available\n\n"
        no_data_msg += f"No data found for **{kpi_info['name']}**."
        if filters:
            no_data_msg += "\n\n**Applied Filters:**\n"
            for k, v in filters.items():
                no_data_msg += f"- {k}: {v}\n"

        return {
            "kpi_results": None,
            "generated_sql": generated_sql,
            "final_answer": no_data_msg,
            "agent_logs": [{
                "agent_name": "KPI Agent",
                "input_summary": f"KPI: {kpi_info['name']}",
                "output_summary": "No data returned",
                "reasoning_summary": f"SQL: {generated_sql[:100]}...",
                "status": "error",
                "timestamp": datetime.now().isoformat()
            }]
        }

    kpi_result: KPIResult = {
        "kpi_name": kpi_info["name"],
        "breakdown_by": "Site/Period",
        "data_points": data_points,
        "explanation": None
    }

    # Generate explanation
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
        f"- {dp['site']}: {dp['value']}{dp['unit']} ({dp['period']})"
        for dp in data_points[:10]
    ])

    try:
        messages = [
            SystemMessage(content=response_prompt),
            HumanMessage(content=f"""User asked: {user_query}

Results:
{data_summary}

Provide a clear, concise response.""")
        ]

        response = llm.invoke(messages)
        explanation = response.content

        log_entry: AgentLog = {
            "agent_name": "KPI Agent",
            "input_summary": f"KPI: {kpi_info['name']}",
            "output_summary": f"Retrieved {len(data_points)} data points",
            "reasoning_summary": f"SQL executed on DuckDB. Query: {generated_sql[:100]}...",
            "status": "success",
            "timestamp": datetime.now().isoformat()
        }

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
        simple_response = f"**{kpi_info['name']}**\n\n"
        for dp in data_points[:5]:
            simple_response += f"- {dp['site']}: **{dp['value']}{dp['unit']}** ({dp['period']})\n"

        return {
            "kpi_results": [kpi_result],
            "generated_sql": generated_sql,
            "final_answer": simple_response,
            "agent_logs": [{
                "agent_name": "KPI Agent",
                "input_summary": f"KPI: {kpi_info['name']}",
                "output_summary": "LLM error, using fallback",
                "reasoning_summary": f"SQL executed. Query: {generated_sql[:100]}...",
                "status": "success",
                "timestamp": datetime.now().isoformat()
            }]
        }

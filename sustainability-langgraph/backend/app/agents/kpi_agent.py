"""
KPI Agent for Sustainability Insight Agent
Uses Structured Output JSON Plan for intent classification.
LLM decides WHAT to query (intent), Code decides HOW to query (SQL).
"""

import json
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

# ============================================
# INTENT CLASSIFICATION PROMPT
# ============================================

INTENT_CLASSIFICATION_PROMPT = """You are a SQL PLANNING AGENT. You do NOT write SQL.

Your job:
1) Read the user question about sustainability KPIs.
2) Classify the INTENT and extract parameters.
3) Return a JSON object ONLY. No prose, no SQL, no markdown, no explanation.

## Available Intents:

ENERGY:
- ENERGY_TOTAL: Total energy consumption (current year)
- ENERGY_TOTAL_LAST_YEAR: Energy for previous year
- ENERGY_BY_SITE: Energy breakdown by site
- RENEWABLE_ENERGY: Renewable energy metrics

GHG EMISSIONS:
- GHG_BY_SCOPE: Emissions by Scope 1, Scope 2 (use for "by scope", "by type", "breakdown")
- GHG_TOTAL: Total GHG emissions
- GHG_BY_SITE: Emissions by site
- SCOPE1_EMISSIONS: Only Scope 1
- SCOPE2_EMISSIONS: Only Scope 2

WATER:
- WATER_TOTAL: Total water withdrawn
- WATER_LAST_QUARTER: Water for last quarter
- WATER_BY_SITE: Water by site

WASTE:
- WASTE_TOTAL: Total waste
- WASTE_BY_SITE: Waste by site
- RECYCLED_WASTE: Recycled waste

EV FLEET:
- EV_FLEET_UK: EV data for UK specifically
- EV_FLEET_TOTAL: Total EV fleet data
- EV_BY_MARKET: EV by market
- EV_BY_GEOGRAPHY: EV by geography/region

## Time Filter Rules:
- "last year" or "previous year" or "2024" → time_type: "last_year"
- "last quarter" → time_type: "last_quarter"
- "this year" or "current" or "2025" → time_type: "current_year"
- No time mentioned → time_type: "current_year"

## Geography Filter:
- "UK" or "United Kingdom" → geography: "UK"
- Other specific regions → geography: that region
- No geography → geography: null

## Output Format (JSON only):
{"intent": "INTENT_NAME", "time_type": "current_year|last_year|last_quarter", "geography": null}

## Examples:
User: "What are the greenhouse gas emissions by scope type?"
Output: {"intent": "GHG_BY_SCOPE", "time_type": "current_year", "geography": null}

User: "What was our total energy consumption last year?"
Output: {"intent": "ENERGY_TOTAL_LAST_YEAR", "time_type": "last_year", "geography": null}

User: "What EV fleet data do we have for UK?"
Output: {"intent": "EV_FLEET_UK", "time_type": "current_year", "geography": "UK"}

User: "Total water withdrawn last quarter"
Output: {"intent": "WATER_LAST_QUARTER", "time_type": "last_quarter", "geography": null}

Return ONLY the JSON object. Nothing else."""

# ============================================
# DETERMINISTIC SQL TEMPLATES
# ============================================

SQL_TEMPLATES = {
    # ============ ENERGY ============
    "ENERGY_TOTAL": """
SELECT REPORTING_YEAR_NUMBER, REPORTING_MONTH_NUMBER, SUM(ENERGY_SITE_MWH_QUANTITY) as ENERGY_SITE_MWH_QUANTITY
FROM ENERGY_MONTHLY_SUMMARY
WHERE REPORTING_YEAR_NUMBER = {year}
GROUP BY REPORTING_YEAR_NUMBER, REPORTING_MONTH_NUMBER
ORDER BY REPORTING_MONTH_NUMBER DESC
""",

    "ENERGY_TOTAL_LAST_YEAR": """
SELECT REPORTING_YEAR_NUMBER, REPORTING_MONTH_NUMBER, SUM(ENERGY_SITE_MWH_QUANTITY) as ENERGY_SITE_MWH_QUANTITY
FROM ENERGY_MONTHLY_SUMMARY
WHERE REPORTING_YEAR_NUMBER = {last_year}
GROUP BY REPORTING_YEAR_NUMBER, REPORTING_MONTH_NUMBER
ORDER BY REPORTING_MONTH_NUMBER
""",

    "ENERGY_BY_SITE": """
SELECT SHE_SITE_NAME, SUM(ENERGY_SITE_MWH_QUANTITY) as ENERGY_SITE_MWH_QUANTITY
FROM ENERGY_MONTHLY_SUMMARY
WHERE REPORTING_YEAR_NUMBER = {year}
GROUP BY SHE_SITE_NAME
ORDER BY ENERGY_SITE_MWH_QUANTITY DESC
""",

    "RENEWABLE_ENERGY": """
SELECT REPORTING_YEAR_NUMBER, REPORTING_MONTH_NUMBER, SUM(ENERGY_RENEWABLE_ELECTRICITY_HEAT_MWH_QUANTITY) as ENERGY_RENEWABLE_ELECTRICITY_HEAT_MWH_QUANTITY
FROM ENERGY_MONTHLY_SUMMARY
WHERE REPORTING_YEAR_NUMBER = {year}
GROUP BY REPORTING_YEAR_NUMBER, REPORTING_MONTH_NUMBER
ORDER BY REPORTING_MONTH_NUMBER DESC
""",

    # ============ GHG EMISSIONS ============
    "GHG_BY_SCOPE": """
SELECT 'Scope 1' as SCOPE_TYPE, SUM(SCOPE1_SITE_ENERGY_TCO2_QUANTITY + SCOPE1_F_GASES_TCO2_QUANTITY + SCOPE1_SITE_NON_ENERGY_TCO2_QUANTITY + SCOPE1_SOLVENTS_TCO2_QUANTITY) as EMISSIONS_TCO2
FROM GREENHOUSE_GAS_EMISSIONS_MONTHLY_SUMMARY
WHERE REPORTING_YEAR_NUMBER = {year}
UNION ALL
SELECT 'Scope 2' as SCOPE_TYPE, SUM(SCOPE2_TOTAL_MARKET_BASED_TCO2_QUANTITY) as EMISSIONS_TCO2
FROM GREENHOUSE_GAS_EMISSIONS_MONTHLY_SUMMARY
WHERE REPORTING_YEAR_NUMBER = {year}
UNION ALL
SELECT 'Total (Scope 1+2)' as SCOPE_TYPE, SUM(SCOPE1_SCOPE2_TOTAL_SITE_TCO2_QUANTITY) as EMISSIONS_TCO2
FROM GREENHOUSE_GAS_EMISSIONS_MONTHLY_SUMMARY
WHERE REPORTING_YEAR_NUMBER = {year}
ORDER BY SCOPE_TYPE
""",

    "GHG_TOTAL": """
SELECT REPORTING_YEAR_NUMBER, REPORTING_MONTH_NUMBER, SUM(SCOPE1_SCOPE2_TOTAL_SITE_TCO2_QUANTITY) as SCOPE1_SCOPE2_TOTAL_SITE_TCO2_QUANTITY
FROM GREENHOUSE_GAS_EMISSIONS_MONTHLY_SUMMARY
WHERE REPORTING_YEAR_NUMBER = {year}
GROUP BY REPORTING_YEAR_NUMBER, REPORTING_MONTH_NUMBER
ORDER BY REPORTING_MONTH_NUMBER DESC
""",

    "GHG_BY_SITE": """
SELECT SHE_SITE_NAME, SUM(SCOPE1_SCOPE2_TOTAL_SITE_TCO2_QUANTITY) as SCOPE1_SCOPE2_TOTAL_SITE_TCO2_QUANTITY
FROM GREENHOUSE_GAS_EMISSIONS_MONTHLY_SUMMARY
WHERE REPORTING_YEAR_NUMBER = {year}
GROUP BY SHE_SITE_NAME
ORDER BY SCOPE1_SCOPE2_TOTAL_SITE_TCO2_QUANTITY DESC
""",

    "SCOPE1_EMISSIONS": """
SELECT REPORTING_YEAR_NUMBER, REPORTING_MONTH_NUMBER, SUM(SCOPE1_SITE_ENERGY_TCO2_QUANTITY) as SCOPE1_SITE_ENERGY_TCO2_QUANTITY
FROM GREENHOUSE_GAS_EMISSIONS_MONTHLY_SUMMARY
WHERE REPORTING_YEAR_NUMBER = {year}
GROUP BY REPORTING_YEAR_NUMBER, REPORTING_MONTH_NUMBER
ORDER BY REPORTING_MONTH_NUMBER DESC
""",

    "SCOPE2_EMISSIONS": """
SELECT REPORTING_YEAR_NUMBER, REPORTING_MONTH_NUMBER, SUM(SCOPE2_TOTAL_MARKET_BASED_TCO2_QUANTITY) as SCOPE2_TOTAL_MARKET_BASED_TCO2_QUANTITY
FROM GREENHOUSE_GAS_EMISSIONS_MONTHLY_SUMMARY
WHERE REPORTING_YEAR_NUMBER = {year}
GROUP BY REPORTING_YEAR_NUMBER, REPORTING_MONTH_NUMBER
ORDER BY REPORTING_MONTH_NUMBER DESC
""",

    # ============ WATER ============
    "WATER_TOTAL": """
SELECT REPORTING_YEAR_NUMBER, REPORTING_MONTH_NUMBER, SUM(TOTAL_WATER_WITHDRAWN_MILLION_M3_QUANTITY) as TOTAL_WATER_WITHDRAWN_MILLION_M3_QUANTITY
FROM WATER_MONTHLY_SUMMARY
WHERE REPORTING_YEAR_NUMBER = {year}
GROUP BY REPORTING_YEAR_NUMBER, REPORTING_MONTH_NUMBER
ORDER BY REPORTING_MONTH_NUMBER DESC
""",

    "WATER_LAST_QUARTER": """
SELECT REPORTING_YEAR_NUMBER, REPORTING_QUARTER_NUMBER, REPORTING_MONTH_NUMBER, SUM(TOTAL_WATER_WITHDRAWN_MILLION_M3_QUANTITY) as TOTAL_WATER_WITHDRAWN_MILLION_M3_QUANTITY
FROM WATER_MONTHLY_SUMMARY
WHERE REPORTING_YEAR_NUMBER = {year} AND REPORTING_QUARTER_NUMBER = {last_quarter}
GROUP BY REPORTING_YEAR_NUMBER, REPORTING_QUARTER_NUMBER, REPORTING_MONTH_NUMBER
ORDER BY REPORTING_MONTH_NUMBER DESC
""",

    "WATER_BY_SITE": """
SELECT SHE_SITE_NAME, SUM(TOTAL_WATER_WITHDRAWN_MILLION_M3_QUANTITY) as TOTAL_WATER_WITHDRAWN_MILLION_M3_QUANTITY
FROM WATER_MONTHLY_SUMMARY
WHERE REPORTING_YEAR_NUMBER = {year}
GROUP BY SHE_SITE_NAME
ORDER BY TOTAL_WATER_WITHDRAWN_MILLION_M3_QUANTITY DESC
""",

    # ============ WASTE ============
    "WASTE_TOTAL": """
SELECT REPORTING_YEAR_NUMBER, REPORTING_MONTH_NUMBER, SUM(WASTE_TOTAL_TONNES_QUANTITY) as WASTE_TOTAL_TONNES_QUANTITY
FROM WASTE_MONTHLY_SUMMARY
WHERE REPORTING_YEAR_NUMBER = {year}
GROUP BY REPORTING_YEAR_NUMBER, REPORTING_MONTH_NUMBER
ORDER BY REPORTING_MONTH_NUMBER DESC
""",

    "WASTE_BY_SITE": """
SELECT SHE_SITE_NAME, SUM(WASTE_TOTAL_TONNES_QUANTITY) as WASTE_TOTAL_TONNES_QUANTITY
FROM WASTE_MONTHLY_SUMMARY
WHERE REPORTING_YEAR_NUMBER = {year}
GROUP BY SHE_SITE_NAME
ORDER BY WASTE_TOTAL_TONNES_QUANTITY DESC
""",

    "RECYCLED_WASTE": """
SELECT REPORTING_YEAR_NUMBER, REPORTING_MONTH_NUMBER, SUM(WASTE_RECYCLED_TONNES_QUANTITY) as WASTE_RECYCLED_TONNES_QUANTITY
FROM WASTE_MONTHLY_SUMMARY
WHERE REPORTING_YEAR_NUMBER = {year}
GROUP BY REPORTING_YEAR_NUMBER, REPORTING_MONTH_NUMBER
ORDER BY REPORTING_MONTH_NUMBER DESC
""",

    # ============ EV FLEET ============
    "EV_FLEET_UK": """
SELECT REPORTING_YEAR_NUMBER, REPORTING_QUARTER_NUMBER, SHE_GEOGRAPHY_NAME, SHE_MARKET_NAME,
       TOTAL_BEV_COUNT, TOTAL_FLEET_ASSET_COUNT
FROM ELECTRIC_VEHICLE_TRANSITION_QUARTERLY_SUMMARY
WHERE SHE_GEOGRAPHY_NAME = 'UK' OR SHE_GEOGRAPHY_NAME LIKE '%United Kingdom%'
ORDER BY REPORTING_YEAR_NUMBER DESC, REPORTING_QUARTER_NUMBER DESC
""",

    "EV_FLEET_TOTAL": """
SELECT REPORTING_YEAR_NUMBER, REPORTING_QUARTER_NUMBER, SUM(TOTAL_BEV_COUNT) as TOTAL_BEV_COUNT, SUM(TOTAL_FLEET_ASSET_COUNT) as TOTAL_FLEET_ASSET_COUNT
FROM ELECTRIC_VEHICLE_TRANSITION_QUARTERLY_SUMMARY
GROUP BY REPORTING_YEAR_NUMBER, REPORTING_QUARTER_NUMBER
ORDER BY REPORTING_YEAR_NUMBER DESC, REPORTING_QUARTER_NUMBER DESC
""",

    "EV_BY_MARKET": """
SELECT SHE_MARKET_NAME, SUM(TOTAL_BEV_COUNT) as TOTAL_BEV_COUNT, SUM(TOTAL_FLEET_ASSET_COUNT) as TOTAL_FLEET_ASSET_COUNT
FROM ELECTRIC_VEHICLE_TRANSITION_QUARTERLY_SUMMARY
WHERE REPORTING_YEAR_NUMBER = {year}
GROUP BY SHE_MARKET_NAME
ORDER BY TOTAL_BEV_COUNT DESC
""",

    "EV_BY_GEOGRAPHY": """
SELECT SHE_GEOGRAPHY_NAME, SUM(TOTAL_BEV_COUNT) as TOTAL_BEV_COUNT, SUM(TOTAL_FLEET_ASSET_COUNT) as TOTAL_FLEET_ASSET_COUNT
FROM ELECTRIC_VEHICLE_TRANSITION_QUARTERLY_SUMMARY
WHERE REPORTING_YEAR_NUMBER = {year}
GROUP BY SHE_GEOGRAPHY_NAME
ORDER BY TOTAL_BEV_COUNT DESC
""",
}

# Fallback mapping from KPI ID to intent (if LLM fails)
KPI_TO_INTENT_FALLBACK = {
    "total_energy_consumption": "ENERGY_TOTAL",
    "renewable_energy": "RENEWABLE_ENERGY",
    "solar_energy": "RENEWABLE_ENERGY",
    "total_ghg_emissions": "GHG_TOTAL",
    "scope1_emissions": "SCOPE1_EMISSIONS",
    "scope2_emissions": "SCOPE2_EMISSIONS",
    "f_gases_emissions": "GHG_TOTAL",
    "total_water_withdrawn": "WATER_TOTAL",
    "municipal_water": "WATER_TOTAL",
    "groundwater": "WATER_TOTAL",
    "rainwater_harvesting": "WATER_TOTAL",
    "total_waste": "WASTE_TOTAL",
    "hazardous_waste": "WASTE_TOTAL",
    "recycled_waste": "RECYCLED_WASTE",
    "ev_count": "EV_FLEET_TOTAL",
    "total_fleet_count": "EV_FLEET_TOTAL",
    "ev_transition_rate": "EV_FLEET_TOTAL",
}

RESPONSE_PROMPT = """You are a KPI Agent for the Sustainability Insight Agent (SIA).
Generate a clear, professionally formatted response with excellent structure.

## KPI Details
Name: {kpi_name}
Description: {kpi_description}
Unit: {kpi_unit}
Target: {kpi_target}
Time Period Requested: {time_period}

## CRITICAL RULES:
1. ONLY use the exact values provided in the data - NEVER invent or estimate values
2. If data shows breakdown by scope/category, show that breakdown (not quarterly)
3. If data shows time periods, show the time breakdown
4. The TOTAL must match the data provided

## REQUIRED RESPONSE FORMAT:

**{kpi_name}** is **[TOTAL value with unit]** for {time_period} across all sites.

**Status:** [observation about the value - trend, comparison, etc.]

### Breakdown
[Create a table based on the actual data structure provided - use ONLY the exact values given]

### Key Observations
- **[Observation 1]**: Brief insight using ONLY the exact numbers from the data
- **[Observation 2]**: Trend or pattern based on actual data
- **[Observation 3]**: Recommendation if applicable

## FORMATTING RULES:
1. Use ONLY the exact numeric values from the provided data
2. NEVER invent quarterly breakdowns if data doesn't have them
3. Table columns should match the actual data structure
4. Be concise - sustainability professionals need quick insights
"""


def _classify_intent(user_query: str, kpi_id: str) -> dict:
    """
    Use LLM to classify user intent into structured JSON.
    Returns: {"intent": "INTENT_NAME", "time_type": "...", "geography": ...}
    """
    try:
        llm = ChatBedrock(
            model_id=settings.kpi_model,
            region_name=settings.aws_region,
            model_kwargs={"temperature": 0}
        )

        messages = [
            SystemMessage(content=INTENT_CLASSIFICATION_PROMPT),
            HumanMessage(content=f"User question: {user_query}")
        ]

        response = llm.invoke(messages)
        response_text = response.content.strip()

        # Clean up response - extract JSON if wrapped
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        response_text = response_text.strip()

        # Parse JSON
        intent_json = json.loads(response_text)
        return intent_json

    except Exception as e:
        # Fallback to KPI-based intent
        fallback_intent = KPI_TO_INTENT_FALLBACK.get(kpi_id, "GHG_TOTAL")
        return {
            "intent": fallback_intent,
            "time_type": "current_year",
            "geography": None,
            "_fallback": True,
            "_error": str(e)
        }


def _render_sql_from_intent(intent_json: dict) -> str:
    """
    DETERMINISTIC SQL RENDERING
    LLM decides WHAT (intent), Code decides HOW (SQL)
    """
    intent = intent_json.get("intent", "GHG_TOTAL")
    time_type = intent_json.get("time_type", "current_year")

    # Get template
    template = SQL_TEMPLATES.get(intent)
    if not template:
        # Fallback to a safe default
        template = SQL_TEMPLATES.get("GHG_TOTAL")

    # Calculate time parameters
    data_current_year = 2025  # Latest year with data
    last_year = data_current_year - 1
    now = datetime.now()
    current_quarter = (now.month - 1) // 3 + 1
    last_quarter = current_quarter - 1 if current_quarter > 1 else 4

    # Determine year based on time_type
    if time_type == "last_year":
        year = last_year
    else:
        year = data_current_year

    # Render SQL with parameters
    sql = template.format(
        year=year,
        last_year=last_year,
        current_year=data_current_year,
        last_quarter=last_quarter,
        current_quarter=current_quarter
    )

    return sql.strip()


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
            # Determine site label
            site_name = row.get("SHE_SITE_NAME") or row.get("SHE_MARKET_NAME") or row.get("SHE_GEOGRAPHY_NAME") or row.get("SCOPE_TYPE")
            if site_name and str(site_name) != "nan":
                site_label = str(site_name)
            else:
                site_label = "Total"

            dp = {
                "site": site_label,
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
            elif year:
                dp["period"] = f"{int(year)} Total"
            else:
                dp["period"] = "Total"

            # Get geography for EV data
            if "SHE_GEOGRAPHY_NAME" in row.index:
                dp["geography"] = str(row["SHE_GEOGRAPHY_NAME"])

            # Find KPI value
            value_found = False
            for col in result.columns:
                if col.endswith("_QUANTITY") or col.endswith("_COUNT") or col == "EMISSIONS_TCO2":
                    val = row.get(col)
                    if val is not None and str(val) != "nan":
                        dp["value"] = float(val)
                        dp["column"] = col
                        value_found = True
                        break

            # Fallback to any numeric column
            if not value_found:
                skip_cols = {"SHE_SITE_NAME", "SHE_MARKET_NAME", "SHE_GEOGRAPHY_NAME", "SCOPE_TYPE",
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
    """
    KPI Agent using Structured Output JSON Plan.
    LLM classifies intent → Code renders deterministic SQL.
    """
    matched_kpi = state.get("matched_kpi")
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

    # Step 1: LLM classifies intent (structured output)
    intent_json = _classify_intent(user_query, matched_kpi)
    intent = intent_json.get("intent", "UNKNOWN")

    # Step 2: Code renders SQL deterministically
    generated_sql = _render_sql_from_intent(intent_json)

    # Step 3: Execute SQL
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
                "reasoning_summary": f"Intent: {intent}, SQL: {generated_sql[:100]}...",
                "status": "error",
                "timestamp": datetime.now().isoformat()
            }]
        }

    if not data_points:
        no_data_msg = f"## No Data Available\n\n"
        no_data_msg += f"No data found for **{kpi_info['name']}**."

        return {
            "kpi_results": None,
            "generated_sql": generated_sql,
            "final_answer": no_data_msg,
            "agent_logs": [{
                "agent_name": "KPI Agent",
                "input_summary": f"KPI: {kpi_info['name']}",
                "output_summary": "No data returned",
                "reasoning_summary": f"Intent: {intent}, SQL: {generated_sql[:100]}...",
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

    # Step 4: Generate explanation using LLM
    llm = ChatBedrock(
        model_id=settings.kpi_model,
        region_name=settings.aws_region,
        model_kwargs={"temperature": 0}
    )

    # Determine time period description for the response
    time_type = intent_json.get("time_type", "current_year")
    data_current_year = 2025
    last_year = data_current_year - 1
    if time_type == "last_year":
        time_period = f"Full Year {last_year}"
    elif time_type == "last_quarter":
        now = datetime.now()
        current_quarter = (now.month - 1) // 3 + 1
        last_quarter = current_quarter - 1 if current_quarter > 1 else 4
        time_period = f"Q{last_quarter} {data_current_year if last_quarter < current_quarter else last_year}"
    else:
        time_period = f"Full Year {data_current_year}"

    response_prompt = RESPONSE_PROMPT.format(
        kpi_name=kpi_info["name"],
        kpi_description=kpi_info["description"],
        kpi_unit=kpi_info["unit"],
        kpi_target=kpi_info.get("target", "Not defined"),
        time_period=time_period
    )

    # Determine if this is a breakdown query (use site/scope labels) or time-series (use period)
    is_breakdown_query = any(x in intent for x in ["BY_SCOPE", "BY_SITE", "BY_MARKET", "BY_GEOGRAPHY"])

    # Calculate total for the time period
    # For breakdown queries with a "Total" row, use that value; otherwise sum all values
    if is_breakdown_query:
        # Look for a "Total" row in the data
        total_row = next((dp for dp in data_points if "Total" in dp.get("site", "")), None)
        if total_row:
            total_value = total_row["value"]
        else:
            # No total row, sum all values
            total_value = sum(dp['value'] for dp in data_points if dp['value'] is not None)
    else:
        # For time-series queries, sum all values
        total_value = sum(dp['value'] for dp in data_points if dp['value'] is not None)

    def get_data_label(dp):
        if is_breakdown_query:
            label = dp.get("site", "Unknown")
            return label if label and label != "Total" else dp.get("period", "Unknown")
        return dp.get("period", "Unknown")

    data_summary = f"**TOTAL for {time_period}: {total_value:,.2f}{kpi_info['unit']}**\n\n"
    data_summary += "EXACT DATA (use ONLY these values in your response):\n"
    data_summary += "\n".join([
        f"- {get_data_label(dp)}: {dp['value']:,.2f} {dp['unit']}"
        for dp in data_points[:12]
    ])
    data_summary += "\n\nIMPORTANT: The table above contains ALL available data. Do NOT invent additional rows or quarterly breakdowns."

    try:
        messages = [
            SystemMessage(content=response_prompt),
            HumanMessage(content=f"""User asked: {user_query}

{data_summary}

Create a response using ONLY the exact values listed above. Do NOT generate any values not in the data.""")
        ]

        response = llm.invoke(messages)
        explanation = response.content

        log_entry: AgentLog = {
            "agent_name": "KPI Agent",
            "input_summary": f"KPI: {kpi_info['name']}",
            "output_summary": f"Retrieved {len(data_points)} data points",
            "reasoning_summary": f"Intent: {intent} (Structured Output), SQL rendered deterministically",
            "status": "success",
            "timestamp": datetime.now().isoformat()
        }

        kpi_result["explanation"] = explanation

        # Build chart series from data points (reuse get_data_label from above)
        chart_data = sorted(data_points, key=lambda x: get_data_label(x))
        chart_series = [{
            "name": kpi_info["name"],
            "data": [{"x": get_data_label(dp), "y": dp["value"]} for dp in chart_data]
        }]

        return {
            "kpi_results": [kpi_result],
            "generated_sql": generated_sql,
            "final_answer": explanation,
            "visualization_config": {
                "chartType": "bar",
                "title": kpi_info["name"],
                "series": chart_series,
                "yLabel": kpi_info["unit"].strip()
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
                "reasoning_summary": f"Intent: {intent}, SQL executed",
                "status": "success",
                "timestamp": datetime.now().isoformat()
            }]
        }

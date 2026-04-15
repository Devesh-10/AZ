"""
TEST FILE: Structured Output JSON Plan for KPI Agent
This tests the approach locally before implementing in production.

The LLM classifies INTENT, code renders SQL (deterministic).
"""

import json
from datetime import datetime

# Simulated LLM response for testing
# In production, this would come from Bedrock with structured output

# ============================================
# INTENT SCHEMA (what LLM must return)
# ============================================

INTENT_SCHEMA = {
    "type": "object",
    "properties": {
        "intent": {
            "type": "string",
            "enum": [
                "ENERGY_TOTAL",
                "ENERGY_TOTAL_LAST_YEAR",
                "ENERGY_BY_SITE",
                "RENEWABLE_ENERGY",
                "GHG_BY_SCOPE",
                "GHG_TOTAL",
                "GHG_BY_SITE",
                "SCOPE1_EMISSIONS",
                "SCOPE2_EMISSIONS",
                "WATER_TOTAL",
                "WATER_LAST_QUARTER",
                "WATER_BY_SITE",
                "WASTE_TOTAL",
                "WASTE_BY_SITE",
                "RECYCLED_WASTE",
                "EV_FLEET_UK",
                "EV_FLEET_TOTAL",
                "EV_BY_MARKET",
                "EV_BY_GEOGRAPHY"
            ]
        },
        "time_filter": {
            "type": "object",
            "properties": {
                "type": {"type": "string", "enum": ["current_year", "last_year", "last_quarter", "specific_year", "all_time"]},
                "year": {"type": "integer"},
                "quarter": {"type": "integer"}
            }
        },
        "geography_filter": {
            "type": "string",
            "description": "Optional geography filter like 'UK', 'US', etc."
        },
        "group_by": {
            "type": "string",
            "enum": ["none", "site", "month", "quarter", "scope", "market", "geography"]
        }
    },
    "required": ["intent"]
}

# ============================================
# INTENT CLASSIFICATION PROMPT
# ============================================

INTENT_CLASSIFICATION_PROMPT = """You are a SQL PLANNING AGENT. You do NOT write SQL.

Your job:
1) Read the user question about sustainability KPIs.
2) Classify the INTENT and extract parameters.
3) Return a JSON object matching the schema exactly.
4) Be deterministic - pick canonical defaults.

Available intents:
- ENERGY_TOTAL: Total energy consumption
- ENERGY_TOTAL_LAST_YEAR: Energy consumption for previous year
- ENERGY_BY_SITE: Energy breakdown by site
- RENEWABLE_ENERGY: Renewable energy metrics
- GHG_BY_SCOPE: GHG emissions broken down by Scope 1, 2, 3
- GHG_TOTAL: Total GHG emissions
- GHG_BY_SITE: GHG emissions by site
- SCOPE1_EMISSIONS: Only Scope 1 emissions
- SCOPE2_EMISSIONS: Only Scope 2 emissions
- WATER_TOTAL: Total water withdrawn
- WATER_LAST_QUARTER: Water for last quarter
- WATER_BY_SITE: Water by site
- WASTE_TOTAL: Total waste
- WASTE_BY_SITE: Waste by site
- RECYCLED_WASTE: Recycled waste metrics
- EV_FLEET_UK: EV fleet data for UK
- EV_FLEET_TOTAL: Total EV fleet
- EV_BY_MARKET: EV by market
- EV_BY_GEOGRAPHY: EV by geography/region

Time filter rules:
- If user says "last year" or "previous year" → type: "last_year"
- If user says "last quarter" → type: "last_quarter"
- If user mentions specific year like "2024" → type: "specific_year", year: 2024
- Otherwise → type: "current_year"

Output JSON only. No prose, no SQL, no markdown.

Example output:
{"intent": "GHG_BY_SCOPE", "time_filter": {"type": "current_year"}, "group_by": "scope"}
"""

# ============================================
# DETERMINISTIC SQL TEMPLATES (same as before)
# ============================================

SQL_TEMPLATES = {
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

    "GHG_BY_SCOPE": """
SELECT 'Scope 1' as SCOPE_TYPE, SUM(SCOPE1_SITE_ENERGY_TCO2_QUANTITY) as EMISSIONS_TCO2
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

    "WATER_LAST_QUARTER": """
SELECT REPORTING_YEAR_NUMBER, REPORTING_QUARTER_NUMBER, REPORTING_MONTH_NUMBER, SUM(TOTAL_WATER_WITHDRAWN_MILLION_M3_QUANTITY) as TOTAL_WATER_WITHDRAWN_MILLION_M3_QUANTITY
FROM WATER_MONTHLY_SUMMARY
WHERE REPORTING_YEAR_NUMBER = {year} AND REPORTING_QUARTER_NUMBER = {last_quarter}
GROUP BY REPORTING_YEAR_NUMBER, REPORTING_QUARTER_NUMBER, REPORTING_MONTH_NUMBER
ORDER BY REPORTING_MONTH_NUMBER DESC
""",

    "EV_FLEET_UK": """
SELECT REPORTING_YEAR_NUMBER, REPORTING_QUARTER_NUMBER, SHE_GEOGRAPHY_NAME, SHE_MARKET_NAME,
       TOTAL_BEV_COUNT, TOTAL_FLEET_ASSET_COUNT
FROM ELECTRIC_VEHICLE_TRANSITION_QUARTERLY_SUMMARY
WHERE SHE_GEOGRAPHY_NAME = 'UK' OR SHE_GEOGRAPHY_NAME LIKE '%United Kingdom%'
ORDER BY REPORTING_YEAR_NUMBER DESC, REPORTING_QUARTER_NUMBER DESC
""",
}


def render_sql_from_intent(intent_json: dict) -> str:
    """
    DETERMINISTIC SQL RENDERING
    LLM decides WHAT (intent), Code decides HOW (SQL)
    """
    intent = intent_json.get("intent")
    time_filter = intent_json.get("time_filter", {})

    # Get template
    template = SQL_TEMPLATES.get(intent)
    if not template:
        raise ValueError(f"Unknown intent: {intent}")

    # Calculate time parameters
    data_current_year = 2025  # Latest year with data
    last_year = data_current_year - 1
    current_quarter = 1  # February = Q1
    last_quarter = 4 if current_quarter == 1 else current_quarter - 1

    # Determine year based on time_filter
    time_type = time_filter.get("type", "current_year")
    if time_type == "last_year":
        year = last_year
    elif time_type == "specific_year":
        year = time_filter.get("year", data_current_year)
    else:
        year = data_current_year

    # Render SQL
    sql = template.format(
        year=year,
        last_year=last_year,
        current_year=data_current_year,
        last_quarter=last_quarter
    )

    return sql.strip()


# ============================================
# TEST CASES
# ============================================

def test_structured_output():
    """Test the structured output approach with sample queries"""

    test_cases = [
        {
            "query": "What are the greenhouse gas emissions by scope type?",
            "expected_intent": "GHG_BY_SCOPE"
        },
        {
            "query": "What was our total energy consumption last year?",
            "expected_intent": "ENERGY_TOTAL_LAST_YEAR"
        },
        {
            "query": "Total water withdrawn last quarter",
            "expected_intent": "WATER_LAST_QUARTER"
        },
        {
            "query": "What EV fleet data do we have for UK?",
            "expected_intent": "EV_FLEET_UK"
        }
    ]

    print("=" * 60)
    print("STRUCTURED OUTPUT JSON PLAN - LOCAL TEST")
    print("=" * 60)

    for tc in test_cases:
        print(f"\nQuery: {tc['query']}")
        print(f"Expected Intent: {tc['expected_intent']}")

        # Simulate LLM response (in production, this comes from Bedrock)
        simulated_intent = {"intent": tc["expected_intent"]}

        if tc["expected_intent"] == "ENERGY_TOTAL_LAST_YEAR":
            simulated_intent["time_filter"] = {"type": "last_year"}
        elif tc["expected_intent"] == "WATER_LAST_QUARTER":
            simulated_intent["time_filter"] = {"type": "last_quarter"}
        else:
            simulated_intent["time_filter"] = {"type": "current_year"}

        print(f"Intent JSON: {json.dumps(simulated_intent)}")

        # Render SQL deterministically
        sql = render_sql_from_intent(simulated_intent)
        print(f"Generated SQL (first 100 chars): {sql[:100]}...")
        print("-" * 40)

    print("\n" + "=" * 60)
    print("TEST COMPLETE - SQL generation is DETERMINISTIC")
    print("Same intent JSON always produces same SQL")
    print("=" * 60)


if __name__ == "__main__":
    test_structured_output()

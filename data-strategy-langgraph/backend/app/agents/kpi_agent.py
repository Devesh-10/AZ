"""
KPI Agent for DSA (Data Quality Lifecycle Agent)
Computes data quality metrics on-the-fly by scanning actual operational data using DuckDB.
Unlike MIA's KPI agent which queries pre-computed KPI tables, this agent dynamically
generates SQL to measure completeness, accuracy, uniqueness, consistency, and timeliness.
Uses Claude Sonnet 4.5 for SQL generation and DuckDB for execution.
"""

from datetime import datetime
from pathlib import Path
import duckdb
from langchain_aws import ChatBedrock
from langchain_core.messages import HumanMessage, SystemMessage

from app.core.config import get_settings
from app.models.state import DSAState, AgentLog, KPIResult
from app.tools.data_catalogue import KPI_CATALOGUE

settings = get_settings()

# Data directory - points to root data folder containing all operational data
DATA_DIR = Path(__file__).parent.parent.parent / "data"

# ============================================================
# Table definitions with file paths for DuckDB loading
# ============================================================
TABLE_DEFINITIONS = {
    "analytics_batch_status": {
        "path": "Analytical/analytics_batch_status.csv",
        "columns": [
            "batch_id", "order_id", "material_id", "batch_size", "uom", "route",
            "scheduled_start", "scheduled_end", "cycle_time_hr", "yield_qty", "yield_pct",
            "status", "deviations_count", "rework_flag", "primary_equipment_id",
            "actual_start", "actual_end", "std_yield_pct", "std_cycle_time_hr", "steps",
            "wait_time_min", "active_time_min", "lims_first_pass", "alarm_count",
            "wait_time_hr", "active_time_hr", "delay_vs_schedule_hr", "on_time", "rft",
            "alarms_per_hr", "month", "iso_week"
        ]
    },
    "analytics_order_status": {
        "path": "Analytical/analytics_order_status.csv",
        "columns": [
            "site_id", "plant", "order_id", "order_type", "material_id", "material_desc",
            "uom", "qty_ordered", "scheduled_start", "scheduled_end", "priority",
            "work_center", "bom_version", "std_yield_pct", "std_cycle_time_hr", "status",
            "batches", "qty_produced", "released", "pct_batches_on_time", "avg_cycle_time_hr",
            "deviation_count", "qty_in_full", "on_time", "otif", "schedule_adherence_pct"
        ]
    },
    "lims_results": {
        "path": "Transactional/lims_results.csv",
        "columns": [
            "sample_id", "batch_id", "material_id", "test_name", "analyte", "result_value",
            "unit", "spec_low", "spec_high", "result_status", "sampled_ts", "received_ts",
            "approved_ts", "analyst_id", "tat_days"
        ]
    },
    "mes_pasx_batches": {
        "path": "Transactional/mes_pasx_batches.csv",
        "columns": [
            "batch_id", "order_id", "material_id", "batch_size", "uom", "route",
            "actual_start", "actual_end", "cycle_time_hr", "yield_qty", "yield_pct",
            "status", "deviations_count", "rework_flag", "primary_equipment_id"
        ]
    },
    "mes_pasx_batch_steps": {
        "path": "Transactional/mes_pasx_batch_steps.csv",
        "columns": [
            "batch_id", "step_id", "step_code", "step_name", "sequence", "step_start",
            "step_end", "duration_min", "wait_before_min", "target_temp_C", "target_pH",
            "equipment_id"
        ]
    },
    "sap_orders": {
        "path": "Transactional/sap_orders.csv",
        "columns": [
            "site_id", "plant", "order_id", "order_type", "material_id", "material_desc",
            "uom", "qty_ordered", "scheduled_start", "scheduled_end", "priority",
            "work_center", "bom_version", "std_yield_pct", "std_cycle_time_hr", "status"
        ]
    },
    "events_alarms": {
        "path": "Transactional/events_alarms.csv",
        "columns": [
            "timestamp", "equipment_id", "batch_id", "step_id", "event_type", "code",
            "severity", "description", "duration_sec", "ack_ts", "cleared_ts"
        ]
    },
    "goods_receipts": {
        "path": "Transactional/goods_receipts.csv",
        "columns": [
            "gr_id", "po_id", "material_id", "qty_received", "uom", "receipt_date",
            "lot_id", "coa_status", "qc_release_ts"
        ]
    },
    "inventory_snapshots": {
        "path": "Transactional/inventory_snapshots.csv",
        "columns": [
            "date", "material_id", "on_hand_qty", "uom", "lot_count", "days_on_hand",
            "iso_week"
        ]
    },
    "consumption_movements": {
        "path": "Transactional/consumption_movements.csv",
        "columns": [
            "move_id", "batch_id", "material_id", "qty_issued", "uom", "issue_date",
            "storage_location", "lot_id"
        ]
    },
    "procurement_pos": {
        "path": "Transactional/procurement_pos.csv",
        "columns": [
            "po_id", "vendor_id", "material_id", "qty_ordered", "uom", "order_date",
            "promised_date", "delivery_date", "status", "price_per_uom", "currency",
            "month", "on_time"
        ]
    },
    "equipment_master": {
        "path": "Master data/equipment_master.csv",
        "columns": [
            "equipment_id", "type", "area", "line", "capacity_L"
        ]
    },
    "materials_master": {
        "path": "Master data/materials_master.csv",
        "columns": [
            "material_id", "description", "uom", "std_batch_size", "value_stream",
            "route", "type", "lead_time_days", "critical"
        ]
    },
    "vendors_master": {
        "path": "Master data/vendors_master.csv",
        "columns": [
            "vendor_id", "name", "preferred"
        ]
    }
}


def _build_table_schema_section() -> str:
    """Build a formatted schema description of all tables for the SQL generation prompt."""
    sections = []
    for table_name, table_info in TABLE_DEFINITIONS.items():
        cols = ", ".join(table_info["columns"])
        sections.append(f"### {table_name}\nColumns: {cols}")
    return "\n\n".join(sections)


# SQL Generation system prompt - instructs LLM to compute data quality metrics on the fly
SQL_GENERATION_PROMPT = """You are a SQL expert for a Data Quality Lifecycle Agent.
Your job is to generate SQL queries that COMPUTE data quality metrics by scanning actual operational data.
You do NOT have pre-computed KPI tables. Instead, you must calculate metrics from raw transactional and master data tables.

## Available Tables

{table_schema}

## Data Quality Metric Computation Patterns

### Completeness (percentage of non-null values)
Pattern: ROUND(COUNT(column_name) * 100.0 / COUNT(*), 2) as completeness_pct
- COUNT(*) gives total records
- COUNT(column) gives non-null values for that column
- For multi-column completeness, average the individual percentages

### Accuracy (values within valid ranges or matching master data)
Pattern: ROUND(COUNT(CASE WHEN condition THEN 1 END) * 100.0 / COUNT(*), 2) as accuracy_pct
- Check numeric ranges (e.g., yield_pct BETWEEN 0 AND 110)
- Check referential integrity via LEFT JOIN to master tables

### Uniqueness (no duplicate records)
Pattern: ROUND(COUNT(DISTINCT id_column) * 100.0 / COUNT(id_column), 2) as uniqueness_pct
- Compare COUNT vs COUNT(DISTINCT) on key columns

### Consistency (data agreement across systems)
Pattern: Use JOINs between related tables and compare shared columns
- Compare MES data (mes_pasx_batches) vs analytics (analytics_batch_status)
- Compare SAP orders (sap_orders) vs analytics orders (analytics_order_status)

### Timeliness (how current/fresh the data is)
Pattern: Date/time calculations using DuckDB date functions
- DATEDIFF('day', timestamp_col, CURRENT_DATE) for freshness
- AVG turnaround times
- Records updated within expected timeframes

## KPI to SQL Mapping
{kpi_column_mapping}

## SQL Examples

- "Batch data completeness" ->
  SELECT
    'analytics_batch_status' as table_name,
    COUNT(*) as total_records,
    ROUND(COUNT(yield_pct) * 100.0 / NULLIF(COUNT(*), 0), 2) as yield_completeness,
    ROUND(COUNT(cycle_time_hr) * 100.0 / NULLIF(COUNT(*), 0), 2) as cycle_time_completeness,
    ROUND(COUNT(status) * 100.0 / NULLIF(COUNT(*), 0), 2) as status_completeness,
    ROUND(COUNT(primary_equipment_id) * 100.0 / NULLIF(COUNT(*), 0), 2) as equipment_completeness,
    ROUND((COUNT(yield_pct) + COUNT(cycle_time_hr) + COUNT(status) + COUNT(primary_equipment_id)) * 100.0 / NULLIF(4 * COUNT(*), 0), 2) as overall_completeness_pct
  FROM analytics_batch_status

- "LIMS data completeness" ->
  SELECT
    'lims_results' as table_name,
    COUNT(*) as total_records,
    ROUND(COUNT(result_value) * 100.0 / NULLIF(COUNT(*), 0), 2) as result_value_completeness,
    ROUND(COUNT(spec_low) * 100.0 / NULLIF(COUNT(*), 0), 2) as spec_low_completeness,
    ROUND(COUNT(spec_high) * 100.0 / NULLIF(COUNT(*), 0), 2) as spec_high_completeness,
    ROUND(COUNT(approved_ts) * 100.0 / NULLIF(COUNT(*), 0), 2) as approved_ts_completeness,
    ROUND((COUNT(result_value) + COUNT(spec_low) + COUNT(spec_high) + COUNT(approved_ts)) * 100.0 / NULLIF(4 * COUNT(*), 0), 2) as overall_completeness_pct
  FROM lims_results

- "Equipment reference accuracy" ->
  SELECT
    COUNT(DISTINCT b.primary_equipment_id) as total_equipment_refs,
    COUNT(DISTINCT CASE WHEN e.equipment_id IS NOT NULL THEN b.primary_equipment_id END) as valid_refs,
    ROUND(COUNT(DISTINCT CASE WHEN e.equipment_id IS NOT NULL THEN b.primary_equipment_id END) * 100.0 / NULLIF(COUNT(DISTINCT b.primary_equipment_id), 0), 2) as accuracy_pct
  FROM analytics_batch_status b
  LEFT JOIN equipment_master e ON b.primary_equipment_id = e.equipment_id
  WHERE b.primary_equipment_id IS NOT NULL

- "Material reference accuracy" ->
  SELECT
    COUNT(DISTINCT b.material_id) as total_material_refs,
    COUNT(DISTINCT CASE WHEN m.material_id IS NOT NULL THEN b.material_id END) as valid_refs,
    ROUND(COUNT(DISTINCT CASE WHEN m.material_id IS NOT NULL THEN b.material_id END) * 100.0 / NULLIF(COUNT(DISTINCT b.material_id), 0), 2) as accuracy_pct
  FROM analytics_batch_status b
  LEFT JOIN materials_master m ON b.material_id = m.material_id
  WHERE b.material_id IS NOT NULL

- "Yield data accuracy" ->
  SELECT
    COUNT(*) as total_records,
    COUNT(CASE WHEN yield_pct BETWEEN 0 AND 110 THEN 1 END) as valid_yields,
    ROUND(COUNT(CASE WHEN yield_pct BETWEEN 0 AND 110 THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0), 2) as accuracy_pct
  FROM analytics_batch_status
  WHERE yield_pct IS NOT NULL

- "LIMS spec compliance" ->
  SELECT
    COUNT(*) as total_tests,
    COUNT(CASE WHEN result_value BETWEEN spec_low AND spec_high THEN 1 END) as within_spec,
    ROUND(COUNT(CASE WHEN result_value BETWEEN spec_low AND spec_high THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0), 2) as compliance_pct
  FROM lims_results
  WHERE result_value IS NOT NULL AND spec_low IS NOT NULL AND spec_high IS NOT NULL

- "Cross-system consistency" ->
  SELECT
    COUNT(*) as total_matched_batches,
    SUM(CASE WHEN a.yield_pct = m.yield_pct THEN 1 ELSE 0 END) as yield_matching,
    ROUND(SUM(CASE WHEN a.yield_pct = m.yield_pct THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0), 2) as yield_consistency_pct,
    SUM(CASE WHEN a.status = m.status THEN 1 ELSE 0 END) as status_matching,
    ROUND(SUM(CASE WHEN a.status = m.status THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0), 2) as status_consistency_pct
  FROM analytics_batch_status a
  JOIN mes_pasx_batches m ON a.batch_id = m.batch_id

- "Order-batch consistency" ->
  SELECT
    COUNT(DISTINCT b.order_id) as total_order_refs_in_batches,
    COUNT(DISTINCT CASE WHEN o.order_id IS NOT NULL THEN b.order_id END) as valid_order_refs,
    ROUND(COUNT(DISTINCT CASE WHEN o.order_id IS NOT NULL THEN b.order_id END) * 100.0 / NULLIF(COUNT(DISTINCT b.order_id), 0), 2) as consistency_pct
  FROM analytics_batch_status b
  LEFT JOIN sap_orders o ON b.order_id = o.order_id
  WHERE b.order_id IS NOT NULL

- "Batch ID uniqueness" ->
  SELECT
    'analytics_batch_status' as table_name,
    COUNT(batch_id) as total_count,
    COUNT(DISTINCT batch_id) as unique_count,
    COUNT(batch_id) - COUNT(DISTINCT batch_id) as duplicate_count,
    ROUND(COUNT(DISTINCT batch_id) * 100.0 / NULLIF(COUNT(batch_id), 0), 2) as uniqueness_pct
  FROM analytics_batch_status

- "LIMS turnaround time" ->
  SELECT
    COUNT(*) as total_tests,
    ROUND(AVG(tat_days), 2) as avg_tat_days,
    ROUND(MIN(tat_days), 2) as min_tat_days,
    ROUND(MAX(tat_days), 2) as max_tat_days,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY tat_days), 2) as median_tat_days
  FROM lims_results
  WHERE tat_days IS NOT NULL

- "Data freshness score" ->
  SELECT
    'analytics_batch_status' as table_name,
    COUNT(*) as total_records,
    MAX(TRY_CAST(actual_end AS DATE)) as latest_record,
    ROUND(COUNT(CASE WHEN TRY_CAST(actual_end AS DATE) >= CURRENT_DATE - INTERVAL '30' DAY THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0), 2) as freshness_pct_30d
  FROM analytics_batch_status
  WHERE actual_end IS NOT NULL

- "Master data completeness" ->
  SELECT
    'equipment_master' as table_name,
    COUNT(*) as total_records,
    ROUND((COUNT(equipment_id) + COUNT(type) + COUNT(area) + COUNT(line) + COUNT(capacity_L)) * 100.0 / NULLIF(5 * COUNT(*), 0), 2) as completeness_pct
  FROM equipment_master
  UNION ALL
  SELECT
    'materials_master' as table_name,
    COUNT(*) as total_records,
    ROUND((COUNT(material_id) + COUNT(description) + COUNT(uom) + COUNT(std_batch_size) + COUNT(type)) * 100.0 / NULLIF(5 * COUNT(*), 0), 2) as completeness_pct
  FROM materials_master
  UNION ALL
  SELECT
    'vendors_master' as table_name,
    COUNT(*) as total_records,
    ROUND((COUNT(vendor_id) + COUNT(name) + COUNT(preferred)) * 100.0 / NULLIF(3 * COUNT(*), 0), 2) as completeness_pct
  FROM vendors_master

- "Overall data quality score" ->
  WITH completeness AS (
    SELECT ROUND((COUNT(yield_pct) + COUNT(cycle_time_hr) + COUNT(status) + COUNT(primary_equipment_id)) * 100.0 / NULLIF(4 * COUNT(*), 0), 2) as score FROM analytics_batch_status
  ),
  accuracy AS (
    SELECT ROUND(COUNT(CASE WHEN yield_pct BETWEEN 0 AND 110 THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0), 2) as score FROM analytics_batch_status WHERE yield_pct IS NOT NULL
  ),
  uniqueness AS (
    SELECT ROUND(COUNT(DISTINCT batch_id) * 100.0 / NULLIF(COUNT(batch_id), 0), 2) as score FROM analytics_batch_status
  ),
  consistency AS (
    SELECT ROUND(SUM(CASE WHEN a.yield_pct = m.yield_pct THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0), 2) as score FROM analytics_batch_status a JOIN mes_pasx_batches m ON a.batch_id = m.batch_id
  )
  SELECT
    'Overall DQ Score' as metric,
    (SELECT score FROM completeness) as completeness_score,
    (SELECT score FROM accuracy) as accuracy_score,
    (SELECT score FROM uniqueness) as uniqueness_score,
    (SELECT score FROM consistency) as consistency_score,
    ROUND(((SELECT score FROM completeness) + (SELECT score FROM accuracy) + (SELECT score FROM uniqueness) + (SELECT score FROM consistency)) / 4.0, 2) as overall_dq_score

## Rules
1. Return ONLY the SQL query, no explanations or markdown
2. Use the exact column names from the table schemas above
3. Use standard SQL syntax compatible with DuckDB
4. Always compute percentages using ROUND(..., 2) for readability
5. Use NULLIF(denominator, 0) to avoid division by zero
6. Include descriptive aliases for computed columns (e.g., completeness_pct, accuracy_pct)
7. For completeness metrics, always include total_records count alongside percentage
8. For accuracy metrics, include both valid count and total count
9. For cross-table JOINs, use appropriate join keys (batch_id, order_id, material_id, etc.)
10. Use TRY_CAST for date parsing when computing timeliness metrics
11. For "overall" or "summary" DQ metrics, use CTEs to compute each dimension separately
12. When a metric applies to multiple tables (e.g., completeness across all tables), use UNION ALL
"""

# Response generation prompt for data quality context
RESPONSE_PROMPT = """You are a Data Quality Analyst for a pharmaceutical manufacturing organization.
You are presenting data quality metrics computed from real operational data.

KPI: {kpi_name}
Description: {kpi_description}
Unit: {kpi_unit}
Target: {kpi_target}

## Response Guidelines
1. State the computed metric value clearly and prominently
2. Explain what the metric means in plain business language
3. Compare against the target and indicate if the metric is GOOD (at or above target), WARNING (within 5% of target), or CRITICAL (more than 5% below target)
4. If below target, explain the business impact and suggest specific remediation actions
5. Reference the actual data volumes (record counts) to give context on sample size
6. Use pharmaceutical/GxP terminology where appropriate (e.g., batch records, LIMS, OOS, deviations)
7. Keep the response concise but actionable - focus on what matters and what to do about it
8. Format with markdown for readability (bold key numbers, use bullet points for actions)
"""


def _get_kpi_column_mapping() -> str:
    """Generate KPI to computation approach mapping for SQL prompt."""
    mappings = []
    for kpi_id, info in KPI_CATALOGUE.items():
        mappings.append(
            f"- {info['name']} (kpi_id={kpi_id}): {info['description']} "
            f"[target: {info.get('target', 'N/A')}{info['unit']}]"
        )
    return "\n".join(mappings)


def _generate_sql(user_query: str, kpi_id: str, kpi_info: dict, filters: dict | None) -> str:
    """Use LLM to generate SQL that computes a data quality metric on-the-fly."""
    llm = ChatBedrock(
        model_id=settings.kpi_model,
        region_name=settings.aws_region
    )

    prompt = SQL_GENERATION_PROMPT.format(
        table_schema=_build_table_schema_section(),
        kpi_column_mapping=_get_kpi_column_mapping()
    )

    filter_context = ""
    if filters:
        if filters.get("table"):
            filter_context += f"\nFocus on table: {filters['table']}"
        if filters.get("system"):
            filter_context += f"\nFocus on system: {filters['system']}"
        if filters.get("dimension"):
            filter_context += f"\nData quality dimension: {filters['dimension']}"
        if filters.get("time_period"):
            filter_context += f"\nTime period: {filters['time_period']}"

    messages = [
        SystemMessage(content=prompt),
        HumanMessage(content=f"""Generate a SQL query to compute this data quality metric:

User question: {user_query}

Target KPI: {kpi_info['name']} (kpi_id: {kpi_id})
Description: {kpi_info['description']}
Target: {kpi_info.get('target', 'Not defined')}{kpi_info['unit']}
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
    """Execute SQL using DuckDB against all operational data tables.

    Loads all operational, analytical, and master data CSVs into an in-memory
    DuckDB instance, then executes the generated SQL to compute data quality metrics.

    Args:
        sql: The SQL query to execute
        kpi_id: The KPI identifier from the catalogue
        kpi_info: The KPI metadata from catalogue

    Returns:
        Tuple of (data_points list, error message or None)
    """
    try:
        conn = duckdb.connect(":memory:")

        # Load ALL operational data tables into DuckDB
        for table_name, table_info in TABLE_DEFINITIONS.items():
            csv_path = DATA_DIR / table_info["path"]
            if csv_path.exists():
                # Use quoted path to handle spaces in "Master data" directory
                conn.execute(
                    f"CREATE TABLE {table_name} AS SELECT * FROM read_csv_auto('{csv_path}')"
                )
                print(f"[KPI Agent] Loaded table: {table_name} from {csv_path}")
            else:
                print(f"[KPI Agent] WARNING: CSV not found: {csv_path}")

        # Execute the query
        result = conn.execute(sql).fetchdf()
        conn.close()

        if result.empty:
            print("[KPI Agent] SQL returned empty result")
            return [], None

        print(f"[KPI Agent] SQL result columns: {list(result.columns)}")
        print(f"[KPI Agent] Result shape: {result.shape}")

        # Convert to list of dicts with standardized format
        data_points = []

        # Identify which columns contain metric values vs metadata
        metadata_cols = {
            "table_name", "metric", "dimension", "category", "description"
        }
        count_cols = {
            "total_records", "total_count", "total_tests", "total_matched_batches",
            "total_equipment_refs", "total_material_refs", "total_order_refs_in_batches",
            "valid_refs", "valid_order_refs", "valid_yields", "within_spec",
            "unique_count", "duplicate_count", "yield_matching", "status_matching",
            "min_tat_days", "max_tat_days", "median_tat_days"
        }

        for _, row in result.iterrows():
            dp = {
                "unit": kpi_info["unit"]
            }

            # Determine the label for this data point
            if "table_name" in row.index and str(row.get("table_name", "")) != "nan":
                dp["label"] = str(row["table_name"])
            elif "metric" in row.index and str(row.get("metric", "")) != "nan":
                dp["label"] = str(row["metric"])
            elif "dimension" in row.index and str(row.get("dimension", "")) != "nan":
                dp["label"] = str(row["dimension"])
            else:
                dp["label"] = kpi_info["name"]

            # Extract all numeric values as sub-metrics
            sub_metrics = {}
            primary_value = None

            for col in row.index:
                col_lower = col.lower()
                val = row.get(col)

                # Skip metadata columns
                if col_lower in metadata_cols:
                    continue

                # Skip NaN values
                if val is None or str(val) == "nan":
                    continue

                try:
                    numeric_val = float(val)
                except (ValueError, TypeError):
                    continue

                sub_metrics[col] = numeric_val

                # Determine the primary value - prefer pct/score columns
                if primary_value is None:
                    if any(suffix in col_lower for suffix in [
                        "_pct", "_score", "completeness", "accuracy",
                        "consistency", "uniqueness", "freshness", "compliance",
                        "overall_dq", "avg_tat"
                    ]):
                        primary_value = numeric_val

            # If no percentage/score column found, take the last numeric value
            if primary_value is None and sub_metrics:
                # Prefer the rightmost column (usually the computed metric)
                primary_value = list(sub_metrics.values())[-1]

            if primary_value is not None:
                dp["value"] = primary_value
                dp["sub_metrics"] = sub_metrics
                dp["period"] = dp["label"]  # For chart x-axis
                data_points.append(dp)

        return data_points[:30], None

    except Exception as e:
        print(f"[KPI Agent] SQL execution error: {e}")
        return [], str(e)


def kpi_agent(state: DSAState) -> dict:
    """
    KPI Agent that computes data quality metrics on-the-fly from operational data.

    Flow: Generate SQL -> Execute on DuckDB -> Generate explanation -> Build viz config -> Return state

    Args:
        state: Current DSA state with matched KPI from supervisor

    Returns:
        Updated state with KPI results, generated SQL, visualization config, and explanation
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

    # Step 2: Execute SQL using DuckDB against all operational data
    data_points, exec_error = _execute_sql(generated_sql, matched_kpi, kpi_info)

    if exec_error:
        error_msg = f"## Query Error\n\n"
        error_msg += f"I encountered an issue while computing **{kpi_info['name']}**.\n\n"
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
                reasoning_summary=f"Generated SQL: {generated_sql[:200]}...",
                status="error",
                timestamp=datetime.now().isoformat()
            )]
        }

    if not data_points:
        no_data_msg = f"## No Data Available\n\n"
        no_data_msg += f"I attempted to compute **{kpi_info['name']}** but didn't find any matching records.\n\n"

        if filters:
            no_data_msg += "**Applied Filters:**\n"
            if filters.get("table"):
                no_data_msg += f"- Table: {filters['table']}\n"
            if filters.get("system"):
                no_data_msg += f"- System: {filters['system']}\n"
            if filters.get("dimension"):
                no_data_msg += f"- Dimension: {filters['dimension']}\n"
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
        no_data_msg += "- Verify that the underlying data files exist in the data directory\n"
        no_data_msg += "- Try removing filters to see all available data\n"
        no_data_msg += "- Check if the relevant CSV files contain data\n"

        return {
            "kpi_results": None,
            "generated_sql": generated_sql,
            "final_answer": no_data_msg,
            "agent_logs": [AgentLog(
                agent_name="KPI Agent",
                input_summary=f"KPI: {kpi_info['name']}",
                output_summary="No data returned from query",
                reasoning_summary=f"SQL: {generated_sql[:200]}...",
                status="error",
                timestamp=datetime.now().isoformat()
            )]
        }

    # Build KPI result
    kpi_result = KPIResult(
        kpi_name=kpi_info["name"],
        breakdown_by="Table/Dimension",
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

    # Build data summary for the LLM
    data_summary_lines = []
    for dp in data_points:
        line = f"- {dp['label']}: {dp['value']}{dp['unit']}"
        if "sub_metrics" in dp:
            sub_parts = [
                f"{k}={v}" for k, v in dp["sub_metrics"].items()
                if k not in ("value",)
            ]
            if sub_parts:
                line += f" (details: {', '.join(sub_parts[:6])})"
        data_summary_lines.append(line)
    data_summary = "\n".join(data_summary_lines)

    try:
        messages = [
            SystemMessage(content=response_prompt),
            HumanMessage(content=f"""User question: {user_query}

Computed data quality metric results:
{data_summary}

Target: {kpi_info.get('target', 'Not defined')}{kpi_info['unit']}

SQL used to compute this metric:
{generated_sql}

Answer the user's question based on the computed data above. Provide the metric value, interpretation, and any recommended actions.""")
        ]

        response = llm.invoke(messages)
        explanation = response.content

        log_entry = AgentLog(
            agent_name="KPI Agent",
            input_summary=f"KPI: {kpi_info['name']}, Filters: {filters}",
            output_summary=f"Computed {len(data_points)} data points via on-the-fly SQL",
            reasoning_summary=(
                f"Generated SQL using Claude Sonnet 4.5 to compute {kpi_info['name']} "
                f"from operational data tables via DuckDB. "
                f"Query: {generated_sql[:150]}..."
            ),
            status="success",
            timestamp=datetime.now().isoformat()
        )

        kpi_result["explanation"] = explanation

        # Step 4: Build visualization config
        viz_config = _build_visualization_config(data_points, kpi_info, matched_kpi)

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
            simple_response += f"- **{dp['label']}**: {dp['value']}{dp['unit']}\n"
            if "sub_metrics" in dp:
                for metric_name, metric_val in dp["sub_metrics"].items():
                    if metric_name not in ("value",):
                        simple_response += f"  - {metric_name}: {metric_val}\n"
        if kpi_info.get("target"):
            simple_response += f"\n**Target:** {kpi_info['target']}{kpi_info['unit']}"
        simple_response += f"\n\n**Generated SQL:**\n```sql\n{generated_sql}\n```"

        return {
            "kpi_results": [kpi_result],
            "generated_sql": generated_sql,
            "final_answer": simple_response,
            "visualization_config": _build_visualization_config(data_points, kpi_info, matched_kpi),
            "agent_logs": [AgentLog(
                agent_name="KPI Agent",
                input_summary=f"KPI: {kpi_info['name']}",
                output_summary=f"LLM explanation failed, using fallback: {str(e)}",
                reasoning_summary=(
                    f"SQL generated and executed on DuckDB against operational data. "
                    f"Response generation fallback used. Query: {generated_sql[:150]}..."
                ),
                status="success",
                timestamp=datetime.now().isoformat()
            )]
        }


def _build_visualization_config(
    data_points: list[dict],
    kpi_info: dict,
    kpi_id: str
) -> dict:
    """Build visualization config for the frontend chart component.

    Generates appropriate chart configurations based on the nature of the data:
    - Single metric: gauge-style bar chart
    - Multiple tables/dimensions: grouped bar chart for comparison
    - Time-series data: line chart

    Args:
        data_points: The computed data points
        kpi_info: KPI metadata from catalogue
        kpi_id: The KPI identifier

    Returns:
        Visualization config dict for the frontend
    """
    if not data_points:
        return {}

    labels = [dp.get("label", "Unknown") for dp in data_points]
    has_multiple_labels = len(set(labels)) > 1

    if has_multiple_labels:
        # Multiple data points (e.g., completeness across tables, or DQ dimensions)
        # Use bar chart for comparison
        series_data = [
            {"x": dp["label"], "y": float(dp["value"])}
            for dp in data_points
        ]

        # Add target line reference if available
        target = kpi_info.get("target")

        viz_config = {
            "chartType": "bar",
            "title": kpi_info["name"],
            "xLabel": "Table / Dimension",
            "yLabel": kpi_info["unit"],
            "series": [
                {
                    "name": kpi_info["name"],
                    "data": series_data
                }
            ]
        }

        # Add target reference line if applicable
        if target is not None and kpi_info["unit"] == "%":
            viz_config["referenceLine"] = {
                "y": target,
                "label": f"Target: {target}%"
            }

        return viz_config

    else:
        # Single data point - show with sub-metrics if available
        dp = data_points[0]
        sub_metrics = dp.get("sub_metrics", {})

        if len(sub_metrics) > 1:
            # Show sub-metrics as individual bars for detail
            series_data = []
            for metric_name, metric_val in sub_metrics.items():
                # Create human-readable labels from column names
                label = metric_name.replace("_", " ").replace(" pct", " %").title()
                series_data.append({"x": label, "y": float(metric_val)})

            viz_config = {
                "chartType": "bar",
                "title": kpi_info["name"],
                "xLabel": "Sub-Metric",
                "yLabel": "Value",
                "series": [
                    {
                        "name": kpi_info["name"],
                        "data": series_data
                    }
                ]
            }
        else:
            # Single value - simple bar
            viz_config = {
                "chartType": "bar",
                "title": kpi_info["name"],
                "xLabel": "",
                "yLabel": kpi_info["unit"],
                "series": [
                    {
                        "name": kpi_info["name"],
                        "data": [{"x": kpi_info["name"], "y": float(dp["value"])}]
                    }
                ]
            }

        # Add target reference line if applicable
        target = kpi_info.get("target")
        if target is not None and kpi_info["unit"] == "%":
            viz_config["referenceLine"] = {
                "y": target,
                "label": f"Target: {target}%"
            }

        return viz_config

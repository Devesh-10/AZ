"""
Rules Agent for DSA - Data Quality Lifecycle
Executes DQ validation rules against operational data. Loads rules from
Collibra (via data_source) or falls back to a comprehensive default rule set.
Each rule is a SQL-based check executed in DuckDB, producing pass/fail,
violation count, and sample violation records.
"""

from datetime import datetime
from pathlib import Path
import duckdb

from app.core.config import get_settings
from app.models.state import DSAState, AgentLog

settings = get_settings()

DATA_DIR = Path(__file__).parent.parent.parent / "data"

TABLE_PATHS = {
    "analytics_batch_status": "Analytical/analytics_batch_status.csv",
    "analytics_order_status": "Analytical/analytics_order_status.csv",
    "lims_results": "Transactional/lims_results.csv",
    "mes_pasx_batches": "Transactional/mes_pasx_batches.csv",
    "mes_pasx_batch_steps": "Transactional/mes_pasx_batch_steps.csv",
    "sap_orders": "Transactional/sap_orders.csv",
    "events_alarms": "Transactional/events_alarms.csv",
    "goods_receipts": "Transactional/goods_receipts.csv",
    "inventory_snapshots": "Transactional/inventory_snapshots.csv",
    "consumption_movements": "Transactional/consumption_movements.csv",
    "procurement_pos": "Transactional/procurement_pos.csv",
    "equipment_master": "Master data/equipment_master.csv",
    "materials_master": "Master data/materials_master.csv",
    "vendors_master": "Master data/vendors_master.csv",
}

# ============================================================
# Default DQ Rules - used when Collibra rules are not available
# Each rule: id, name, dimension, severity, table, check_sql, violation_sql
#   check_sql: returns a single row with (total, violations, pass_pct)
#   violation_sql: returns sample violating records
# ============================================================
DEFAULT_RULES = [
    {
        "rule_id": "R001",
        "name": "Batch ID must not be null",
        "dimension": "completeness",
        "severity": "critical",
        "table": "mes_pasx_batches",
        "check_sql": (
            "SELECT COUNT(*) AS total, "
            "SUM(CASE WHEN batch_id IS NULL THEN 1 ELSE 0 END) AS violations, "
            "ROUND(COUNT(batch_id) * 100.0 / NULLIF(COUNT(*), 0), 2) AS pass_pct "
            "FROM mes_pasx_batches"
        ),
        "violation_sql": (
            "SELECT * FROM mes_pasx_batches WHERE batch_id IS NULL LIMIT 10"
        ),
    },
    {
        "rule_id": "R002",
        "name": "Yield percentage must be between 0 and 110",
        "dimension": "accuracy",
        "severity": "high",
        "table": "analytics_batch_status",
        "check_sql": (
            "SELECT COUNT(*) AS total, "
            "SUM(CASE WHEN yield_pct NOT BETWEEN 0 AND 110 THEN 1 ELSE 0 END) AS violations, "
            "ROUND(SUM(CASE WHEN yield_pct BETWEEN 0 AND 110 THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0), 2) AS pass_pct "
            "FROM analytics_batch_status WHERE yield_pct IS NOT NULL"
        ),
        "violation_sql": (
            "SELECT batch_id, yield_pct FROM analytics_batch_status "
            "WHERE yield_pct IS NOT NULL AND yield_pct NOT BETWEEN 0 AND 110 LIMIT 10"
        ),
    },
    {
        "rule_id": "R003",
        "name": "Material ID must exist in materials master",
        "dimension": "accuracy",
        "severity": "high",
        "table": "mes_pasx_batches",
        "check_sql": (
            "SELECT COUNT(DISTINCT t.material_id) AS total, "
            "COUNT(DISTINCT CASE WHEN m.material_id IS NULL THEN t.material_id END) AS violations, "
            "ROUND(COUNT(DISTINCT CASE WHEN m.material_id IS NOT NULL THEN t.material_id END) * 100.0 "
            "/ NULLIF(COUNT(DISTINCT t.material_id), 0), 2) AS pass_pct "
            "FROM mes_pasx_batches t "
            "LEFT JOIN materials_master m ON t.material_id = m.material_id "
            "WHERE t.material_id IS NOT NULL"
        ),
        "violation_sql": (
            "SELECT DISTINCT t.material_id FROM mes_pasx_batches t "
            "LEFT JOIN materials_master m ON t.material_id = m.material_id "
            "WHERE m.material_id IS NULL AND t.material_id IS NOT NULL LIMIT 10"
        ),
    },
    {
        "rule_id": "R004",
        "name": "Equipment ID must exist in equipment master",
        "dimension": "accuracy",
        "severity": "high",
        "table": "analytics_batch_status",
        "check_sql": (
            "SELECT COUNT(DISTINCT t.primary_equipment_id) AS total, "
            "COUNT(DISTINCT CASE WHEN m.equipment_id IS NULL THEN t.primary_equipment_id END) AS violations, "
            "ROUND(COUNT(DISTINCT CASE WHEN m.equipment_id IS NOT NULL THEN t.primary_equipment_id END) * 100.0 "
            "/ NULLIF(COUNT(DISTINCT t.primary_equipment_id), 0), 2) AS pass_pct "
            "FROM analytics_batch_status t "
            "LEFT JOIN equipment_master m ON t.primary_equipment_id = m.equipment_id "
            "WHERE t.primary_equipment_id IS NOT NULL"
        ),
        "violation_sql": (
            "SELECT DISTINCT t.primary_equipment_id FROM analytics_batch_status t "
            "LEFT JOIN equipment_master m ON t.primary_equipment_id = m.equipment_id "
            "WHERE m.equipment_id IS NULL AND t.primary_equipment_id IS NOT NULL LIMIT 10"
        ),
    },
    {
        "rule_id": "R005",
        "name": "Batch ID must be unique in MES batches",
        "dimension": "uniqueness",
        "severity": "critical",
        "table": "mes_pasx_batches",
        "check_sql": (
            "SELECT COUNT(batch_id) AS total, "
            "COUNT(batch_id) - COUNT(DISTINCT batch_id) AS violations, "
            "ROUND(COUNT(DISTINCT batch_id) * 100.0 / NULLIF(COUNT(batch_id), 0), 2) AS pass_pct "
            "FROM mes_pasx_batches"
        ),
        "violation_sql": (
            "SELECT batch_id, COUNT(*) AS dup_count FROM mes_pasx_batches "
            "GROUP BY batch_id HAVING COUNT(*) > 1 ORDER BY dup_count DESC LIMIT 10"
        ),
    },
    {
        "rule_id": "R006",
        "name": "Order ID must be unique in SAP orders",
        "dimension": "uniqueness",
        "severity": "critical",
        "table": "sap_orders",
        "check_sql": (
            "SELECT COUNT(order_id) AS total, "
            "COUNT(order_id) - COUNT(DISTINCT order_id) AS violations, "
            "ROUND(COUNT(DISTINCT order_id) * 100.0 / NULLIF(COUNT(order_id), 0), 2) AS pass_pct "
            "FROM sap_orders"
        ),
        "violation_sql": (
            "SELECT order_id, COUNT(*) AS dup_count FROM sap_orders "
            "GROUP BY order_id HAVING COUNT(*) > 1 ORDER BY dup_count DESC LIMIT 10"
        ),
    },
    {
        "rule_id": "R007",
        "name": "MES and analytics batch status must match",
        "dimension": "consistency",
        "severity": "high",
        "table": "analytics_batch_status",
        "check_sql": (
            "SELECT COUNT(*) AS total, "
            "SUM(CASE WHEN a.status != m.status THEN 1 ELSE 0 END) AS violations, "
            "ROUND(SUM(CASE WHEN a.status = m.status THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0), 2) AS pass_pct "
            "FROM analytics_batch_status a "
            "JOIN mes_pasx_batches m ON a.batch_id = m.batch_id"
        ),
        "violation_sql": (
            "SELECT a.batch_id, a.status AS analytics_status, m.status AS mes_status "
            "FROM analytics_batch_status a "
            "JOIN mes_pasx_batches m ON a.batch_id = m.batch_id "
            "WHERE a.status != m.status LIMIT 10"
        ),
    },
    {
        "rule_id": "R008",
        "name": "MES and analytics yield must match",
        "dimension": "consistency",
        "severity": "high",
        "table": "analytics_batch_status",
        "check_sql": (
            "SELECT COUNT(*) AS total, "
            "SUM(CASE WHEN a.yield_pct != m.yield_pct THEN 1 ELSE 0 END) AS violations, "
            "ROUND(SUM(CASE WHEN a.yield_pct = m.yield_pct THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0), 2) AS pass_pct "
            "FROM analytics_batch_status a "
            "JOIN mes_pasx_batches m ON a.batch_id = m.batch_id"
        ),
        "violation_sql": (
            "SELECT a.batch_id, a.yield_pct AS analytics_yield, m.yield_pct AS mes_yield "
            "FROM analytics_batch_status a "
            "JOIN mes_pasx_batches m ON a.batch_id = m.batch_id "
            "WHERE a.yield_pct != m.yield_pct LIMIT 10"
        ),
    },
    {
        "rule_id": "R009",
        "name": "LIMS results must be within spec limits",
        "dimension": "accuracy",
        "severity": "critical",
        "table": "lims_results",
        "check_sql": (
            "SELECT COUNT(*) AS total, "
            "SUM(CASE WHEN result_value NOT BETWEEN spec_low AND spec_high THEN 1 ELSE 0 END) AS violations, "
            "ROUND(SUM(CASE WHEN result_value BETWEEN spec_low AND spec_high THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0), 2) AS pass_pct "
            "FROM lims_results "
            "WHERE result_value IS NOT NULL AND spec_low IS NOT NULL AND spec_high IS NOT NULL"
        ),
        "violation_sql": (
            "SELECT sample_id, batch_id, test_name, result_value, spec_low, spec_high "
            "FROM lims_results "
            "WHERE result_value IS NOT NULL AND spec_low IS NOT NULL AND spec_high IS NOT NULL "
            "AND result_value NOT BETWEEN spec_low AND spec_high LIMIT 10"
        ),
    },
    {
        "rule_id": "R010",
        "name": "LIMS result must not be null for completed samples",
        "dimension": "completeness",
        "severity": "high",
        "table": "lims_results",
        "check_sql": (
            "SELECT COUNT(*) AS total, "
            "SUM(CASE WHEN result_value IS NULL THEN 1 ELSE 0 END) AS violations, "
            "ROUND(COUNT(result_value) * 100.0 / NULLIF(COUNT(*), 0), 2) AS pass_pct "
            "FROM lims_results"
        ),
        "violation_sql": (
            "SELECT sample_id, batch_id, test_name, result_status "
            "FROM lims_results WHERE result_value IS NULL LIMIT 10"
        ),
    },
    {
        "rule_id": "R011",
        "name": "Batch actual_start must be before actual_end",
        "dimension": "accuracy",
        "severity": "high",
        "table": "mes_pasx_batches",
        "check_sql": (
            "SELECT COUNT(*) AS total, "
            "SUM(CASE WHEN TRY_CAST(actual_start AS TIMESTAMP) > TRY_CAST(actual_end AS TIMESTAMP) THEN 1 ELSE 0 END) AS violations, "
            "ROUND(SUM(CASE WHEN TRY_CAST(actual_start AS TIMESTAMP) <= TRY_CAST(actual_end AS TIMESTAMP) THEN 1 ELSE 0 END) * 100.0 "
            "/ NULLIF(COUNT(*), 0), 2) AS pass_pct "
            "FROM mes_pasx_batches "
            "WHERE actual_start IS NOT NULL AND actual_end IS NOT NULL"
        ),
        "violation_sql": (
            "SELECT batch_id, actual_start, actual_end "
            "FROM mes_pasx_batches "
            "WHERE actual_start IS NOT NULL AND actual_end IS NOT NULL "
            "AND TRY_CAST(actual_start AS TIMESTAMP) > TRY_CAST(actual_end AS TIMESTAMP) LIMIT 10"
        ),
    },
    {
        "rule_id": "R012",
        "name": "Vendor ID must exist in vendors master for procurement POs",
        "dimension": "accuracy",
        "severity": "high",
        "table": "procurement_pos",
        "check_sql": (
            "SELECT COUNT(DISTINCT t.vendor_id) AS total, "
            "COUNT(DISTINCT CASE WHEN m.vendor_id IS NULL THEN t.vendor_id END) AS violations, "
            "ROUND(COUNT(DISTINCT CASE WHEN m.vendor_id IS NOT NULL THEN t.vendor_id END) * 100.0 "
            "/ NULLIF(COUNT(DISTINCT t.vendor_id), 0), 2) AS pass_pct "
            "FROM procurement_pos t "
            "LEFT JOIN vendors_master m ON t.vendor_id = m.vendor_id "
            "WHERE t.vendor_id IS NOT NULL"
        ),
        "violation_sql": (
            "SELECT DISTINCT t.vendor_id FROM procurement_pos t "
            "LEFT JOIN vendors_master m ON t.vendor_id = m.vendor_id "
            "WHERE m.vendor_id IS NULL AND t.vendor_id IS NOT NULL LIMIT 10"
        ),
    },
    {
        "rule_id": "R013",
        "name": "Goods receipt date must not be in the future",
        "dimension": "timeliness",
        "severity": "medium",
        "table": "goods_receipts",
        "check_sql": (
            "SELECT COUNT(*) AS total, "
            "SUM(CASE WHEN TRY_CAST(receipt_date AS DATE) > CURRENT_DATE THEN 1 ELSE 0 END) AS violations, "
            "ROUND(SUM(CASE WHEN TRY_CAST(receipt_date AS DATE) <= CURRENT_DATE THEN 1 ELSE 0 END) * 100.0 "
            "/ NULLIF(COUNT(*), 0), 2) AS pass_pct "
            "FROM goods_receipts WHERE receipt_date IS NOT NULL"
        ),
        "violation_sql": (
            "SELECT gr_id, po_id, receipt_date FROM goods_receipts "
            "WHERE TRY_CAST(receipt_date AS DATE) > CURRENT_DATE LIMIT 10"
        ),
    },
    {
        "rule_id": "R014",
        "name": "Sample ID must be unique in LIMS results",
        "dimension": "uniqueness",
        "severity": "critical",
        "table": "lims_results",
        "check_sql": (
            "SELECT COUNT(sample_id) AS total, "
            "COUNT(sample_id) - COUNT(DISTINCT sample_id) AS violations, "
            "ROUND(COUNT(DISTINCT sample_id) * 100.0 / NULLIF(COUNT(sample_id), 0), 2) AS pass_pct "
            "FROM lims_results"
        ),
        "violation_sql": (
            "SELECT sample_id, COUNT(*) AS dup_count FROM lims_results "
            "GROUP BY sample_id HAVING COUNT(*) > 1 ORDER BY dup_count DESC LIMIT 10"
        ),
    },
    {
        "rule_id": "R015",
        "name": "PO delivery date should be on or after order date",
        "dimension": "accuracy",
        "severity": "medium",
        "table": "procurement_pos",
        "check_sql": (
            "SELECT COUNT(*) AS total, "
            "SUM(CASE WHEN TRY_CAST(delivery_date AS DATE) < TRY_CAST(order_date AS DATE) THEN 1 ELSE 0 END) AS violations, "
            "ROUND(SUM(CASE WHEN TRY_CAST(delivery_date AS DATE) >= TRY_CAST(order_date AS DATE) THEN 1 ELSE 0 END) * 100.0 "
            "/ NULLIF(COUNT(*), 0), 2) AS pass_pct "
            "FROM procurement_pos "
            "WHERE delivery_date IS NOT NULL AND order_date IS NOT NULL"
        ),
        "violation_sql": (
            "SELECT po_id, vendor_id, order_date, delivery_date "
            "FROM procurement_pos "
            "WHERE delivery_date IS NOT NULL AND order_date IS NOT NULL "
            "AND TRY_CAST(delivery_date AS DATE) < TRY_CAST(order_date AS DATE) LIMIT 10"
        ),
    },
]

# Severity weights for prioritisation
SEVERITY_WEIGHTS = {
    "critical": 4,
    "high": 3,
    "medium": 2,
    "low": 1,
}


def _load_tables(conn, table_names=None):
    """Load CSV files into DuckDB as tables."""
    for name, path in TABLE_PATHS.items():
        if table_names and name not in table_names:
            continue
        csv_path = DATA_DIR / path
        if csv_path.exists():
            conn.execute(
                f"CREATE TABLE IF NOT EXISTS {name} AS SELECT * FROM read_csv_auto('{csv_path}')"
            )


def _execute_rule(conn, rule: dict) -> dict:
    """Execute a single DQ rule and return the result.

    Args:
        conn: DuckDB connection with tables loaded
        rule: Rule definition dict

    Returns:
        Rule execution result dict
    """
    result = {
        "rule_id": rule["rule_id"],
        "name": rule["name"],
        "dimension": rule["dimension"],
        "severity": rule["severity"],
        "table": rule["table"],
        "status": "error",
        "total": 0,
        "violations": 0,
        "pass_pct": 0.0,
        "examples": [],
        "check_sql": rule["check_sql"],
    }

    try:
        # Execute the check SQL
        check_result = conn.execute(rule["check_sql"]).fetchone()
        if check_result:
            result["total"] = int(check_result[0]) if check_result[0] is not None else 0
            result["violations"] = int(check_result[1]) if check_result[1] is not None else 0
            result["pass_pct"] = float(check_result[2]) if check_result[2] is not None else 0.0
            result["status"] = "pass" if result["violations"] == 0 else "fail"

        # Get violation examples if there are violations
        if result["violations"] > 0 and rule.get("violation_sql"):
            try:
                violation_rows = conn.execute(rule["violation_sql"]).fetchdf()
                result["examples"] = violation_rows.head(10).to_dict(orient="records")
            except Exception:
                result["examples"] = []

    except Exception as e:
        result["error"] = str(e)
        print(f"[Rules Agent] Error executing rule {rule['rule_id']}: {e}")

    return result


def rules_agent(state: DSAState) -> dict:
    """Rules Agent - executes DQ validation rules against operational data.

    Loads rules from Collibra (via data_source.collibra_rules) or uses a
    comprehensive default rule set. Each rule is a SQL check executed in DuckDB.
    Results include pass/fail status, violation count, and sample violations.

    Args:
        state: Current DSA workflow state

    Returns:
        Dict with rules_result, generated_sql, and agent_logs updates
    """
    start_time = datetime.now()

    # Determine which rules to execute
    data_source = state.get("data_source") or {}
    collibra_rules = data_source.get("collibra_rules", [])

    if collibra_rules:
        rules = collibra_rules
        rules_source = "Collibra"
        print(f"[Rules Agent] Using {len(rules)} Collibra-defined rules")
    else:
        rules = DEFAULT_RULES
        rules_source = "Default"
        print(f"[Rules Agent] Using {len(rules)} default DQ rules")

    # Determine which tables are needed
    required_tables = set()
    for rule in rules:
        required_tables.add(rule["table"])
        # Also add any joined tables (master tables for FK checks)
        check_sql_lower = rule["check_sql"].lower()
        for table_name in TABLE_PATHS:
            if table_name in check_sql_lower:
                required_tables.add(table_name)

    rules_result = []
    all_sql = []

    try:
        conn = duckdb.connect(":memory:")
        _load_tables(conn, table_names=list(required_tables))

        for rule in rules:
            print(f"[Rules Agent] Executing rule {rule['rule_id']}: {rule['name']}")
            result = _execute_rule(conn, rule)
            rules_result.append(result)
            all_sql.append(
                f"-- Rule {rule['rule_id']}: {rule['name']}\n"
                f"-- Dimension: {rule['dimension']} | Severity: {rule['severity']}\n"
                f"{rule['check_sql']};"
            )

        conn.close()

    except Exception as e:
        elapsed = (datetime.now() - start_time).total_seconds()
        log_entry = AgentLog(
            agent_name="Rules",
            input_summary=f"Rules source: {rules_source}, Count: {len(rules)}",
            output_summary=f"DuckDB error: {str(e)}",
            reasoning_summary=None,
            status="error",
            timestamp=datetime.now().isoformat(),
        )
        return {
            "rules_result": [],
            "agent_logs": [log_entry],
        }

    elapsed = (datetime.now() - start_time).total_seconds()
    generated_sql = "\n\n".join(all_sql)

    # Summarize results
    total_rules = len(rules_result)
    passed = sum(1 for r in rules_result if r["status"] == "pass")
    failed = sum(1 for r in rules_result if r["status"] == "fail")
    errored = sum(1 for r in rules_result if r["status"] == "error")
    total_violations = sum(r.get("violations", 0) for r in rules_result)

    # Sort by severity-weighted violations for priority
    for r in rules_result:
        weight = SEVERITY_WEIGHTS.get(r.get("severity", "low"), 1)
        r["priority_score"] = r.get("violations", 0) * weight

    rules_result.sort(key=lambda r: r.get("priority_score", 0), reverse=True)

    # Critical failures
    critical_failures = [
        r for r in rules_result
        if r["status"] == "fail" and r["severity"] == "critical"
    ]

    log_entry = AgentLog(
        agent_name="Rules",
        input_summary=(
            f"Source: {rules_source}, Rules: {total_rules}, "
            f"Tables: {list(required_tables)}"
        ),
        output_summary=(
            f"Passed: {passed}/{total_rules}, Failed: {failed}, Errors: {errored}. "
            f"Total violations: {total_violations}. "
            f"Critical failures: {len(critical_failures)}. "
            f"Elapsed: {elapsed:.2f}s."
        ),
        reasoning_summary=(
            f"Executed {total_rules} DQ rules ({rules_source}) via DuckDB SQL. "
            f"Each rule returns total count, violation count, and pass percentage. "
            f"Violations sorted by severity * count for prioritisation."
        ),
        status="success" if errored == 0 else "error",
        timestamp=datetime.now().isoformat(),
    )

    # Append rules SQL to any existing generated_sql
    existing_sql = state.get("generated_sql") or ""
    combined_sql = (existing_sql + "\n\n" + generated_sql).strip() if existing_sql else generated_sql

    lifecycle_stages = state.get("lifecycle_stages") or []
    result = {
        "rules_result": rules_result,
        "generated_sql": combined_sql,
        "agent_logs": [log_entry],
    }

    if "reporting" not in lifecycle_stages:
        # Generate a rules summary as final_answer
        pass_rate = round(passed * 100.0 / total_rules, 1) if total_rules else 0
        lines = [f"## DQ Rule Validation — {total_rules} Rules ({rules_source})\n"]
        lines.append(f"**Pass Rate: {passed}/{total_rules} ({pass_rate}%)** | Violations: {total_violations}\n")
        lines.append("| Rule | Dimension | Severity | Table | Status | Violations |")
        lines.append("|:-----|:----------|:---------|:------|:-------|:-----------|")
        for r in rules_result:
            status_icon = "Pass" if r["status"] == "pass" else ("**FAIL**" if r["status"] == "fail" else "Error")
            lines.append(
                f"| {r['rule_id']}: {r['name']} "
                f"| {r['dimension']} | {r['severity']} | {r['table']} "
                f"| {status_icon} | {r.get('violations', 0)} |"
            )
        if critical_failures:
            lines.append(f"\n**Critical Failures ({len(critical_failures)}):**")
            for cf in critical_failures:
                lines.append(f"- **{cf['rule_id']}**: {cf['name']} — {cf.get('violations', 0)} violations in `{cf['table']}`")

        result["final_answer"] = "\n".join(lines)

        # Build visualization config for rule results
        result["visualization_config"] = {
            "chartType": "bar",
            "title": f"DQ Rule Validation ({pass_rate}% Pass Rate)",
            "xLabel": "Status",
            "yLabel": "Count",
            "series": [{
                "name": "Rules",
                "data": [
                    {"x": "Passed", "y": passed, "color": "#4CAF50"},
                    {"x": "Failed", "y": failed, "color": "#F44336"},
                    {"x": "Errors", "y": errored, "color": "#FF9800"},
                ],
            }],
        }

    return result

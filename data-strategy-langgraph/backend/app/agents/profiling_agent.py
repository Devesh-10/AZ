"""
Profiling Agent for DSA - Data Quality Lifecycle
Computes the 5 core DQ dimensions (Completeness, Accuracy, Uniqueness,
Consistency, Timeliness) for each discovered table using DuckDB SQL.
Builds on the discovery_result from the Discovery Agent.
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
# FK relationships for accuracy checks (referential integrity)
# Maps: transactional_column -> (master_table, master_column)
# ============================================================
FK_RELATIONSHIPS = {
    "material_id": ("materials_master", "material_id"),
    "primary_equipment_id": ("equipment_master", "equipment_id"),
    "equipment_id": ("equipment_master", "equipment_id"),
    "vendor_id": ("vendors_master", "vendor_id"),
}

# ============================================================
# Range checks for accuracy on specific columns
# Maps: column_name -> (min_valid, max_valid)
# ============================================================
RANGE_CHECKS = {
    "yield_pct": (0, 110),
    "yield_qty": (0, 100000),
    "cycle_time_hr": (0, 500),
    "batch_size": (0, 100000),
    "tat_days": (0, 365),
    "duration_min": (0, 10000),
    "wait_before_min": (0, 5000),
    "target_temp_C": (-50, 200),
    "target_pH": (0, 14),
    "capacity_L": (0, 1000000),
    "qty_ordered": (0, 1000000),
    "qty_produced": (0, 1000000),
    "qty_received": (0, 1000000),
    "qty_issued": (0, 1000000),
    "on_hand_qty": (0, 10000000),
    "days_on_hand": (0, 3650),
    "price_per_uom": (0, 1000000),
    "result_value": (-10000, 10000),
    "duration_sec": (0, 86400),
    "schedule_adherence_pct": (0, 200),
    "std_yield_pct": (0, 110),
    "std_cycle_time_hr": (0, 500),
}

# ============================================================
# Primary/unique key columns per table
# ============================================================
KEY_COLUMNS = {
    "analytics_batch_status": "batch_id",
    "analytics_order_status": "order_id",
    "lims_results": "sample_id",
    "mes_pasx_batches": "batch_id",
    "mes_pasx_batch_steps": "step_id",
    "sap_orders": "order_id",
    "events_alarms": None,  # no single unique key
    "goods_receipts": "gr_id",
    "inventory_snapshots": None,  # composite key (date, material_id)
    "consumption_movements": "move_id",
    "procurement_pos": "po_id",
    "equipment_master": "equipment_id",
    "materials_master": "material_id",
    "vendors_master": "vendor_id",
}

# ============================================================
# Consistency pairs: tables with overlapping data to compare
# (table_a, table_b, join_col, compare_cols)
# ============================================================
CONSISTENCY_PAIRS = [
    (
        "analytics_batch_status", "mes_pasx_batches", "batch_id",
        ["yield_pct", "status", "cycle_time_hr"],
    ),
    (
        "analytics_order_status", "sap_orders", "order_id",
        ["material_id", "status", "qty_ordered"],
    ),
]

# ============================================================
# Timestamp columns per table for timeliness checks
# ============================================================
TIMESTAMP_COLUMNS = {
    "analytics_batch_status": ["actual_end", "actual_start"],
    "analytics_order_status": ["scheduled_end"],
    "lims_results": ["approved_ts", "sampled_ts"],
    "mes_pasx_batches": ["actual_end", "actual_start"],
    "mes_pasx_batch_steps": ["step_end", "step_start"],
    "sap_orders": ["scheduled_end", "scheduled_start"],
    "events_alarms": ["timestamp", "cleared_ts"],
    "goods_receipts": ["receipt_date", "qc_release_ts"],
    "inventory_snapshots": ["date"],
    "consumption_movements": ["issue_date"],
    "procurement_pos": ["delivery_date", "order_date"],
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


def _compute_completeness(conn, table_name: str, columns: list[str]) -> tuple[float, str]:
    """Compute completeness score: average non-null percentage across all columns.

    Returns:
        Tuple of (completeness_score, sql_used)
    """
    if not columns:
        return 100.0, ""

    count_exprs = [f"COUNT(\"{col}\") * 100.0 / NULLIF(COUNT(*), 0)" for col in columns]
    avg_expr = " + ".join(count_exprs) + f") / {len(columns)}"
    sql = (
        f"SELECT ROUND(({avg_expr}, 2) AS completeness_pct FROM {table_name}"
    )
    # Simpler approach: compute per-column then average
    per_col_sql_parts = []
    for col in columns:
        per_col_sql_parts.append(
            f"ROUND(COUNT(\"{col}\") * 100.0 / NULLIF(COUNT(*), 0), 2)"
        )

    sql = (
        f"SELECT\n"
        f"  ({' + '.join(per_col_sql_parts)}) / {len(columns)} AS completeness_pct\n"
        f"FROM {table_name}"
    )

    try:
        result = conn.execute(sql).fetchone()
        score = round(float(result[0]), 2) if result and result[0] is not None else 0.0
    except Exception as e:
        print(f"[Profiling Agent] Completeness error for {table_name}: {e}")
        score = 0.0

    return score, sql


def _compute_accuracy(conn, table_name: str, columns: list[str]) -> tuple[float, str]:
    """Compute accuracy score: range checks on numeric columns + FK match %.

    Returns:
        Tuple of (accuracy_score, sql_used)
    """
    checks = []
    sql_parts = []

    # Range checks on numeric columns
    for col in columns:
        if col in RANGE_CHECKS:
            low, high = RANGE_CHECKS[col]
            range_sql = (
                f"SELECT ROUND(\n"
                f"  COUNT(CASE WHEN \"{col}\" BETWEEN {low} AND {high} THEN 1 END) * 100.0\n"
                f"  / NULLIF(COUNT(\"{col}\"), 0), 2\n"
                f") AS accuracy_pct\n"
                f"FROM {table_name}\n"
                f"WHERE \"{col}\" IS NOT NULL"
            )
            try:
                result = conn.execute(range_sql).fetchone()
                if result and result[0] is not None:
                    checks.append(float(result[0]))
                    sql_parts.append(f"-- Range check: {table_name}.{col} BETWEEN {low} AND {high}\n{range_sql}")
            except Exception:
                pass

    # FK referential integrity checks
    for col in columns:
        if col in FK_RELATIONSHIPS:
            master_table, master_col = FK_RELATIONSHIPS[col]
            # Verify master table exists
            try:
                conn.execute(f"SELECT 1 FROM {master_table} LIMIT 1")
            except Exception:
                continue

            fk_sql = (
                f"SELECT ROUND(\n"
                f"  COUNT(DISTINCT CASE WHEN m.\"{master_col}\" IS NOT NULL THEN t.\"{col}\" END) * 100.0\n"
                f"  / NULLIF(COUNT(DISTINCT t.\"{col}\"), 0), 2\n"
                f") AS fk_accuracy_pct\n"
                f"FROM {table_name} t\n"
                f"LEFT JOIN {master_table} m ON t.\"{col}\" = m.\"{master_col}\"\n"
                f"WHERE t.\"{col}\" IS NOT NULL"
            )
            try:
                result = conn.execute(fk_sql).fetchone()
                if result and result[0] is not None:
                    checks.append(float(result[0]))
                    sql_parts.append(f"-- FK check: {table_name}.{col} -> {master_table}.{master_col}\n{fk_sql}")
            except Exception:
                pass

    if not checks:
        return 100.0, ""

    score = round(sum(checks) / len(checks), 2)
    combined_sql = "\n\n".join(sql_parts)
    return score, combined_sql


def _compute_uniqueness(conn, table_name: str) -> tuple[float, str]:
    """Compute uniqueness score: COUNT(DISTINCT key) / COUNT(key).

    Returns:
        Tuple of (uniqueness_score, sql_used)
    """
    key_col = KEY_COLUMNS.get(table_name)
    if not key_col:
        # No single key column; check full-row uniqueness
        sql = (
            f"SELECT ROUND(\n"
            f"  COUNT(DISTINCT *) * 100.0 / NULLIF(COUNT(*), 0), 2\n"
            f") AS uniqueness_pct\n"
            f"FROM {table_name}"
        )
        # DuckDB does not support COUNT(DISTINCT *); fall back
        sql = (
            f"WITH row_hashes AS (\n"
            f"  SELECT hash(*) AS rh FROM {table_name}\n"
            f")\n"
            f"SELECT ROUND(\n"
            f"  COUNT(DISTINCT rh) * 100.0 / NULLIF(COUNT(rh), 0), 2\n"
            f") AS uniqueness_pct\n"
            f"FROM row_hashes"
        )
    else:
        sql = (
            f"SELECT ROUND(\n"
            f"  COUNT(DISTINCT \"{key_col}\") * 100.0 / NULLIF(COUNT(\"{key_col}\"), 0), 2\n"
            f") AS uniqueness_pct\n"
            f"FROM {table_name}"
        )

    try:
        result = conn.execute(sql).fetchone()
        score = round(float(result[0]), 2) if result and result[0] is not None else 0.0
    except Exception as e:
        print(f"[Profiling Agent] Uniqueness error for {table_name}: {e}")
        score = 100.0
        sql = f"-- Uniqueness check failed: {e}"

    return score, sql


def _compute_consistency(conn, table_name: str) -> tuple[float, str]:
    """Compute consistency score: cross-table join on shared columns.

    Returns:
        Tuple of (consistency_score, sql_used)
    """
    scores = []
    sql_parts = []

    for table_a, table_b, join_col, compare_cols in CONSISTENCY_PAIRS:
        if table_name not in (table_a, table_b):
            continue

        # Verify both tables exist
        try:
            conn.execute(f"SELECT 1 FROM {table_a} LIMIT 1")
            conn.execute(f"SELECT 1 FROM {table_b} LIMIT 1")
        except Exception:
            continue

        for compare_col in compare_cols:
            consistency_sql = (
                f"SELECT ROUND(\n"
                f"  SUM(CASE WHEN a.\"{compare_col}\" = b.\"{compare_col}\" THEN 1 ELSE 0 END) * 100.0\n"
                f"  / NULLIF(COUNT(*), 0), 2\n"
                f") AS consistency_pct\n"
                f"FROM {table_a} a\n"
                f"JOIN {table_b} b ON a.\"{join_col}\" = b.\"{join_col}\""
            )
            try:
                result = conn.execute(consistency_sql).fetchone()
                if result and result[0] is not None:
                    scores.append(float(result[0]))
                    sql_parts.append(
                        f"-- Consistency: {table_a}.{compare_col} vs {table_b}.{compare_col}\n"
                        f"{consistency_sql}"
                    )
            except Exception:
                pass

    if not scores:
        return 100.0, "-- No consistency pairs applicable for this table"

    score = round(sum(scores) / len(scores), 2)
    combined_sql = "\n\n".join(sql_parts)
    return score, combined_sql


def _compute_timeliness(conn, table_name: str) -> tuple[float, str]:
    """Compute timeliness score: % of records with latest timestamp within 30 days.

    Returns:
        Tuple of (timeliness_score, sql_used)
    """
    ts_cols = TIMESTAMP_COLUMNS.get(table_name, [])
    if not ts_cols:
        return 100.0, "-- No timestamp columns to assess timeliness"

    scores = []
    sql_parts = []

    for ts_col in ts_cols:
        timeliness_sql = (
            f"SELECT ROUND(\n"
            f"  COUNT(CASE WHEN TRY_CAST(\"{ts_col}\" AS DATE) >= CURRENT_DATE - INTERVAL '30' DAY THEN 1 END) * 100.0\n"
            f"  / NULLIF(COUNT(*), 0), 2\n"
            f") AS freshness_pct,\n"
            f"  MAX(TRY_CAST(\"{ts_col}\" AS DATE)) AS latest_record\n"
            f"FROM {table_name}\n"
            f"WHERE \"{ts_col}\" IS NOT NULL"
        )
        try:
            result = conn.execute(timeliness_sql).fetchone()
            if result and result[0] is not None:
                scores.append(float(result[0]))
                sql_parts.append(
                    f"-- Timeliness: {table_name}.{ts_col} freshness within 30 days\n"
                    f"{timeliness_sql}"
                )
        except Exception:
            pass

    if not scores:
        return 100.0, "-- Timeliness check could not be executed"

    score = round(sum(scores) / len(scores), 2)
    combined_sql = "\n\n".join(sql_parts)
    return score, combined_sql


def profiling_agent(state: DSAState) -> dict:
    """Profiling Agent - computes 5 DQ dimension scores per table.

    Takes discovery_result from state and computes Completeness, Accuracy,
    Uniqueness, Consistency, and Timeliness scores for each discovered table.
    All checks are executed via DuckDB SQL against in-memory loaded CSVs.

    Args:
        state: Current DSA workflow state with discovery_result

    Returns:
        Dict with profiling_result, generated_sql, and agent_logs updates
    """
    start_time = datetime.now()

    discovery_result = state.get("discovery_result")
    if not discovery_result or not discovery_result.get("tables"):
        log_entry = AgentLog(
            agent_name="Profiling",
            input_summary="No discovery_result in state",
            output_summary="Skipped - no tables discovered",
            reasoning_summary=None,
            status="error",
            timestamp=datetime.now().isoformat(),
        )
        return {
            "profiling_result": None,
            "agent_logs": [log_entry],
        }

    discovered_tables = discovery_result["tables"]
    table_names = list(discovered_tables.keys())

    profiling_result = {}
    all_sql = []

    try:
        conn = duckdb.connect(":memory:")
        _load_tables(conn, table_names=table_names)

        for table_name in table_names:
            table_profile = discovered_tables[table_name]
            if table_profile.get("error"):
                continue

            columns = [c["name"] for c in table_profile.get("columns", [])]
            if not columns:
                continue

            print(f"[Profiling Agent] Profiling dimensions for: {table_name}")

            # Compute all 5 dimensions
            completeness_score, completeness_sql = _compute_completeness(conn, table_name, columns)
            accuracy_score, accuracy_sql = _compute_accuracy(conn, table_name, columns)
            uniqueness_score, uniqueness_sql = _compute_uniqueness(conn, table_name)
            consistency_score, consistency_sql = _compute_consistency(conn, table_name)
            timeliness_score, timeliness_sql = _compute_timeliness(conn, table_name)

            # Weighted overall score
            weights = {
                "completeness": 0.25,
                "accuracy": 0.25,
                "uniqueness": 0.20,
                "consistency": 0.15,
                "timeliness": 0.15,
            }
            overall_score = round(
                completeness_score * weights["completeness"]
                + accuracy_score * weights["accuracy"]
                + uniqueness_score * weights["uniqueness"]
                + consistency_score * weights["consistency"]
                + timeliness_score * weights["timeliness"],
                2,
            )

            profiling_result[table_name] = {
                "table_name": table_name,
                "row_count": table_profile.get("row_count", 0),
                "dimensions": {
                    "completeness": {
                        "score": completeness_score,
                        "weight": weights["completeness"],
                        "description": "Average non-null percentage across all columns",
                    },
                    "accuracy": {
                        "score": accuracy_score,
                        "weight": weights["accuracy"],
                        "description": "Range validity checks and FK referential integrity",
                    },
                    "uniqueness": {
                        "score": uniqueness_score,
                        "weight": weights["uniqueness"],
                        "description": "Duplicate check on primary/unique key columns",
                    },
                    "consistency": {
                        "score": consistency_score,
                        "weight": weights["consistency"],
                        "description": "Cross-system data agreement on shared columns",
                    },
                    "timeliness": {
                        "score": timeliness_score,
                        "weight": weights["timeliness"],
                        "description": "Percentage of records with timestamps within 30 days",
                    },
                },
                "overall_score": overall_score,
            }

            # Collect SQL for transparency
            table_sql_header = f"-- ====== DQ Profiling SQL for {table_name} ======\n"
            table_sqls = [table_sql_header]
            if completeness_sql:
                table_sqls.append(f"-- [Completeness]\n{completeness_sql}")
            if accuracy_sql:
                table_sqls.append(f"-- [Accuracy]\n{accuracy_sql}")
            if uniqueness_sql:
                table_sqls.append(f"-- [Uniqueness]\n{uniqueness_sql}")
            if consistency_sql:
                table_sqls.append(f"-- [Consistency]\n{consistency_sql}")
            if timeliness_sql:
                table_sqls.append(f"-- [Timeliness]\n{timeliness_sql}")
            all_sql.append("\n\n".join(table_sqls))

            print(
                f"[Profiling Agent] {table_name}: "
                f"C={completeness_score} A={accuracy_score} U={uniqueness_score} "
                f"Co={consistency_score} T={timeliness_score} => Overall={overall_score}"
            )

        conn.close()

    except Exception as e:
        elapsed = (datetime.now() - start_time).total_seconds()
        log_entry = AgentLog(
            agent_name="Profiling",
            input_summary=f"Tables: {table_names}",
            output_summary=f"DuckDB error: {str(e)}",
            reasoning_summary=None,
            status="error",
            timestamp=datetime.now().isoformat(),
        )
        return {
            "profiling_result": {"error": str(e), "tables": profiling_result},
            "generated_sql": "\n\n".join(all_sql) if all_sql else None,
            "agent_logs": [log_entry],
        }

    elapsed = (datetime.now() - start_time).total_seconds()
    generated_sql = "\n\n".join(all_sql)

    # Build summary across all tables
    all_scores = [v["overall_score"] for v in profiling_result.values()]
    avg_overall = round(sum(all_scores) / len(all_scores), 2) if all_scores else 0.0
    low_score_tables = [
        k for k, v in profiling_result.items() if v["overall_score"] < 80
    ]

    log_entry = AgentLog(
        agent_name="Profiling",
        input_summary=f"Profiled {len(profiling_result)} tables from discovery_result",
        output_summary=(
            f"Average DQ score: {avg_overall}%. "
            f"Tables below 80%: {low_score_tables or 'None'}. "
            f"Elapsed: {elapsed:.2f}s."
        ),
        reasoning_summary=(
            f"Computed 5 DQ dimensions per table via DuckDB SQL: "
            f"Completeness (null%), Accuracy (range + FK), Uniqueness (distinct/total), "
            f"Consistency (cross-table joins), Timeliness (30-day freshness). "
            f"Weights: C=25%, A=25%, U=20%, Co=15%, T=15%."
        ),
        status="success",
        timestamp=datetime.now().isoformat(),
    )

    # Append profiling SQL to any existing generated_sql
    existing_sql = state.get("generated_sql") or ""
    combined_sql = (existing_sql + "\n\n" + generated_sql).strip() if existing_sql else generated_sql

    # Build standalone final_answer (used when reporting stage is skipped)
    lifecycle_stages = state.get("lifecycle_stages") or []
    result = {
        "profiling_result": profiling_result,
        "generated_sql": combined_sql,
        "agent_logs": [log_entry],
    }

    if "reporting" not in lifecycle_stages:
        # Generate a profiling summary as final_answer
        lines = [f"## Data Quality Profiling — {len(profiling_result)} Tables\n"]
        lines.append(f"**Average DQ Score: {avg_overall}%**\n")
        lines.append("| Table | Completeness | Accuracy | Uniqueness | Consistency | Timeliness | Overall |")
        lines.append("|:------|:------------|:---------|:-----------|:------------|:-----------|:--------|")
        for tname, tdata in profiling_result.items():
            dims = tdata.get("dimensions", {})
            lines.append(
                f"| {tname} "
                f"| {dims.get('completeness', {}).get('score', '-')}% "
                f"| {dims.get('accuracy', {}).get('score', '-')}% "
                f"| {dims.get('uniqueness', {}).get('score', '-')}% "
                f"| {dims.get('consistency', {}).get('score', '-')}% "
                f"| {dims.get('timeliness', {}).get('score', '-')}% "
                f"| **{tdata.get('overall_score', '-')}%** |"
            )
        if low_score_tables:
            lines.append(f"\n**Tables below 80%:** {', '.join(low_score_tables)}")
        lines.append(f"\n*Weights: Completeness 25%, Accuracy 25%, Uniqueness 20%, Consistency 15%, Timeliness 15%*")

        result["final_answer"] = "\n".join(lines)

        # Build a visualization config for the dimension averages
        dim_chart_data = []
        dim_labels = {"completeness": "Completeness", "accuracy": "Accuracy", "uniqueness": "Uniqueness", "consistency": "Consistency", "timeliness": "Timeliness"}
        dim_colors = {"completeness": "#4CAF50", "accuracy": "#2196F3", "uniqueness": "#FF9800", "consistency": "#9C27B0", "timeliness": "#F44336"}
        dim_totals = {}
        dim_counts = {}
        for tdata in profiling_result.values():
            for d, dd in tdata.get("dimensions", {}).items():
                dim_totals[d] = dim_totals.get(d, 0) + dd.get("score", 0)
                dim_counts[d] = dim_counts.get(d, 0) + 1
        for d in ["completeness", "accuracy", "uniqueness", "consistency", "timeliness"]:
            avg = round(dim_totals.get(d, 0) / max(dim_counts.get(d, 1), 1), 2)
            dim_chart_data.append({"x": dim_labels.get(d, d), "y": avg, "color": dim_colors.get(d, "#666")})

        result["visualization_config"] = {
            "chartType": "bar",
            "title": f"DQ Dimension Scores (Average: {avg_overall}%)",
            "xLabel": "Dimension",
            "yLabel": "Score (%)",
            "series": [{"name": "DQ Score", "data": dim_chart_data}],
            "referenceLine": {"y": 95, "label": "Target: 95%"},
        }

    return result

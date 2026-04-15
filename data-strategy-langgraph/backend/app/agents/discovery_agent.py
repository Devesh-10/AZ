"""
Discovery Agent for DSA - Data Quality Lifecycle
Scans all operational data tables to build comprehensive profiles: row counts,
column counts, data types, null percentages, and sample values. Optionally
enriches with Collibra asset metadata when a data_source is configured.
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


def _load_tables(conn, table_names=None):
    """Load CSV files into DuckDB as tables.

    Args:
        conn: DuckDB connection
        table_names: Optional list of table names to load. Loads all if None.
    """
    for name, path in TABLE_PATHS.items():
        if table_names and name not in table_names:
            continue
        csv_path = DATA_DIR / path
        if csv_path.exists():
            conn.execute(
                f"CREATE TABLE IF NOT EXISTS {name} AS SELECT * FROM read_csv_auto('{csv_path}')"
            )


def _profile_table(conn, table_name: str) -> dict:
    """Profile a single table: row count, column metadata, null %, sample values.

    Args:
        conn: DuckDB connection with the table already loaded
        table_name: Name of the table to profile

    Returns:
        Dictionary with table profile information
    """
    profile = {
        "table_name": table_name,
        "row_count": 0,
        "column_count": 0,
        "columns": [],
    }

    try:
        # Row count
        row_count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        profile["row_count"] = row_count

        # Column info via PRAGMA
        col_info = conn.execute(f"PRAGMA table_info('{table_name}')").fetchall()
        profile["column_count"] = len(col_info)

        for col_row in col_info:
            col_name = col_row[1]
            col_type = col_row[2]

            col_profile = {
                "name": col_name,
                "data_type": col_type,
                "null_count": 0,
                "null_pct": 0.0,
                "distinct_count": 0,
                "sample_values": [],
            }

            if row_count > 0:
                # Null count and percentage
                null_result = conn.execute(
                    f"SELECT COUNT(*) - COUNT(\"{col_name}\") AS null_count, "
                    f"ROUND((COUNT(*) - COUNT(\"{col_name}\")) * 100.0 / COUNT(*), 2) AS null_pct "
                    f"FROM {table_name}"
                ).fetchone()
                col_profile["null_count"] = int(null_result[0])
                col_profile["null_pct"] = float(null_result[1])

                # Distinct count
                distinct_result = conn.execute(
                    f"SELECT COUNT(DISTINCT \"{col_name}\") FROM {table_name}"
                ).fetchone()
                col_profile["distinct_count"] = int(distinct_result[0])

                # Sample values (up to 5 non-null distinct values)
                try:
                    sample_rows = conn.execute(
                        f"SELECT DISTINCT \"{col_name}\" FROM {table_name} "
                        f"WHERE \"{col_name}\" IS NOT NULL LIMIT 5"
                    ).fetchall()
                    col_profile["sample_values"] = [str(r[0]) for r in sample_rows]
                except Exception:
                    col_profile["sample_values"] = []

            profile["columns"].append(col_profile)

    except Exception as e:
        profile["error"] = str(e)

    return profile


def _enrich_with_collibra(profiles: dict, data_source: dict) -> dict:
    """Enrich table profiles with Collibra asset metadata if available.

    Args:
        profiles: Dict of table_name -> profile dict
        data_source: Data source config that may contain Collibra metadata

    Returns:
        Enriched profiles dict
    """
    collibra_assets = data_source.get("collibra_assets", {})
    collibra_domain = data_source.get("collibra_domain", "Unknown")
    collibra_community = data_source.get("collibra_community", "Unknown")

    for table_name, profile in profiles.items():
        asset = collibra_assets.get(table_name, {})
        if asset:
            profile["collibra"] = {
                "asset_id": asset.get("asset_id", "N/A"),
                "asset_name": asset.get("asset_name", table_name),
                "domain": collibra_domain,
                "community": collibra_community,
                "status": asset.get("status", "Unknown"),
                "owner": asset.get("owner", "Unassigned"),
                "steward": asset.get("steward", "Unassigned"),
                "classification": asset.get("classification", "Internal"),
                "description": asset.get("description", ""),
                "last_certified": asset.get("last_certified", "N/A"),
            }

            # Enrich columns with Collibra attribute metadata
            collibra_columns = asset.get("columns", {})
            for col in profile.get("columns", []):
                col_meta = collibra_columns.get(col["name"], {})
                if col_meta:
                    col["collibra"] = {
                        "business_name": col_meta.get("business_name", col["name"]),
                        "description": col_meta.get("description", ""),
                        "sensitivity": col_meta.get("sensitivity", "Non-sensitive"),
                        "is_pii": col_meta.get("is_pii", False),
                        "business_rule": col_meta.get("business_rule", ""),
                    }
        else:
            profile["collibra"] = {
                "status": "Not registered",
                "domain": collibra_domain,
                "note": f"Table '{table_name}' not found in Collibra catalogue",
            }

    return profiles


def discovery_agent(state: DSAState) -> dict:
    """Discovery Agent - scans all data tables and builds comprehensive profiles.

    Scans each table using DuckDB to collect: row counts, column counts,
    data types, null percentages per column, distinct counts, and sample values.
    If a Collibra data source is configured, enriches profiles with governance metadata.

    Args:
        state: Current DSA workflow state

    Returns:
        Dict with discovery_result and agent_logs updates
    """
    start_time = datetime.now()

    # Determine which tables to scan
    target_table = state.get("extracted_filters", {}).get("table") if state.get("extracted_filters") else None
    if target_table:
        # Map user-friendly names to table keys
        target_tables = []
        for table_key in TABLE_PATHS:
            if target_table.lower() in table_key.lower():
                target_tables.append(table_key)
        # If no match found, scan all tables
        if not target_tables:
            target_tables = None
    else:
        target_tables = None

    profiles = {}
    tables_scanned = 0
    tables_failed = 0

    try:
        conn = duckdb.connect(":memory:")
        _load_tables(conn, table_names=target_tables)

        # Determine which tables were loaded
        loaded_tables = conn.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
        ).fetchall()
        loaded_table_names = [row[0] for row in loaded_tables]

        for table_name in loaded_table_names:
            try:
                profile = _profile_table(conn, table_name)
                profiles[table_name] = profile
                tables_scanned += 1
                print(f"[Discovery Agent] Profiled: {table_name} "
                      f"({profile['row_count']} rows, {profile['column_count']} cols)")
            except Exception as e:
                profiles[table_name] = {"table_name": table_name, "error": str(e)}
                tables_failed += 1
                print(f"[Discovery Agent] Error profiling {table_name}: {e}")

        conn.close()

    except Exception as e:
        elapsed = (datetime.now() - start_time).total_seconds()
        log_entry = AgentLog(
            agent_name="Discovery",
            input_summary=f"Target tables: {target_tables or 'all'}",
            output_summary=f"DuckDB connection failed: {str(e)}",
            reasoning_summary=None,
            status="error",
            timestamp=datetime.now().isoformat(),
        )
        return {
            "discovery_result": {"error": str(e), "tables": {}, "elapsed_sec": elapsed},
            "agent_logs": [log_entry],
        }

    # Enrich with Collibra metadata if available
    data_source = state.get("data_source")
    if data_source and data_source.get("collibra_assets"):
        profiles = _enrich_with_collibra(profiles, data_source)
        print("[Discovery Agent] Enriched profiles with Collibra metadata")

    elapsed = (datetime.now() - start_time).total_seconds()

    # Build summary statistics
    total_rows = sum(p.get("row_count", 0) for p in profiles.values())
    total_columns = sum(p.get("column_count", 0) for p in profiles.values())
    tables_with_nulls = sum(
        1 for p in profiles.values()
        if any(c.get("null_pct", 0) > 0 for c in p.get("columns", []))
    )

    discovery_result = {
        "tables": profiles,
        "summary": {
            "tables_scanned": tables_scanned,
            "tables_failed": tables_failed,
            "total_rows": total_rows,
            "total_columns": total_columns,
            "tables_with_nulls": tables_with_nulls,
            "has_collibra": bool(data_source and data_source.get("collibra_assets")),
            "elapsed_sec": round(elapsed, 2),
        },
    }

    log_entry = AgentLog(
        agent_name="Discovery",
        input_summary=f"Target: {target_tables or 'all tables'}, Data source: {'Collibra-enriched' if data_source else 'local CSV'}",
        output_summary=(
            f"Scanned {tables_scanned} tables ({tables_failed} failed). "
            f"Total: {total_rows} rows across {total_columns} columns. "
            f"{tables_with_nulls} tables contain null values."
        ),
        reasoning_summary=(
            f"Loaded CSV files into DuckDB in-memory, profiled each table with "
            f"PRAGMA table_info, COUNT/COUNT(col) for nulls, COUNT(DISTINCT) for "
            f"uniqueness. Elapsed: {elapsed:.2f}s."
        ),
        status="success" if tables_failed == 0 else "error",
        timestamp=datetime.now().isoformat(),
    )

    return {
        "discovery_result": discovery_result,
        "agent_logs": [log_entry],
    }

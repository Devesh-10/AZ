"""
Data Table Catalogue for DSA - Data Quality Lifecycle Agent
Describes operational data tables from a data quality perspective.
"""

from typing import TypedDict


class TableMetadata(TypedDict):
    name: str
    description: str
    file_path: str
    category: str
    columns: list[str]
    key_columns: list[str]
    sample_values: dict[str, list[str]]
    sample_queries: list[str]
    aliases: list[str]


DATA_TABLE_CATALOGUE: dict[str, TableMetadata] = {
    "analytics_batch_status": {
        "name": "Batch Status Analytics",
        "description": "Pre-computed batch analytics with yield, cycle time, wait time, RFT, deviations, "
                      "and quality status. Critical table for data quality monitoring - contains key "
                      "manufacturing KPIs that downstream reports depend on.",
        "file_path": "Analytical/analytics_batch_status.csv",
        "category": "Analytical",
        "columns": ["batch_id", "order_id", "material_id", "batch_size", "uom", "route", "scheduled_start",
                   "scheduled_end", "cycle_time_hr", "yield_qty", "yield_pct", "status", "deviations_count",
                   "rework_flag", "primary_equipment_id", "actual_start", "actual_end", "std_yield_pct",
                   "std_cycle_time_hr", "steps", "wait_time_min", "active_time_min", "lims_first_pass",
                   "alarm_count", "wait_time_hr", "active_time_hr", "delay_vs_schedule_hr", "on_time",
                   "rft", "alarms_per_hr", "month", "iso_week"],
        "key_columns": ["batch_id", "yield_pct", "status", "cycle_time_hr", "rft"],
        "sample_values": {
            "status": ["Released", "Quarantined", "Rejected", "In Progress"]
        },
        "sample_queries": [
            "How complete is the batch status data?",
            "Profile the batch analytics table",
            "Are there null values in batch yield?",
            "Data quality of batch records",
            "Missing values in batch status",
            "Batch data completeness check",
            "How many batch records have missing equipment IDs?",
            "Validate batch data quality"
        ],
        "aliases": ["batch status", "batch analytics", "batch data", "batch quality"]
    },

    "analytics_order_status": {
        "name": "Order Status Analytics",
        "description": "Production order analytics with schedule adherence, OTIF, and delivery metrics. "
                      "Contains site and plant information. Key for tracking order data quality.",
        "file_path": "Analytical/analytics_order_status.csv",
        "category": "Analytical",
        "columns": ["site_id", "plant", "order_id", "order_type", "material_id", "material_desc", "uom",
                   "qty_ordered", "scheduled_start", "scheduled_end", "priority", "work_center",
                   "bom_version", "std_yield_pct", "std_cycle_time_hr", "status", "batches",
                   "qty_produced", "released", "pct_batches_on_time", "avg_cycle_time_hr",
                   "deviation_count", "qty_in_full", "on_time", "otif", "schedule_adherence_pct"],
        "key_columns": ["order_id", "site_id", "status", "schedule_adherence_pct"],
        "sample_values": {
            "status": ["TECO", "REL", "CRTD"],
            "site_id": ["FCTN-PLANT-01", "MCLS-PLANT-02", "SODR-PLANT-03"]
        },
        "sample_queries": [
            "How complete is the order data?",
            "Profile order status table",
            "Missing values in order records",
            "Order data quality assessment",
            "Are there orders with missing quantities?"
        ],
        "aliases": ["order status", "order data", "production orders", "order quality"]
    },

    "lims_results": {
        "name": "LIMS Test Results",
        "description": "Laboratory test results with sample data, spec limits, pass/fail status, and "
                      "turnaround times. Critical for quality compliance - data quality issues here "
                      "directly impact batch release decisions.",
        "file_path": "Transactional/lims_results.csv",
        "category": "Transactional",
        "columns": ["sample_id", "batch_id", "material_id", "test_name", "analyte", "result_value",
                   "unit", "spec_low", "spec_high", "result_status", "sampled_ts", "received_ts",
                   "approved_ts", "analyst_id", "tat_days"],
        "key_columns": ["sample_id", "batch_id", "result_value", "result_status", "tat_days"],
        "sample_values": {
            "test_name": ["Assay", "Impurity A", "pH", "Endotoxin"],
            "result_status": ["PASS", "FAIL"]
        },
        "sample_queries": [
            "How complete is the LIMS data?",
            "Profile LIMS test results",
            "Are there missing spec limits in LIMS?",
            "LIMS data quality check",
            "Missing result values in lab data",
            "LIMS turnaround time analysis",
            "Out of spec results",
            "Test result data quality"
        ],
        "aliases": ["LIMS", "lab results", "test results", "LIMS data", "lab data quality"]
    },

    "mes_pasx_batches": {
        "name": "MES Batch Records",
        "description": "Raw MES batch execution records from PAS-X. Source of truth for batch data - "
                      "should be consistent with analytics_batch_status.",
        "file_path": "Transactional/mes_pasx_batches.csv",
        "category": "Transactional",
        "columns": ["batch_id", "order_id", "material_id", "batch_size", "uom", "route",
                   "actual_start", "actual_end", "cycle_time_hr", "yield_qty", "yield_pct",
                   "status", "deviations_count", "rework_flag", "primary_equipment_id"],
        "key_columns": ["batch_id", "order_id", "status", "yield_pct"],
        "sample_values": {
            "status": ["Completed", "In Progress", "Scheduled"]
        },
        "sample_queries": [
            "MES batch data quality",
            "Do MES batches match analytics batches?",
            "Cross-system consistency check for batches",
            "Profile MES batch records",
            "Missing values in MES data"
        ],
        "aliases": ["MES batches", "PAS-X batches", "MES data", "batch execution data"]
    },

    "mes_pasx_batch_steps": {
        "name": "MES Batch Steps",
        "description": "Step-by-step manufacturing process data for each batch. Contains timing, "
                      "temperature, and pH targets. Data quality critical for lead time calculations.",
        "file_path": "Transactional/mes_pasx_batch_steps.csv",
        "category": "Transactional",
        "columns": ["batch_id", "step_id", "step_code", "step_name", "sequence", "step_start",
                   "step_end", "duration_min", "wait_before_min", "target_temp_C", "target_pH",
                   "equipment_id"],
        "key_columns": ["batch_id", "step_code", "duration_min", "wait_before_min"],
        "sample_values": {
            "step_code": ["CHRG", "MIX", "HEAT", "HOLD", "COOL", "FLT", "FILL"],
            "step_name": ["Charge", "Mix", "Heat", "Hold", "Cool", "Filter", "Fill/Pack"]
        },
        "sample_queries": [
            "Profile batch step data",
            "Missing timestamps in batch steps",
            "Batch step data completeness",
            "Are there steps with null duration?",
            "Step timing data quality"
        ],
        "aliases": ["batch steps", "process steps", "MES steps", "step data quality"]
    },

    "sap_orders": {
        "name": "SAP Production Orders",
        "description": "SAP ERP production order data. Should match analytics_order_status for consistency.",
        "file_path": "Transactional/sap_orders.csv",
        "category": "Transactional",
        "columns": ["site_id", "plant", "order_id", "order_type", "material_id", "material_desc",
                   "uom", "qty_ordered", "scheduled_start", "scheduled_end", "priority",
                   "work_center", "bom_version", "std_yield_pct", "std_cycle_time_hr", "status"],
        "key_columns": ["order_id", "site_id", "status", "material_id"],
        "sample_values": {
            "status": ["TECO", "REL", "CRTD"]
        },
        "sample_queries": [
            "SAP order data quality",
            "Do SAP orders match analytics orders?",
            "Cross-system consistency for orders",
            "Profile SAP order data"
        ],
        "aliases": ["SAP orders", "ERP orders", "SAP data quality"]
    },

    "events_alarms": {
        "name": "Equipment Events and Alarms",
        "description": "Equipment alarm and event data. Data quality impacts equipment reliability analysis.",
        "file_path": "Transactional/events_alarms.csv",
        "category": "Transactional",
        "columns": ["timestamp", "equipment_id", "batch_id", "step_id", "event_type", "code",
                   "severity", "description", "duration_sec", "ack_ts", "cleared_ts"],
        "key_columns": ["equipment_id", "batch_id", "event_type", "severity"],
        "sample_values": {
            "event_type": ["Alarm", "Warning"],
            "severity": ["Low", "Medium", "High"]
        },
        "sample_queries": [
            "Alarm data quality check",
            "Missing alarm acknowledgment times",
            "Profile events and alarms data",
            "Alarm data completeness"
        ],
        "aliases": ["alarms", "events", "alarm data", "equipment events"]
    },

    "goods_receipts": {
        "name": "Goods Receipts",
        "description": "Incoming material receipts with COA status and QC release dates.",
        "file_path": "Transactional/goods_receipts.csv",
        "category": "Transactional",
        "columns": ["gr_id", "po_id", "material_id", "qty_received", "uom", "receipt_date",
                   "lot_id", "coa_status", "qc_release_ts"],
        "key_columns": ["gr_id", "material_id", "coa_status"],
        "sample_values": {
            "coa_status": ["Accepted", "Rejected"]
        },
        "sample_queries": [
            "Goods receipt data quality",
            "Missing QC release dates in receipts",
            "Profile goods receipt data"
        ],
        "aliases": ["goods receipts", "GR data", "receiving data"]
    },

    "inventory_snapshots": {
        "name": "Inventory Snapshots",
        "description": "Weekly inventory snapshot data with material quantities on hand.",
        "file_path": "Transactional/inventory_snapshots.csv",
        "category": "Transactional",
        "columns": ["date", "material_id", "on_hand_qty", "uom", "lot_count", "days_on_hand", "iso_week"],
        "key_columns": ["material_id", "on_hand_qty", "days_on_hand"],
        "sample_values": {},
        "sample_queries": [
            "Inventory data quality",
            "Profile inventory snapshots",
            "Missing inventory records"
        ],
        "aliases": ["inventory", "stock data", "inventory data quality"]
    },

    "consumption_movements": {
        "name": "Material Consumption",
        "description": "Material consumption movements for production batches.",
        "file_path": "Transactional/consumption_movements.csv",
        "category": "Transactional",
        "columns": ["move_id", "batch_id", "material_id", "qty_issued", "uom", "issue_date",
                   "storage_location", "lot_id"],
        "key_columns": ["batch_id", "material_id", "qty_issued"],
        "sample_values": {
            "storage_location": ["COLD", "HAZ", "AMBIENT"]
        },
        "sample_queries": [
            "Consumption data quality",
            "Profile material consumption data",
            "Missing lot IDs in consumption"
        ],
        "aliases": ["consumption", "material usage", "consumption data quality"]
    },

    "procurement_pos": {
        "name": "Procurement Purchase Orders",
        "description": "Purchase order data for raw material procurement.",
        "file_path": "Transactional/procurement_pos.csv",
        "category": "Transactional",
        "columns": ["po_id", "vendor_id", "material_id", "qty_ordered", "uom", "order_date",
                   "promised_date", "delivery_date", "status", "price_per_uom", "currency",
                   "month", "on_time"],
        "key_columns": ["po_id", "vendor_id", "status", "on_time"],
        "sample_values": {
            "status": ["Closed", "Open"]
        },
        "sample_queries": [
            "Procurement data quality",
            "Profile purchase order data",
            "Missing delivery dates in POs"
        ],
        "aliases": ["PO data", "procurement data", "purchase order quality"]
    },

    "equipment_master": {
        "name": "Equipment Master",
        "description": "Master data for manufacturing equipment. Small but critical - referenced by many tables.",
        "file_path": "Master data/equipment_master.csv",
        "category": "Master",
        "columns": ["equipment_id", "type", "area", "line", "capacity_L"],
        "key_columns": ["equipment_id", "type", "area"],
        "sample_values": {
            "type": ["Reactor", "Centrifuge", "FilterSkid", "FillerLine", "TabletPress"]
        },
        "sample_queries": [
            "Equipment master data quality",
            "Profile equipment master",
            "Are all equipment IDs referenced in transactions valid?"
        ],
        "aliases": ["equipment master", "equipment data", "machine data"]
    },

    "materials_master": {
        "name": "Materials Master",
        "description": "Master data for all materials. Critical reference table for material_id lookups.",
        "file_path": "Master data/materials_master.csv",
        "category": "Master",
        "columns": ["material_id", "description", "uom", "std_batch_size", "value_stream", "route", "type",
                   "lead_time_days", "critical"],
        "key_columns": ["material_id", "description", "type"],
        "sample_values": {
            "type": ["FG", "RM"]
        },
        "sample_queries": [
            "Material master data quality",
            "Profile materials master",
            "Missing fields in material master",
            "Are all material IDs in transactions valid?"
        ],
        "aliases": ["materials master", "material data", "product master"]
    },

    "vendors_master": {
        "name": "Vendors Master",
        "description": "Master data for suppliers/vendors. Referenced by procurement data.",
        "file_path": "Master data/vendors_master.csv",
        "category": "Master",
        "columns": ["vendor_id", "name", "preferred"],
        "key_columns": ["vendor_id", "name", "preferred"],
        "sample_values": {
            "preferred": ["True", "False"]
        },
        "sample_queries": [
            "Vendor master data quality",
            "Profile vendor data",
            "Are all vendor IDs in POs valid?"
        ],
        "aliases": ["vendor master", "supplier data", "vendor data quality"]
    },

    "kpi_store_monthly": {
        "name": "Monthly KPI Store",
        "description": "Pre-computed monthly KPI metrics covering yield, OEE, RFT, and other manufacturing "
                      "KPIs aggregated by month. Data quality here affects executive dashboards.",
        "file_path": "KPI/kpi_store_monthly.csv",
        "category": "KPI",
        "columns": ["month", "site_id", "kpi_id", "kpi_name", "value", "target", "unit", "trend"],
        "key_columns": ["month", "kpi_id", "value", "target"],
        "sample_values": {
            "kpi_name": ["Yield", "OEE", "RFT", "Cycle Time"]
        },
        "sample_queries": [
            "Monthly KPI data quality",
            "Profile monthly KPI store",
            "Missing KPI values by month",
            "KPI data completeness check"
        ],
        "aliases": ["monthly KPIs", "monthly metrics", "KPI monthly", "KPI data quality"]
    },

    "kpi_store_weekly": {
        "name": "Weekly KPI Store",
        "description": "Pre-computed weekly KPI metrics for more granular trend analysis. "
                      "Should be consistent with monthly aggregations.",
        "file_path": "KPI/kpi_store_weekly.csv",
        "category": "KPI",
        "columns": ["iso_week", "site_id", "kpi_id", "kpi_name", "value", "target", "unit", "trend"],
        "key_columns": ["iso_week", "kpi_id", "value", "target"],
        "sample_values": {
            "kpi_name": ["Yield", "OEE", "RFT", "Cycle Time"]
        },
        "sample_queries": [
            "Weekly KPI data quality",
            "Profile weekly KPI store",
            "Do weekly KPIs aggregate to monthly?",
            "Weekly KPI completeness"
        ],
        "aliases": ["weekly KPIs", "weekly metrics", "KPI weekly"]
    }
}


def get_all_table_descriptions() -> list[dict]:
    """Get all table descriptions for embedding generation."""
    descriptions = []
    for table_id, meta in DATA_TABLE_CATALOGUE.items():
        text = f"{meta['name']}: {meta['description']} "
        text += f"Columns: {', '.join(meta['columns'])}. "
        text += f"Sample questions: {'; '.join(meta['sample_queries'][:5])}. "
        text += f"Also known as: {', '.join(meta['aliases'])}."
        descriptions.append({
            "table_id": table_id,
            "text": text,
            "category": meta["category"]
        })
    return descriptions


def get_table_metadata(table_id: str) -> TableMetadata | None:
    """Get metadata for a specific table."""
    return DATA_TABLE_CATALOGUE.get(table_id)


def get_tables_by_category(category: str) -> list[str]:
    """Get all table IDs in a category."""
    return [
        table_id for table_id, meta in DATA_TABLE_CATALOGUE.items()
        if meta["category"] == category
    ]

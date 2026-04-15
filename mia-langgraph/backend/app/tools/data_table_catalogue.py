"""
Data Table Catalogue for MIA Analyst Agent
Provides semantic search over data tables to load only relevant CSVs.
"""

from typing import TypedDict


class TableMetadata(TypedDict):
    name: str
    description: str
    file_path: str
    category: str  # Analytical, Transactional, Master
    columns: list[str]
    key_columns: list[str]  # Important columns for filtering
    sample_values: dict[str, list[str]]  # Column -> sample values
    sample_queries: list[str]  # Questions this table can answer
    aliases: list[str]  # Alternative names/terms


# Complete catalogue of all data tables with rich metadata for semantic search
DATA_TABLE_CATALOGUE: dict[str, TableMetadata] = {
    # ============ ANALYTICAL DATA ============
    "analytics_batch_status": {
        "name": "Batch Status Analytics",
        "description": "Pre-computed batch analytics with yield, cycle time, wait time, RFT (right first time), "
                      "deviations, alarms, and quality status. Each row is a production batch with performance metrics. "
                      "Use for batch-level KPIs, quality analysis, and production performance questions.",
        "file_path": "Analytical/analytics_batch_status.csv",
        "category": "Analytical",
        "columns": ["batch_id", "order_id", "material_id", "batch_size", "uom", "route", "scheduled_start",
                   "scheduled_end", "cycle_time_hr", "yield_qty", "yield_pct", "status", "deviations_count",
                   "rework_flag", "primary_equipment_id", "actual_start", "actual_end", "steps", "wait_time_min",
                   "active_time_min", "lims_first_pass", "alarm_count", "rft", "month", "iso_week"],
        "key_columns": ["batch_id", "status", "yield_pct", "cycle_time_hr", "wait_time_min", "rft"],
        "sample_values": {
            "status": ["Released", "Quarantined", "Rejected", "In Progress"],
            "rft": ["0", "1"],  # 0=failed first pass, 1=passed first time
            "route": ["Upstream→Downstream→Fill", "Blend→Compress→Coat→Pack"]
        },
        "sample_queries": [
            "How many batches are quarantined?",
            "What is the yield for batch B2025-00001?",
            "Which batches have deviations?",
            "Average cycle time for all batches",
            "Batches with wait time over 2 hours",
            "How many batches are there?",
            "List all rejected batches",
            "Batch performance this month",
            "Which batches failed RFT (right first time)?",
            "Batches with alarms",
            "Why is RFT below target?",
            "Root cause of RFT failures",
            "How can we improve yield?",
            "How can we improve OEE?",
            "OEE improvement analysis",
            "Equipment efficiency analysis",
            "Packaging line performance",
            "Production efficiency",
            "What is causing low yield?",
            "Why are batches failing?"
        ],
        "aliases": ["batch status", "batches", "batch analytics", "batch performance", "production batches",
                   "RFT analysis", "yield analysis", "OEE analysis", "efficiency", "root cause"]
    },

    "analytics_order_status": {
        "name": "Order Status Analytics",
        "description": "Pre-computed order analytics with production orders, quantities, schedule adherence, "
                      "OTIF (on time in full), and delivery performance. Each row is a production order with "
                      "aggregated batch metrics. Contains site_id and plant information for location queries. "
                      "Use for order tracking, schedule adherence, delivery questions, and site/plant queries.",
        "file_path": "Analytical/analytics_order_status.csv",
        "category": "Analytical",
        "columns": ["site_id", "plant", "order_id", "order_type", "material_id", "material_desc", "uom",
                   "qty_ordered", "scheduled_start", "scheduled_end", "priority", "work_center", "status",
                   "batches", "qty_produced", "released", "pct_batches_on_time", "avg_cycle_time_hr",
                   "deviation_count", "qty_in_full", "on_time", "otif", "schedule_adherence_pct"],
        "key_columns": ["order_id", "site_id", "plant", "status", "priority", "on_time", "otif", "schedule_adherence_pct"],
        "sample_values": {
            "status": ["TECO", "REL", "CRTD"],
            "priority": ["High", "Medium", "Low"],
            "plant": ["DUB1"],
            "site_id": ["FCTN-PLANT-01"]
        },
        "sample_queries": [
            "How many orders are there?",
            "Which orders are delayed?",
            "Order schedule adherence",
            "OTIF performance",
            "High priority orders",
            "Orders for material FG-VA01",
            "How many orders missed their scheduled date?",
            "Order status summary",
            "How many sites are there?",
            "How many plants are there?",
            "Number of unique site id",
            "List all sites",
            "Orders by site",
            "Orders by plant"
        ],
        "aliases": ["orders", "order status", "production orders", "order analytics", "order performance",
                   "sites", "plants", "site id", "plant id", "locations", "facilities"]
    },

    # ============ TRANSACTIONAL DATA ============
    "mes_pasx_batches": {
        "name": "MES Batch Records",
        "description": "Raw MES (Manufacturing Execution System) batch records from PAS-X. Contains batch "
                      "execution details, timestamps, and production data. Use for detailed batch tracking.",
        "file_path": "Transactional/mes_pasx_batches.csv",
        "category": "Transactional",
        "columns": ["batch_id", "order_id", "material_id", "batch_size", "uom", "route", "scheduled_start",
                   "scheduled_end", "actual_start", "actual_end", "status", "equipment_id"],
        "key_columns": ["batch_id", "order_id", "status"],
        "sample_values": {
            "status": ["Completed", "In Progress", "Scheduled"]
        },
        "sample_queries": [
            "Batch execution details",
            "When did batch B2025-00001 start?",
            "Which equipment was used for batch?",
            "MES batch records"
        ],
        "aliases": ["MES batches", "PAS-X batches", "batch records", "batch execution"]
    },

    "mes_pasx_batch_steps": {
        "name": "MES Batch Steps",
        "description": "Step-by-step manufacturing process data for each batch. Contains timing for each "
                      "production step (Charge, Mix, Heat, Hold, Cool, Filter, Fill/Pack). Use for lead time "
                      "analysis, wait time between steps, and process bottleneck identification.",
        "file_path": "Transactional/mes_pasx_batch_steps.csv",
        "category": "Transactional",
        "columns": ["batch_id", "step_id", "step_code", "step_name", "sequence", "step_start", "step_end",
                   "duration_min", "wait_before_min", "target_temp_C", "target_pH", "equipment_id"],
        "key_columns": ["batch_id", "step_code", "step_name", "duration_min", "wait_before_min"],
        "sample_values": {
            "step_code": ["CHRG", "MIX", "HEAT", "HOLD", "COOL", "FLT", "FILL"],
            "step_name": ["Charge", "Mix", "Heat", "Hold", "Cool", "Filter", "Fill/Pack"]
        },
        "sample_queries": [
            "What is the wait time between formulation and packaging?",
            "Lead time for batch B2025-00001",
            "How long did the filter step take?",
            "Wait time between steps",
            "Manufacturing process steps",
            "Time between Filter and Fill/Pack",
            "Step duration analysis",
            "Longest step in production"
        ],
        "aliases": ["batch steps", "process steps", "manufacturing steps", "lead time", "step timing"]
    },

    "sap_orders": {
        "name": "SAP Production Orders",
        "description": "SAP ERP production order data. Contains order details, scheduling, material info, "
                      "site_id, plant, and standard parameters. Use for order planning, ERP-level queries, "
                      "and site/plant information.",
        "file_path": "Transactional/sap_orders.csv",
        "category": "Transactional",
        "columns": ["site_id", "plant", "order_id", "order_type", "material_id", "material_desc", "uom",
                   "qty_ordered", "scheduled_start", "scheduled_end", "priority", "work_center",
                   "bom_version", "std_yield_pct", "std_cycle_time_hr", "status"],
        "key_columns": ["order_id", "site_id", "plant", "material_id", "status", "priority"],
        "sample_values": {
            "status": ["TECO", "REL", "CRTD"],
            "plant": ["DUB1"],
            "site_id": ["FCTN-PLANT-01"],
            "order_type": ["PI01"]
        },
        "sample_queries": [
            "SAP orders for this month",
            "Orders by material",
            "Standard cycle time for orders",
            "Plant DUB1 orders",
            "How many plants are there?",
            "Which sites have orders?"
        ],
        "aliases": ["SAP orders", "ERP orders", "production planning", "work orders"]
    },

    "lims_results": {
        "name": "LIMS Test Results",
        "description": "Laboratory Information Management System (LIMS) quality test results. Contains "
                      "sample testing data, pass/fail status, specifications, and turnaround time. "
                      "Use for quality control, test results, and lab performance questions.",
        "file_path": "Transactional/lims_results.csv",
        "category": "Transactional",
        "columns": ["sample_id", "batch_id", "material_id", "test_name", "analyte", "result_value",
                   "unit", "spec_low", "spec_high", "result_status", "sampled_ts", "received_ts",
                   "approved_ts", "analyst_id", "tat_days"],
        "key_columns": ["batch_id", "test_name", "result_status", "tat_days"],
        "sample_values": {
            "test_name": ["Assay", "Impurity A", "pH", "Endotoxin"],
            "result_status": ["PASS", "FAIL"],
            "analyte": ["API", "Imp A", "pH", "EU/mL"]
        },
        "sample_queries": [
            "Test results for batch B2025-00001",
            "Which batches failed quality testing?",
            "Lab turnaround time",
            "Assay results",
            "Failed tests this month",
            "LIMS performance",
            "Quality test pass rate"
        ],
        "aliases": ["LIMS", "lab results", "quality tests", "QC results", "test results", "laboratory"]
    },

    "events_alarms": {
        "name": "Equipment Events and Alarms",
        "description": "Equipment event and alarm data from manufacturing systems. Contains alarms, "
                      "warnings, severity levels, and acknowledgment times. Use for equipment reliability, "
                      "alarm analysis, and maintenance questions.",
        "file_path": "Transactional/events_alarms.csv",
        "category": "Transactional",
        "columns": ["timestamp", "equipment_id", "batch_id", "step_id", "event_type", "code",
                   "severity", "description", "duration_sec", "ack_ts", "cleared_ts"],
        "key_columns": ["equipment_id", "batch_id", "event_type", "severity"],
        "sample_values": {
            "event_type": ["Alarm", "Warning"],
            "severity": ["Low", "Medium", "High"],
            "code": ["LEVEL_HI", "TEMP_LO", "TEMP_HI"]
        },
        "sample_queries": [
            "Alarms for batch B2025-00001",
            "High severity alarms",
            "Equipment alarms today",
            "How many alarms per equipment?",
            "Warning events",
            "Alarm acknowledgment time",
            "Equipment reliability"
        ],
        "aliases": ["alarms", "events", "equipment alarms", "warnings", "equipment events"]
    },

    "inventory_snapshots": {
        "name": "Inventory Snapshots",
        "description": "Weekly inventory snapshot data showing material quantities on hand. "
                      "Use for inventory levels, stock analysis, and material availability questions.",
        "file_path": "Transactional/inventory_snapshots.csv",
        "category": "Transactional",
        "columns": ["date", "material_id", "on_hand_qty", "uom", "lot_count", "days_on_hand", "iso_week"],
        "key_columns": ["material_id", "on_hand_qty", "days_on_hand"],
        "sample_values": {},
        "sample_queries": [
            "Current inventory levels",
            "Materials low on stock",
            "Days on hand for materials",
            "Inventory by week",
            "Stock levels for raw materials"
        ],
        "aliases": ["inventory", "stock", "on hand", "material inventory", "stock levels"]
    },

    "goods_receipts": {
        "name": "Goods Receipts",
        "description": "Incoming material receipts from suppliers. Contains receipt quantities, "
                      "COA (Certificate of Analysis) status, and QC release dates. Use for receiving, "
                      "supplier quality, and material intake questions.",
        "file_path": "Transactional/goods_receipts.csv",
        "category": "Transactional",
        "columns": ["gr_id", "po_id", "material_id", "qty_received", "uom", "receipt_date",
                   "lot_id", "coa_status", "qc_release_ts"],
        "key_columns": ["material_id", "coa_status", "receipt_date"],
        "sample_values": {
            "coa_status": ["Accepted", "Rejected"]
        },
        "sample_queries": [
            "Goods received this month",
            "Rejected COA receipts",
            "Material receipts by supplier",
            "QC release time for receipts"
        ],
        "aliases": ["goods receipt", "GR", "receiving", "material receipts", "incoming materials"]
    },

    "consumption_movements": {
        "name": "Material Consumption",
        "description": "Material consumption/issue movements for production batches. Shows what raw "
                      "materials were issued to which batches. Use for material usage, BOM consumption, "
                      "and traceability questions.",
        "file_path": "Transactional/consumption_movements.csv",
        "category": "Transactional",
        "columns": ["move_id", "batch_id", "material_id", "qty_issued", "uom", "issue_date",
                   "storage_location", "lot_id"],
        "key_columns": ["batch_id", "material_id", "qty_issued"],
        "sample_values": {
            "storage_location": ["COLD", "HAZ", "AMBIENT"]
        },
        "sample_queries": [
            "Materials consumed by batch B2025-00001",
            "Raw material usage",
            "BOM consumption",
            "Material traceability",
            "Which lots were used in production?"
        ],
        "aliases": ["consumption", "material usage", "goods issue", "BOM consumption", "material movements"]
    },

    "procurement_pos": {
        "name": "Procurement Purchase Orders",
        "description": "Purchase order data for raw material procurement. Contains order details, "
                      "pricing, vendor info, and delivery performance. Use for procurement, supplier "
                      "performance, and purchasing questions.",
        "file_path": "Transactional/procurement_pos.csv",
        "category": "Transactional",
        "columns": ["po_id", "vendor_id", "material_id", "qty_ordered", "uom", "order_date",
                   "promised_date", "delivery_date", "status", "price_per_uom", "currency",
                   "month", "on_time"],
        "key_columns": ["vendor_id", "material_id", "status", "on_time"],
        "sample_values": {
            "status": ["Closed", "Open"],
            "on_time": ["0", "1"]
        },
        "sample_queries": [
            "Purchase orders this month",
            "Supplier on-time delivery",
            "PO spend by vendor",
            "Late deliveries",
            "Procurement performance"
        ],
        "aliases": ["PO", "purchase orders", "procurement", "purchasing", "supplier orders"]
    },

    # ============ MASTER DATA ============
    "materials_master": {
        "name": "Materials Master",
        "description": "Master data for all materials (finished goods, raw materials). Contains material "
                      "descriptions, standard batch sizes, routes, and value streams. Use for material "
                      "information and product catalog questions.",
        "file_path": "Master data/materials_master.csv",
        "category": "Master",
        "columns": ["material_id", "description", "uom", "std_batch_size", "value_stream", "route", "type"],
        "key_columns": ["material_id", "description", "value_stream", "type"],
        "sample_values": {
            "type": ["FG", "RM"],  # Finished Goods, Raw Materials
            "value_stream": ["FillFinish", "Downstream", "SolidDose"]
        },
        "sample_queries": [
            "What materials do we have?",
            "Material information for FG-VA01",
            "Standard batch size",
            "Products by value stream",
            "List all finished goods"
        ],
        "aliases": ["materials", "products", "material master", "SKUs", "finished goods", "raw materials"]
    },

    "equipment_master": {
        "name": "Equipment Master",
        "description": "Master data for manufacturing equipment. Contains equipment types, areas, "
                      "lines, and capacities. Use for equipment information and capacity questions.",
        "file_path": "Master data/equipment_master.csv",
        "category": "Master",
        "columns": ["equipment_id", "type", "area", "line", "capacity_L"],
        "key_columns": ["equipment_id", "type", "area", "line"],
        "sample_values": {
            "type": ["Reactor", "Centrifuge", "FilterSkid", "FillerLine", "TabletPress"],
            "area": ["Upstream", "Downstream", "FillFinish", "SolidDose"]
        },
        "sample_queries": [
            "What equipment do we have?",
            "Equipment by area",
            "Reactor capacity",
            "Fill line equipment",
            "Equipment list"
        ],
        "aliases": ["equipment", "machines", "assets", "production equipment", "manufacturing equipment"]
    },

    "vendors_master": {
        "name": "Vendors Master",
        "description": "Master data for suppliers/vendors. Contains vendor names and preferred status. "
                      "Use for supplier information questions.",
        "file_path": "Master data/vendors_master.csv",
        "category": "Master",
        "columns": ["vendor_id", "name", "preferred"],
        "key_columns": ["vendor_id", "name", "preferred"],
        "sample_values": {
            "preferred": ["True", "False"]
        },
        "sample_queries": [
            "Who are our suppliers?",
            "Preferred vendors",
            "Vendor list",
            "Supplier information"
        ],
        "aliases": ["vendors", "suppliers", "supplier master", "vendor list"]
    },

    # ============ KPI DATA ============
    "kpi_store_weekly": {
        "name": "Weekly KPI Store",
        "description": "Pre-computed weekly KPI metrics. Contains yield, RFT, OEE, cycle time, and other "
                      "KPIs aggregated by week. Use for weekly performance trending.",
        "file_path": "KPI/kpi_store_weekly.csv",
        "category": "KPI",
        "columns": ["iso_week", "kpi_id", "kpi_name", "value", "target", "unit"],
        "key_columns": ["iso_week", "kpi_id", "kpi_name", "value"],
        "sample_values": {
            "kpi_name": ["Batch Yield", "RFT", "OEE Packaging", "Cycle Time"]
        },
        "sample_queries": [
            "Weekly yield trend",
            "KPI performance by week",
            "Weekly metrics"
        ],
        "aliases": ["weekly KPIs", "weekly metrics", "KPI weekly"]
    },

    "kpi_store_monthly": {
        "name": "Monthly KPI Store",
        "description": "Pre-computed monthly KPI metrics. Contains yield, RFT, OEE, cycle time, and other "
                      "KPIs aggregated by month. Use for monthly performance reporting.",
        "file_path": "KPI/kpi_store_monthly.csv",
        "category": "KPI",
        "columns": ["month", "kpi_id", "kpi_name", "value", "target", "unit"],
        "key_columns": ["month", "kpi_id", "kpi_name", "value"],
        "sample_values": {
            "kpi_name": ["Batch Yield", "RFT", "OEE Packaging", "Cycle Time"]
        },
        "sample_queries": [
            "Monthly yield trend",
            "KPI performance by month",
            "Monthly metrics"
        ],
        "aliases": ["monthly KPIs", "monthly metrics", "KPI monthly"]
    }
}


def get_all_table_descriptions() -> list[dict]:
    """
    Get all table descriptions for embedding generation.
    Returns list of {table_id, text} for Titan embedding.
    """
    descriptions = []
    for table_id, meta in DATA_TABLE_CATALOGUE.items():
        # Combine description, columns, and sample queries into rich text
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
    """Get all table IDs in a category (Analytical, Transactional, Master, KPI)."""
    return [
        table_id for table_id, meta in DATA_TABLE_CATALOGUE.items()
        if meta["category"] == category
    ]

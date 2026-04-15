"""
Simulated Collibra DGC Connector for Data Strategy Agent
=========================================================
Provides simulated integration with Collibra Data Governance Center for demo
purposes. Returns realistic Collibra metadata, data quality rules, and business
glossary terms mapped to the 14 operational manufacturing tables.

This module does NOT make real API calls. All responses are pre-built to
simulate what a production Collibra integration would return.
"""

from typing import Any
from datetime import datetime, timezone


# ---------------------------------------------------------------------------
# Internal connection state (simulated)
# ---------------------------------------------------------------------------
_collibra_connection_state: dict[str, Any] = {
    "connected": False,
    "url": None,
    "community": None,
    "token": None,
    "connected_at": None,
    "api_version": "2.0",
    "dgc_version": "2024.05",
}


# ---------------------------------------------------------------------------
# 1. connect_collibra  -- simulated authentication
# ---------------------------------------------------------------------------
def connect_collibra(
    url: str = "https://astrazeneca.collibra.com",
    token: str = "sim-token-az-dsa-2024",
    community: str = "Manufacturing Data Governance",
) -> dict[str, Any]:
    """Simulate connecting to Collibra DGC.

    In production this would perform OAuth2 / API-key authentication against
    the Collibra REST API.  Here it simply stores the parameters and returns
    a success payload.

    Args:
        url: Collibra instance URL.
        token: API bearer token (simulated).
        community: Collibra community to scope the connection to.

    Returns:
        dict with connection status, version info, and available domains.
    """
    _collibra_connection_state.update(
        {
            "connected": True,
            "url": url,
            "community": community,
            "token": token,
            "connected_at": datetime.now(timezone.utc).isoformat(),
        }
    )

    return {
        "status": "connected",
        "url": url,
        "community": community,
        "dgc_version": _collibra_connection_state["dgc_version"],
        "api_version": _collibra_connection_state["api_version"],
        "available_domains": [
            "Analytical Data",
            "Transactional Data",
            "Master Data",
        ],
        "message": (
            f"Successfully connected to Collibra DGC at {url} "
            f"(community: {community})"
        ),
    }


# ---------------------------------------------------------------------------
# 2. get_collibra_catalog  -- 14 tables enriched with Collibra metadata
# ---------------------------------------------------------------------------
def get_collibra_catalog() -> list[dict[str, Any]]:
    """Return the 14 operational tables with Collibra governance metadata.

    Each entry contains the original table information *plus* Collibra-specific
    fields:
        - collibra_asset_id   : UUID-style asset identifier in Collibra
        - business_name        : Human-readable name assigned by the steward
        - data_steward         : Name of the accountable data steward
        - community            : Collibra community the asset belongs to
        - domain               : Collibra domain within the community
        - classification       : Data classification (Confidential / Internal / Public)
        - quality_score        : Latest DQ score surfaced in Collibra (0-100)
        - last_profiled        : ISO timestamp of last profiling run
    """
    return [
        # ==================== Analytical ====================
        {
            "table_name": "analytics_batch_status",
            "category": "Analytical",
            "collibra_asset_id": "c9a1e0b2-4f3d-4a8c-b1e7-1a2b3c4d5e01",
            "business_name": "Batch Performance Analytics",
            "data_steward": "Dr. Sarah Mitchell",
            "community": "Manufacturing Data Governance",
            "domain": "Analytical Data",
            "classification": "Confidential",
            "quality_score": 94.2,
            "last_profiled": "2025-01-15T08:30:00Z",
            "description": (
                "Pre-computed batch analytics with yield, cycle time, wait "
                "time, RFT, deviations, and quality status."
            ),
        },
        {
            "table_name": "analytics_order_status",
            "category": "Analytical",
            "collibra_asset_id": "c9a1e0b2-4f3d-4a8c-b1e7-1a2b3c4d5e02",
            "business_name": "Production Order Analytics",
            "data_steward": "Dr. Sarah Mitchell",
            "community": "Manufacturing Data Governance",
            "domain": "Analytical Data",
            "classification": "Confidential",
            "quality_score": 91.8,
            "last_profiled": "2025-01-15T08:32:00Z",
            "description": (
                "Production order analytics with schedule adherence, OTIF, "
                "and delivery metrics across sites."
            ),
        },
        # ==================== Transactional ====================
        {
            "table_name": "lims_results",
            "category": "Transactional",
            "collibra_asset_id": "c9a1e0b2-4f3d-4a8c-b1e7-1a2b3c4d5e03",
            "business_name": "Laboratory Test Results (LIMS)",
            "data_steward": "Dr. James Thornton",
            "community": "Manufacturing Data Governance",
            "domain": "Transactional Data",
            "classification": "Confidential",
            "quality_score": 96.5,
            "last_profiled": "2025-01-15T08:35:00Z",
            "description": (
                "Laboratory test results with sample data, spec limits, "
                "pass/fail status, and turnaround times."
            ),
        },
        {
            "table_name": "mes_pasx_batches",
            "category": "Transactional",
            "collibra_asset_id": "c9a1e0b2-4f3d-4a8c-b1e7-1a2b3c4d5e04",
            "business_name": "MES Batch Execution Records (PAS-X)",
            "data_steward": "Raj Patel",
            "community": "Manufacturing Data Governance",
            "domain": "Transactional Data",
            "classification": "Confidential",
            "quality_score": 93.1,
            "last_profiled": "2025-01-15T08:37:00Z",
            "description": (
                "Raw MES batch execution records from Werum PAS-X. Source of "
                "truth for batch lifecycle data."
            ),
        },
        {
            "table_name": "mes_pasx_batch_steps",
            "category": "Transactional",
            "collibra_asset_id": "c9a1e0b2-4f3d-4a8c-b1e7-1a2b3c4d5e05",
            "business_name": "MES Batch Process Steps",
            "data_steward": "Raj Patel",
            "community": "Manufacturing Data Governance",
            "domain": "Transactional Data",
            "classification": "Confidential",
            "quality_score": 91.4,
            "last_profiled": "2025-01-15T08:38:00Z",
            "description": (
                "Step-level manufacturing process data for each batch with "
                "timing, temperature, and pH targets."
            ),
        },
        {
            "table_name": "sap_orders",
            "category": "Transactional",
            "collibra_asset_id": "c9a1e0b2-4f3d-4a8c-b1e7-1a2b3c4d5e06",
            "business_name": "SAP Production Orders",
            "data_steward": "Elena Vasquez",
            "community": "Manufacturing Data Governance",
            "domain": "Transactional Data",
            "classification": "Internal",
            "quality_score": 89.7,
            "last_profiled": "2025-01-15T08:40:00Z",
            "description": (
                "SAP ERP production order data including scheduling, priority, "
                "and BOM version information."
            ),
        },
        {
            "table_name": "events_alarms",
            "category": "Transactional",
            "collibra_asset_id": "c9a1e0b2-4f3d-4a8c-b1e7-1a2b3c4d5e07",
            "business_name": "Equipment Events and Alarms",
            "data_steward": "Raj Patel",
            "community": "Manufacturing Data Governance",
            "domain": "Transactional Data",
            "classification": "Internal",
            "quality_score": 87.3,
            "last_profiled": "2025-01-15T08:42:00Z",
            "description": (
                "Equipment alarm and event data used for reliability and "
                "predictive maintenance analysis."
            ),
        },
        {
            "table_name": "goods_receipts",
            "category": "Transactional",
            "collibra_asset_id": "c9a1e0b2-4f3d-4a8c-b1e7-1a2b3c4d5e08",
            "business_name": "Goods Receipt Records",
            "data_steward": "Elena Vasquez",
            "community": "Manufacturing Data Governance",
            "domain": "Transactional Data",
            "classification": "Internal",
            "quality_score": 90.6,
            "last_profiled": "2025-01-15T08:44:00Z",
            "description": (
                "Incoming material receipts with Certificate of Analysis (CoA) "
                "status and QC release dates."
            ),
        },
        {
            "table_name": "inventory_snapshots",
            "category": "Transactional",
            "collibra_asset_id": "c9a1e0b2-4f3d-4a8c-b1e7-1a2b3c4d5e09",
            "business_name": "Inventory Position Snapshots",
            "data_steward": "Elena Vasquez",
            "community": "Manufacturing Data Governance",
            "domain": "Transactional Data",
            "classification": "Internal",
            "quality_score": 92.0,
            "last_profiled": "2025-01-15T08:45:00Z",
            "description": (
                "Weekly inventory snapshots with material quantities on hand, "
                "lot counts, and days-on-hand metrics."
            ),
        },
        {
            "table_name": "consumption_movements",
            "category": "Transactional",
            "collibra_asset_id": "c9a1e0b2-4f3d-4a8c-b1e7-1a2b3c4d5e10",
            "business_name": "Material Consumption Movements",
            "data_steward": "Elena Vasquez",
            "community": "Manufacturing Data Governance",
            "domain": "Transactional Data",
            "classification": "Internal",
            "quality_score": 88.9,
            "last_profiled": "2025-01-15T08:46:00Z",
            "description": (
                "Material consumption/issuance movements linked to production "
                "batches with lot traceability."
            ),
        },
        {
            "table_name": "procurement_pos",
            "category": "Transactional",
            "collibra_asset_id": "c9a1e0b2-4f3d-4a8c-b1e7-1a2b3c4d5e11",
            "business_name": "Procurement Purchase Orders",
            "data_steward": "Elena Vasquez",
            "community": "Manufacturing Data Governance",
            "domain": "Transactional Data",
            "classification": "Confidential",
            "quality_score": 90.2,
            "last_profiled": "2025-01-15T08:48:00Z",
            "description": (
                "Purchase order data for raw material procurement with vendor, "
                "pricing, and delivery tracking."
            ),
        },
        # ==================== Master ====================
        {
            "table_name": "equipment_master",
            "category": "Master",
            "collibra_asset_id": "c9a1e0b2-4f3d-4a8c-b1e7-1a2b3c4d5e12",
            "business_name": "Equipment Master Data",
            "data_steward": "Raj Patel",
            "community": "Manufacturing Data Governance",
            "domain": "Master Data",
            "classification": "Internal",
            "quality_score": 98.5,
            "last_profiled": "2025-01-15T08:50:00Z",
            "description": (
                "Master data for manufacturing equipment including type, area, "
                "line, and capacity attributes."
            ),
        },
        {
            "table_name": "materials_master",
            "category": "Master",
            "collibra_asset_id": "c9a1e0b2-4f3d-4a8c-b1e7-1a2b3c4d5e13",
            "business_name": "Materials Master Data",
            "data_steward": "Dr. James Thornton",
            "community": "Manufacturing Data Governance",
            "domain": "Master Data",
            "classification": "Internal",
            "quality_score": 97.8,
            "last_profiled": "2025-01-15T08:51:00Z",
            "description": (
                "Master data for all materials (finished goods and raw "
                "materials) with batch size, route, and lead time."
            ),
        },
        {
            "table_name": "vendors_master",
            "category": "Master",
            "collibra_asset_id": "c9a1e0b2-4f3d-4a8c-b1e7-1a2b3c4d5e14",
            "business_name": "Vendor / Supplier Master Data",
            "data_steward": "Elena Vasquez",
            "community": "Manufacturing Data Governance",
            "domain": "Master Data",
            "classification": "Confidential",
            "quality_score": 95.3,
            "last_profiled": "2025-01-15T08:52:00Z",
            "description": (
                "Master data for approved suppliers and vendors with "
                "preferred-vendor flag."
            ),
        },
    ]


# ---------------------------------------------------------------------------
# 3. get_collibra_rules  -- ~15 DQ rules imported from Collibra DGC
# ---------------------------------------------------------------------------
def get_collibra_rules() -> list[dict[str, Any]]:
    """Return data quality rules that simulate import from Collibra DGC.

    Each rule contains:
        - rule_id              : Internal sequential identifier
        - rule_name            : Short human-readable name
        - rule_type            : Category (null_check | range_check |
                                 fk_integrity | format_check | freshness |
                                 cross_system)
        - description          : Detailed description of the rule
        - target_table         : Table the rule applies to
        - target_column        : Column(s) the rule validates
        - sql_check            : SQL expression that can run against DuckDB
        - severity             : critical | high | medium | low
        - collibra_rule_id     : UUID-style rule ID in Collibra
    """
    return [
        # ===================== NULL CHECKS =====================
        {
            "rule_id": "DQ-001",
            "rule_name": "Batch ID Not Null",
            "rule_type": "null_check",
            "description": (
                "Every batch record must have a non-null batch_id. A missing "
                "batch_id breaks traceability across MES, LIMS, and analytics."
            ),
            "target_table": "mes_pasx_batches",
            "target_column": "batch_id",
            "sql_check": (
                "SELECT COUNT(*) AS violations "
                "FROM mes_pasx_batches "
                "WHERE batch_id IS NULL"
            ),
            "severity": "critical",
            "collibra_rule_id": "cr-dq-rule-0001-a1b2-c3d4e5f60001",
        },
        {
            "rule_id": "DQ-002",
            "rule_name": "Product Code Not Null",
            "rule_type": "null_check",
            "description": (
                "Every production order must reference a valid material_id "
                "(product code). Null values prevent order-to-material "
                "traceability."
            ),
            "target_table": "sap_orders",
            "target_column": "material_id",
            "sql_check": (
                "SELECT COUNT(*) AS violations "
                "FROM sap_orders "
                "WHERE material_id IS NULL"
            ),
            "severity": "critical",
            "collibra_rule_id": "cr-dq-rule-0002-a1b2-c3d4e5f60002",
        },
        {
            "rule_id": "DQ-003",
            "rule_name": "LIMS Result Value Not Null",
            "rule_type": "null_check",
            "description": (
                "Every LIMS test record must have a result_value. Null results "
                "indicate incomplete lab workflows and block batch release."
            ),
            "target_table": "lims_results",
            "target_column": "result_value",
            "sql_check": (
                "SELECT COUNT(*) AS violations "
                "FROM lims_results "
                "WHERE result_value IS NULL"
            ),
            "severity": "critical",
            "collibra_rule_id": "cr-dq-rule-0003-a1b2-c3d4e5f60003",
        },
        # ===================== RANGE CHECKS =====================
        {
            "rule_id": "DQ-004",
            "rule_name": "Yield Percentage Valid Range",
            "rule_type": "range_check",
            "description": (
                "Batch yield_pct must be between 0 and 110%. Values outside "
                "this range indicate data entry errors or calculation bugs. "
                "Yields slightly above 100% are acceptable in pharma due to "
                "measurement variability."
            ),
            "target_table": "analytics_batch_status",
            "target_column": "yield_pct",
            "sql_check": (
                "SELECT COUNT(*) AS violations "
                "FROM analytics_batch_status "
                "WHERE yield_pct < 0 OR yield_pct > 110"
            ),
            "severity": "high",
            "collibra_rule_id": "cr-dq-rule-0004-a1b2-c3d4e5f60004",
        },
        {
            "rule_id": "DQ-005",
            "rule_name": "Step Temperature Valid Range",
            "rule_type": "range_check",
            "description": (
                "target_temp_C in batch steps must be between 0 and 100 "
                "degrees Celsius. Values outside this range for standard "
                "pharma processing indicate sensor errors or incorrect entry."
            ),
            "target_table": "mes_pasx_batch_steps",
            "target_column": "target_temp_C",
            "sql_check": (
                "SELECT COUNT(*) AS violations "
                "FROM mes_pasx_batch_steps "
                "WHERE target_temp_C IS NOT NULL "
                "AND (target_temp_C < 0 OR target_temp_C > 100)"
            ),
            "severity": "high",
            "collibra_rule_id": "cr-dq-rule-0005-a1b2-c3d4e5f60005",
        },
        {
            "rule_id": "DQ-006",
            "rule_name": "Cycle Time Positive Value",
            "rule_type": "range_check",
            "description": (
                "Cycle time must be positive and not exceed 720 hours (30 "
                "days). Negative or extreme values indicate timestamp issues."
            ),
            "target_table": "analytics_batch_status",
            "target_column": "cycle_time_hr",
            "sql_check": (
                "SELECT COUNT(*) AS violations "
                "FROM analytics_batch_status "
                "WHERE cycle_time_hr IS NOT NULL "
                "AND (cycle_time_hr <= 0 OR cycle_time_hr > 720)"
            ),
            "severity": "medium",
            "collibra_rule_id": "cr-dq-rule-0006-a1b2-c3d4e5f60006",
        },
        # ===================== FK INTEGRITY =====================
        {
            "rule_id": "DQ-007",
            "rule_name": "Batch Equipment FK Integrity",
            "rule_type": "fk_integrity",
            "description": (
                "Every primary_equipment_id in batch records must exist in "
                "the equipment_master table. Orphan references indicate "
                "master data gaps or decommissioned equipment not cleaned up."
            ),
            "target_table": "mes_pasx_batches",
            "target_column": "primary_equipment_id",
            "sql_check": (
                "SELECT COUNT(*) AS violations "
                "FROM mes_pasx_batches b "
                "LEFT JOIN equipment_master e "
                "  ON b.primary_equipment_id = e.equipment_id "
                "WHERE b.primary_equipment_id IS NOT NULL "
                "AND e.equipment_id IS NULL"
            ),
            "severity": "high",
            "collibra_rule_id": "cr-dq-rule-0007-a1b2-c3d4e5f60007",
        },
        {
            "rule_id": "DQ-008",
            "rule_name": "Consumption Material FK Integrity",
            "rule_type": "fk_integrity",
            "description": (
                "Every material_id in consumption_movements must exist in "
                "the materials_master table. Missing master records break "
                "material traceability and costing."
            ),
            "target_table": "consumption_movements",
            "target_column": "material_id",
            "sql_check": (
                "SELECT COUNT(*) AS violations "
                "FROM consumption_movements c "
                "LEFT JOIN materials_master m "
                "  ON c.material_id = m.material_id "
                "WHERE c.material_id IS NOT NULL "
                "AND m.material_id IS NULL"
            ),
            "severity": "high",
            "collibra_rule_id": "cr-dq-rule-0008-a1b2-c3d4e5f60008",
        },
        {
            "rule_id": "DQ-009",
            "rule_name": "PO Vendor FK Integrity",
            "rule_type": "fk_integrity",
            "description": (
                "Every vendor_id in procurement purchase orders must exist in "
                "the vendors_master table. Orphan vendor IDs indicate "
                "unapproved or retired suppliers."
            ),
            "target_table": "procurement_pos",
            "target_column": "vendor_id",
            "sql_check": (
                "SELECT COUNT(*) AS violations "
                "FROM procurement_pos p "
                "LEFT JOIN vendors_master v "
                "  ON p.vendor_id = v.vendor_id "
                "WHERE p.vendor_id IS NOT NULL "
                "AND v.vendor_id IS NULL"
            ),
            "severity": "high",
            "collibra_rule_id": "cr-dq-rule-0009-a1b2-c3d4e5f60009",
        },
        # ===================== FORMAT CHECKS =====================
        {
            "rule_id": "DQ-010",
            "rule_name": "Batch ID Format Check",
            "rule_type": "format_check",
            "description": (
                "Batch IDs must follow the standard pattern starting with "
                "'B-' (e.g. B-2024-0001). Non-conforming IDs indicate "
                "manual data entry bypassing MES controls."
            ),
            "target_table": "mes_pasx_batches",
            "target_column": "batch_id",
            "sql_check": (
                "SELECT COUNT(*) AS violations "
                "FROM mes_pasx_batches "
                "WHERE batch_id IS NOT NULL "
                "AND batch_id NOT LIKE 'B-%'"
            ),
            "severity": "medium",
            "collibra_rule_id": "cr-dq-rule-0010-a1b2-c3d4e5f60010",
        },
        {
            "rule_id": "DQ-011",
            "rule_name": "Sample ID Format Check",
            "rule_type": "format_check",
            "description": (
                "LIMS sample IDs must follow the standard pattern starting "
                "with 'S-' (e.g. S-0001). Non-conforming IDs indicate "
                "samples created outside the standard LIMS workflow."
            ),
            "target_table": "lims_results",
            "target_column": "sample_id",
            "sql_check": (
                "SELECT COUNT(*) AS violations "
                "FROM lims_results "
                "WHERE sample_id IS NOT NULL "
                "AND sample_id NOT LIKE 'S-%'"
            ),
            "severity": "medium",
            "collibra_rule_id": "cr-dq-rule-0011-a1b2-c3d4e5f60011",
        },
        {
            "rule_id": "DQ-012",
            "rule_name": "Order ID Format Check",
            "rule_type": "format_check",
            "description": (
                "SAP production order IDs must follow the standard pattern "
                "starting with 'ORD-'. Non-conforming IDs suggest data "
                "migration artifacts or manual corrections."
            ),
            "target_table": "sap_orders",
            "target_column": "order_id",
            "sql_check": (
                "SELECT COUNT(*) AS violations "
                "FROM sap_orders "
                "WHERE order_id IS NOT NULL "
                "AND order_id NOT LIKE 'ORD-%'"
            ),
            "severity": "low",
            "collibra_rule_id": "cr-dq-rule-0012-a1b2-c3d4e5f60012",
        },
        # ===================== FRESHNESS =====================
        {
            "rule_id": "DQ-013",
            "rule_name": "Batch Data Freshness (24h)",
            "rule_type": "freshness",
            "description": (
                "The analytics_batch_status table must contain records updated "
                "within the last 24 hours. Stale batch data can lead to "
                "incorrect release decisions and delayed shipments."
            ),
            "target_table": "analytics_batch_status",
            "target_column": "actual_end",
            "sql_check": (
                "SELECT CASE "
                "  WHEN MAX(CAST(actual_end AS TIMESTAMP)) "
                "       < CURRENT_TIMESTAMP - INTERVAL '24' HOUR "
                "  THEN 1 ELSE 0 "
                "END AS violations "
                "FROM analytics_batch_status "
                "WHERE actual_end IS NOT NULL"
            ),
            "severity": "high",
            "collibra_rule_id": "cr-dq-rule-0013-a1b2-c3d4e5f60013",
        },
        {
            "rule_id": "DQ-014",
            "rule_name": "LIMS Results Freshness (24h)",
            "rule_type": "freshness",
            "description": (
                "The lims_results table must contain test results approved "
                "within the last 24 hours. Stale LIMS data delays batch "
                "disposition and quality review."
            ),
            "target_table": "lims_results",
            "target_column": "approved_ts",
            "sql_check": (
                "SELECT CASE "
                "  WHEN MAX(CAST(approved_ts AS TIMESTAMP)) "
                "       < CURRENT_TIMESTAMP - INTERVAL '24' HOUR "
                "  THEN 1 ELSE 0 "
                "END AS violations "
                "FROM lims_results "
                "WHERE approved_ts IS NOT NULL"
            ),
            "severity": "high",
            "collibra_rule_id": "cr-dq-rule-0014-a1b2-c3d4e5f60014",
        },
        # ===================== CROSS-SYSTEM =====================
        {
            "rule_id": "DQ-015",
            "rule_name": "MES-Analytics Batch Status Consistency",
            "rule_type": "cross_system",
            "description": (
                "Batch status in MES (mes_pasx_batches) must be consistent "
                "with the derived status in analytics_batch_status for all "
                "matching batch_ids. Mismatches indicate ETL failures or "
                "timing gaps between source and analytics layers."
            ),
            "target_table": "mes_pasx_batches",
            "target_column": "status",
            "sql_check": (
                "SELECT COUNT(*) AS violations "
                "FROM mes_pasx_batches m "
                "JOIN analytics_batch_status a "
                "  ON m.batch_id = a.batch_id "
                "WHERE m.status != a.status"
            ),
            "severity": "critical",
            "collibra_rule_id": "cr-dq-rule-0015-a1b2-c3d4e5f60015",
        },
    ]


# ---------------------------------------------------------------------------
# 4. get_collibra_glossary  -- business term definitions
# ---------------------------------------------------------------------------
def get_collibra_glossary() -> list[dict[str, Any]]:
    """Return business glossary terms from the Collibra governance catalogue.

    Each entry contains:
        - term          : Canonical term name
        - abbreviation  : Abbreviation / acronym (if applicable)
        - definition    : Full business definition
        - domain        : Governance domain
        - steward       : Accountable steward
        - related_terms : List of related glossary terms
        - collibra_id   : UUID-style Collibra glossary asset ID
    """
    return [
        {
            "term": "Batch",
            "abbreviation": None,
            "definition": (
                "A specific quantity of a drug or material produced during a "
                "single manufacturing cycle. Each batch is assigned a unique "
                "batch_id and must be fully traceable from raw materials "
                "through to finished product release."
            ),
            "domain": "Manufacturing Operations",
            "steward": "Dr. Sarah Mitchell",
            "related_terms": ["Lot", "Batch Record", "Batch Release"],
            "collibra_id": "cr-glossary-term-0001",
        },
        {
            "term": "Lot",
            "abbreviation": None,
            "definition": (
                "A defined quantity of raw material, packaging component, or "
                "finished product that is uniform in character and quality "
                "within specified limits, produced according to a single "
                "manufacturing order. In context of incoming materials, lot "
                "refers to the supplier's batch."
            ),
            "domain": "Manufacturing Operations",
            "steward": "Dr. Sarah Mitchell",
            "related_terms": ["Batch", "Lot Traceability", "Lot Genealogy"],
            "collibra_id": "cr-glossary-term-0002",
        },
        {
            "term": "Yield",
            "abbreviation": None,
            "definition": (
                "The ratio of actual output quantity to the theoretical "
                "(expected) output quantity for a batch, expressed as a "
                "percentage. Yield = (actual qty / theoretical qty) * 100. "
                "Yields above 100% can occur due to measurement variability; "
                "values up to 110% are considered acceptable."
            ),
            "domain": "Manufacturing Operations",
            "steward": "Dr. Sarah Mitchell",
            "related_terms": ["Batch", "RFT", "OEE"],
            "collibra_id": "cr-glossary-term-0003",
        },
        {
            "term": "Out of Specification",
            "abbreviation": "OOS",
            "definition": (
                "A test result that falls outside the pre-defined "
                "specification limits (spec_low, spec_high) established "
                "during product development and registered with regulatory "
                "authorities. OOS results trigger mandatory investigations "
                "per GxP requirements and may lead to batch rejection."
            ),
            "domain": "Quality Assurance",
            "steward": "Dr. James Thornton",
            "related_terms": ["LIMS", "Deviation", "Batch Release"],
            "collibra_id": "cr-glossary-term-0004",
        },
        {
            "term": "Deviation",
            "abbreviation": None,
            "definition": (
                "A departure from an approved instruction or established "
                "standard during manufacturing, testing, or distribution. "
                "Deviations must be documented, investigated, and resolved "
                "per the site quality management system. The deviations_count "
                "field tracks the number of deviations raised per batch."
            ),
            "domain": "Quality Assurance",
            "steward": "Dr. James Thornton",
            "related_terms": ["CAPA", "OOS", "GxP"],
            "collibra_id": "cr-glossary-term-0005",
        },
        {
            "term": "Right First Time",
            "abbreviation": "RFT",
            "definition": (
                "A manufacturing performance metric indicating whether a "
                "batch was completed successfully on the first attempt "
                "without rework, reprocessing, or rejection. RFT = 1 means "
                "the batch passed all quality checks on first pass; RFT = 0 "
                "means intervention was required."
            ),
            "domain": "Manufacturing Operations",
            "steward": "Dr. Sarah Mitchell",
            "related_terms": ["Yield", "OEE", "Batch"],
            "collibra_id": "cr-glossary-term-0006",
        },
        {
            "term": "Laboratory Information Management System",
            "abbreviation": "LIMS",
            "definition": (
                "An information management system that supports laboratory "
                "operations including sample management, test execution, "
                "result recording, and approval workflows. At AstraZeneca, "
                "LIMS data feeds into batch release decisions and is stored "
                "in the lims_results table."
            ),
            "domain": "Quality Assurance",
            "steward": "Dr. James Thornton",
            "related_terms": ["OOS", "TAT", "CoA"],
            "collibra_id": "cr-glossary-term-0007",
        },
        {
            "term": "Manufacturing Execution System",
            "abbreviation": "MES",
            "definition": (
                "A computerised system used to track and document the "
                "transformation of raw materials into finished products on "
                "the manufacturing floor. AstraZeneca uses Werum PAS-X as "
                "its MES platform. Data is captured in mes_pasx_batches and "
                "mes_pasx_batch_steps tables."
            ),
            "domain": "Manufacturing Operations",
            "steward": "Raj Patel",
            "related_terms": ["Batch", "Batch Steps", "PAS-X"],
            "collibra_id": "cr-glossary-term-0008",
        },
        {
            "term": "Good Practice",
            "abbreviation": "GxP",
            "definition": (
                "An umbrella term for quality guidelines and regulations "
                "including GMP (Good Manufacturing Practice), GLP (Good "
                "Laboratory Practice), and GDP (Good Distribution Practice). "
                "GxP compliance requires complete data integrity, "
                "traceability, and audit trails across all manufacturing "
                "and quality systems."
            ),
            "domain": "Regulatory Compliance",
            "steward": "Dr. James Thornton",
            "related_terms": ["Deviation", "ALCOA+", "Data Integrity"],
            "collibra_id": "cr-glossary-term-0009",
        },
        {
            "term": "Certificate of Analysis",
            "abbreviation": "CoA",
            "definition": (
                "A document issued by a supplier or internal quality lab "
                "certifying that a specific lot of material meets its "
                "predefined quality specifications. CoA status is tracked "
                "in the goods_receipts table (coa_status field) and is "
                "required before material can be used in production."
            ),
            "domain": "Quality Assurance",
            "steward": "Dr. James Thornton",
            "related_terms": ["Goods Receipt", "LIMS", "Lot"],
            "collibra_id": "cr-glossary-term-0010",
        },
        {
            "term": "Turnaround Time",
            "abbreviation": "TAT",
            "definition": (
                "The elapsed time from sample receipt in the laboratory to "
                "final result approval, measured in days. TAT is a critical "
                "KPI for lab efficiency -- long TATs delay batch release and "
                "increase inventory holding costs. Tracked in lims_results "
                "as tat_days."
            ),
            "domain": "Quality Assurance",
            "steward": "Dr. James Thornton",
            "related_terms": ["LIMS", "Batch Release", "Lead Time"],
            "collibra_id": "cr-glossary-term-0011",
        },
    ]

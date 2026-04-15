"""
Data Catalogue for DSA - Data Quality Lifecycle Agent
Defines data quality metrics computed against real operational manufacturing data.
"""

from typing import Any
from langchain_core.tools import tool


# Data Quality KPI Catalogue - metrics computed on-the-fly from operational data
KPI_CATALOGUE = {
    # ============ COMPLETENESS METRICS ============
    "batch_data_completeness": {
        "name": "Batch Data Completeness",
        "description": "Percentage of batch records with all critical fields populated including yield, cycle time, status, and equipment ID. Measures how complete our batch data is.",
        "unit": "%",
        "target": 99,
        "table": "OPERATIONAL_DATA",
        "aliases": ["batch completeness", "batch data quality", "missing batch data", "null values in batches"],
        "sample_queries": [
            "How complete is our batch data?",
            "What percentage of batch fields are populated?",
            "Are there missing values in batch records?",
            "Batch data completeness score"
        ]
    },
    "lims_data_completeness": {
        "name": "LIMS Data Completeness",
        "description": "Percentage of LIMS test result records with all required fields populated including result values, spec limits, and timestamps.",
        "unit": "%",
        "target": 99.5,
        "table": "OPERATIONAL_DATA",
        "aliases": ["LIMS completeness", "lab data completeness", "missing LIMS data", "test result completeness"],
        "sample_queries": [
            "How complete is our LIMS data?",
            "Are there missing lab results?",
            "LIMS data quality score",
            "Missing values in test results"
        ]
    },
    "order_data_completeness": {
        "name": "Order Data Completeness",
        "description": "Percentage of production order records with all required fields populated including quantities, schedules, and material information.",
        "unit": "%",
        "target": 99,
        "table": "OPERATIONAL_DATA",
        "aliases": ["order completeness", "order data quality", "missing order data", "SAP order completeness"],
        "sample_queries": [
            "How complete is our order data?",
            "Missing fields in production orders",
            "Order data completeness percentage",
            "SAP data quality"
        ]
    },
    "master_data_completeness": {
        "name": "Master Data Completeness",
        "description": "Percentage of master data records (materials, equipment, vendors) with all required fields populated.",
        "unit": "%",
        "target": 100,
        "table": "OPERATIONAL_DATA",
        "aliases": ["master data completeness", "MDM completeness", "missing master data"],
        "sample_queries": [
            "How complete is our master data?",
            "Missing values in material master",
            "Master data completeness score",
            "Equipment master data quality"
        ]
    },

    # ============ ACCURACY METRICS ============
    "yield_data_accuracy": {
        "name": "Yield Data Accuracy",
        "description": "Percentage of batch yield values that fall within valid range (0-110%) indicating accurate recording. Values outside range suggest data entry errors.",
        "unit": "%",
        "target": 100,
        "table": "OPERATIONAL_DATA",
        "aliases": ["yield accuracy", "yield data quality", "invalid yields", "yield outliers"],
        "sample_queries": [
            "How accurate is our yield data?",
            "Are there invalid yield values?",
            "Yield data accuracy score",
            "Batches with impossible yield values"
        ]
    },
    "equipment_reference_accuracy": {
        "name": "Equipment Reference Accuracy",
        "description": "Percentage of equipment IDs in batch records that match valid entries in the equipment master. Orphan references indicate data integrity issues.",
        "unit": "%",
        "target": 100,
        "table": "OPERATIONAL_DATA",
        "aliases": ["equipment accuracy", "equipment reference integrity", "orphan equipment IDs", "equipment master match"],
        "sample_queries": [
            "Do all equipment references match the master?",
            "Equipment reference integrity check",
            "Orphan equipment IDs in batch data",
            "Equipment data accuracy"
        ]
    },
    "material_reference_accuracy": {
        "name": "Material Reference Accuracy",
        "description": "Percentage of material IDs in transactional records that match valid entries in the materials master.",
        "unit": "%",
        "target": 100,
        "table": "OPERATIONAL_DATA",
        "aliases": ["material accuracy", "material reference integrity", "orphan materials", "material master match"],
        "sample_queries": [
            "Do all material references match the master?",
            "Material reference integrity",
            "Orphan material IDs",
            "Material data accuracy"
        ]
    },
    "lims_spec_accuracy": {
        "name": "LIMS Spec Compliance",
        "description": "Percentage of LIMS test results where the result value falls within specified limits (spec_low to spec_high). Results outside specs may indicate data quality or process issues.",
        "unit": "%",
        "target": 98,
        "table": "OPERATIONAL_DATA",
        "aliases": ["spec compliance", "OOS rate", "out of spec", "LIMS accuracy", "test result accuracy"],
        "sample_queries": [
            "What percentage of LIMS results are within spec?",
            "Out of spec test results",
            "LIMS spec compliance rate",
            "How many tests failed spec limits?"
        ]
    },

    # ============ TIMELINESS METRICS ============
    "data_freshness_score": {
        "name": "Data Freshness Score",
        "description": "Measures how current our operational data is - percentage of records updated within expected timeframes.",
        "unit": "%",
        "target": 95,
        "table": "OPERATIONAL_DATA",
        "aliases": ["data freshness", "data currency", "stale data", "data timeliness"],
        "sample_queries": [
            "How fresh is our data?",
            "Is our data up to date?",
            "Data freshness score",
            "Stale records in the system"
        ]
    },
    "lims_turnaround_time": {
        "name": "LIMS Turnaround Time",
        "description": "Average turnaround time in days for LIMS test results from sample receipt to approval. Measures lab data timeliness.",
        "unit": "days",
        "target": 2,
        "table": "OPERATIONAL_DATA",
        "aliases": ["LIMS TAT", "lab turnaround", "test turnaround time", "LIMS timeliness"],
        "sample_queries": [
            "What is the LIMS turnaround time?",
            "How long do lab results take?",
            "Average test result turnaround",
            "LIMS TAT performance"
        ]
    },

    # ============ CONSISTENCY METRICS ============
    "cross_system_consistency": {
        "name": "Cross-System Consistency",
        "description": "Percentage of batch records where data is consistent between MES (mes_pasx_batches) and analytics (analytics_batch_status) tables. Measures data reconciliation quality.",
        "unit": "%",
        "target": 100,
        "table": "OPERATIONAL_DATA",
        "aliases": ["data consistency", "cross-system match", "reconciliation", "MES vs analytics consistency"],
        "sample_queries": [
            "How consistent is our data across systems?",
            "Do MES and analytics data match?",
            "Cross-system data consistency",
            "Data reconciliation check"
        ]
    },
    "order_batch_consistency": {
        "name": "Order-Batch Consistency",
        "description": "Percentage of batch records that correctly link to valid production orders. Measures referential integrity between orders and batches.",
        "unit": "%",
        "target": 100,
        "table": "OPERATIONAL_DATA",
        "aliases": ["order-batch match", "order consistency", "batch-order link", "referential integrity"],
        "sample_queries": [
            "Do all batches link to valid orders?",
            "Order-batch referential integrity",
            "Orphan batches without orders",
            "Order-batch consistency check"
        ]
    },

    # ============ UNIQUENESS METRICS ============
    "batch_id_uniqueness": {
        "name": "Batch ID Uniqueness",
        "description": "Percentage of batch IDs that are unique across the system - no duplicate batch records.",
        "unit": "%",
        "target": 100,
        "table": "OPERATIONAL_DATA",
        "aliases": ["duplicate batches", "batch uniqueness", "batch ID duplicates", "unique batch records"],
        "sample_queries": [
            "Are there duplicate batch IDs?",
            "Batch ID uniqueness check",
            "Duplicate batch records",
            "How unique are our batch IDs?"
        ]
    },
    "overall_data_quality_score": {
        "name": "Overall Data Quality Score",
        "description": "Composite data quality score across all dimensions: completeness, accuracy, timeliness, consistency, and uniqueness. Weighted average of all DQ metrics.",
        "unit": "%",
        "target": 95,
        "table": "OPERATIONAL_DATA",
        "aliases": ["overall DQ", "data quality score", "DQ score", "total data quality", "overall quality"],
        "sample_queries": [
            "What is our overall data quality score?",
            "How good is our data quality?",
            "Overall data quality assessment",
            "Data quality summary"
        ]
    }
}


# Foundation Data Products for complex analytical queries
FOUNDATION_DATA_PRODUCTS = {
    "completeness_analysis": {
        "name": "Completeness Analysis",
        "description": "Deep analysis of null values and missing data across all tables",
        "table": "ALL_TABLES",
        "sample_queries": [
            "Which tables have the most missing data?",
            "Null value analysis across all tables",
            "Which columns have the most gaps?"
        ]
    },
    "profiling_report": {
        "name": "Data Profiling Report",
        "description": "Statistical profiling of data tables - distributions, outliers, patterns",
        "table": "ALL_TABLES",
        "sample_queries": [
            "Profile the batch data",
            "Show me data distributions",
            "Statistical summary of LIMS results"
        ]
    },
    "rules_validation": {
        "name": "Rules Validation",
        "description": "Validation of data against business rules and standards",
        "table": "ALL_TABLES",
        "sample_queries": [
            "What data rules are failing?",
            "Business rule violations",
            "Which records break validation rules?"
        ]
    },
    "remediation_report": {
        "name": "Remediation Report",
        "description": "Identifies data issues and suggests remediation actions",
        "table": "ALL_TABLES",
        "sample_queries": [
            "What data needs to be fixed?",
            "Remediation recommendations",
            "Priority data fixes needed"
        ]
    }
}


def get_kpi_catalogue() -> dict:
    return KPI_CATALOGUE


def get_foundation_data_products() -> dict:
    return FOUNDATION_DATA_PRODUCTS


@tool
def search_kpi_catalogue(query: str) -> dict[str, Any]:
    """Search the KPI catalogue for matching data quality metrics."""
    query_lower = query.lower()
    matches = []
    for kpi_id, kpi_info in KPI_CATALOGUE.items():
        score = 0
        for alias in kpi_info["aliases"]:
            if alias.lower() in query_lower:
                score += 10
        for sample in kpi_info["sample_queries"]:
            if any(word in query_lower for word in sample.lower().split()):
                score += 5
        if any(word in query_lower for word in kpi_info["description"].lower().split()):
            score += 2
        if score > 0:
            matches.append({"kpi_id": kpi_id, "score": score, **kpi_info})
    matches.sort(key=lambda x: x["score"], reverse=True)
    return {"matches": matches[:3], "total_matches": len(matches)}


@tool
def get_kpi_details(kpi_id: str) -> dict[str, Any] | None:
    """Get detailed information about a specific data quality KPI."""
    if kpi_id in KPI_CATALOGUE:
        return {"kpi_id": kpi_id, **KPI_CATALOGUE[kpi_id]}
    return None

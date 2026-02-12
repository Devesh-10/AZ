"""
Data Catalogue Tool for MIA
Provides semantic search over KPI definitions and sample queries.
"""

import json
from pathlib import Path
from typing import Any
from langchain_core.tools import tool


# KPI Catalogue - definitions and sample queries for semantic matching
# Rich descriptions help with embeddings-based semantic search
KPI_CATALOGUE = {
    "batch_yield_avg_pct": {
        "name": "Batch Yield",
        "description": "Average batch yield percentage - measures how much usable product comes from production batches. High yield means less waste and better efficiency.",
        "unit": "%",
        "target": 98,
        "table": "KPI_STORE_WEEKLY",
        "aliases": ["yield", "batch yield", "production yield", "yield rate", "yield percentage"],
        "sample_queries": [
            "What is the batch yield?",
            "Show me yield performance",
            "Current yield percentage",
            "How much yield are we getting?",
            "What percentage of batches are successful?",
            "Production yield rate"
        ]
    },
    "rft_pct": {
        "name": "Right First Time (RFT)",
        "description": "Right First Time percentage - measures quality by tracking batches that pass inspection on the first attempt without rework. Also known as first pass yield or first time quality.",
        "unit": "%",
        "target": 92,
        "table": "KPI_STORE_WEEKLY",
        "aliases": ["RFT", "right first time", "first pass yield", "first time right", "first pass rate", "quality rate", "first time quality", "FPY"],
        "sample_queries": [
            "What is the RFT?",
            "Show me right first time rate",
            "First pass yield percentage",
            "How many batches passed first time?",
            "What is the first pass rate?",
            "Quality pass rate",
            "Batches passing on first attempt"
        ]
    },
    "oee_packaging_pct": {
        "name": "OEE Packaging",
        "description": "Overall Equipment Effectiveness for packaging line - measures how efficiently packaging equipment runs considering availability, performance, and quality. Indicates equipment utilization and efficiency.",
        "unit": "%",
        "target": 80,
        "table": "KPI_STORE_WEEKLY",
        "aliases": ["OEE", "equipment effectiveness", "packaging efficiency", "equipment efficiency", "machine efficiency", "packaging OEE", "line efficiency"],
        "sample_queries": [
            "What is the OEE?",
            "Show OEE performance",
            "Equipment effectiveness",
            "How effective is our packaging line?",
            "Packaging line efficiency",
            "Machine performance",
            "Equipment utilization"
        ]
    },
    "avg_cycle_time_hr": {
        "name": "Average Cycle Time",
        "description": "Average cycle time in hours - measures how long it takes to complete one production cycle from start to finish. Lower is better for throughput.",
        "unit": "hours",
        "target": None,
        "table": "KPI_STORE_WEEKLY",
        "aliases": ["cycle time", "production time", "manufacturing time", "processing time", "batch time"],
        "sample_queries": [
            "What is the cycle time?",
            "Average production cycle time",
            "How long does production take?",
            "Manufacturing cycle duration",
            "Time per batch"
        ]
    },
    "formulation_lead_time_hr": {
        "name": "Formulation Lead Time",
        "description": "Formulation lead time in hours - measures the time from start of formulation to completion. Important for production planning and scheduling.",
        "unit": "hours",
        "target": None,
        "table": "KPI_STORE_MONTHLY",
        "aliases": ["lead time", "formulation time", "formulation lead time", "prep time"],
        "sample_queries": [
            "What is the formulation lead time?",
            "Show lead time for formulation",
            "How long does formulation take?",
            "Formulation duration"
        ]
    },
    "schedule_adherence_pct": {
        "name": "Schedule Adherence",
        "description": "Schedule adherence percentage - measures how well production follows the planned schedule. High adherence means on-time delivery and reliable planning.",
        "unit": "%",
        "target": 95,
        "table": "KPI_STORE_WEEKLY",
        "aliases": ["schedule adherence", "on-time delivery", "schedule compliance", "on time", "OTD", "planning accuracy"],
        "sample_queries": [
            "What is the schedule adherence?",
            "Are we meeting schedule targets?",
            "On-time delivery rate",
            "Are we on schedule?",
            "Schedule compliance rate"
        ]
    },
    "deviations_per_100_batches": {
        "name": "Deviations Rate",
        "description": "Number of deviations per 100 batches - measures quality issues and non-conformances in production. Lower is better, indicates fewer problems.",
        "unit": "per 100 batches",
        "target": None,
        "table": "KPI_STORE_WEEKLY",
        "aliases": ["deviations", "deviation rate", "non-conformances", "NCRs", "quality issues", "defects"],
        "sample_queries": [
            "How many deviations do we have?",
            "Show deviation rate",
            "Quality issues per batch",
            "Non-conformance rate",
            "Defect rate"
        ]
    },
    "production_volume": {
        "name": "Production Volume",
        "description": "Total production volume - measures the quantity of products manufactured. Indicates overall production output and capacity utilization.",
        "unit": "units",
        "target": None,
        "table": "KPI_STORE_WEEKLY",
        "aliases": ["volume", "production", "output", "quantity", "throughput", "units produced"],
        "sample_queries": [
            "What is the production volume?",
            "How much did we produce?",
            "Total output",
            "Production quantity",
            "How many units did we make?",
            "Manufacturing output"
        ]
    },
    "batch_count": {
        "name": "Batch Count",
        "description": "Number of batches produced - counts total batches manufactured in a period. Used for capacity planning and workload analysis.",
        "unit": "batches",
        "target": None,
        "table": "KPI_STORE_WEEKLY",
        "aliases": ["batches", "batch count", "number of batches", "total batches", "batch quantity"],
        "sample_queries": [
            "How many batches?",
            "Total batch count",
            "Number of batches produced",
            "Batch quantity this month"
        ]
    }
}

# Foundation Data Products - for complex queries
FOUNDATION_DATA_PRODUCTS = {
    "order_status": {
        "name": "Order Status",
        "description": "Individual order records with status tracking",
        "table": "ORDER_STATUS",
        "sample_queries": [
            "How many orders are in packing today?",
            "How many orders of CP are scheduled this week?",
            "Orders that missed scheduled finish date"
        ]
    },
    "batch_status": {
        "name": "Batch Status",
        "description": "Individual batch records with quality status",
        "table": "MES_PASX_BATCHES",
        "sample_queries": [
            "Which batches are quarantined?",
            "List all finish packs waiting for QA release",
            "Batches with deviations"
        ]
    },
    "factory_flow": {
        "name": "Factory Flow",
        "description": "Production flow data across manufacturing stages",
        "table": "FACTORY_FLOW",
        "sample_queries": [
            "Orders exceeding MLT target",
            "Production flow analysis"
        ]
    },
    "manufacturing_lead_time": {
        "name": "Manufacturing Lead Time",
        "description": "Step-by-step timing for manufacturing processes",
        "table": "MES_PASX_BATCH_STEPS",
        "sample_queries": [
            "What is the lead time for batch X?",
            "Waiting time between steps"
        ]
    }
}


def get_kpi_catalogue() -> dict:
    """Return the full KPI catalogue"""
    return KPI_CATALOGUE


def get_foundation_data_products() -> dict:
    """Return the foundation data products catalogue"""
    return FOUNDATION_DATA_PRODUCTS


@tool
def search_kpi_catalogue(query: str) -> dict[str, Any]:
    """
    Search the KPI catalogue for matching KPIs based on user query.
    Returns matched KPI details including name, description, and SQL template.

    Args:
        query: The user's natural language query about KPIs

    Returns:
        Dictionary with matched KPIs and their details
    """
    query_lower = query.lower()
    matches = []

    for kpi_id, kpi_info in KPI_CATALOGUE.items():
        score = 0

        # Check aliases
        for alias in kpi_info["aliases"]:
            if alias.lower() in query_lower:
                score += 10

        # Check sample queries
        for sample in kpi_info["sample_queries"]:
            if any(word in query_lower for word in sample.lower().split()):
                score += 5

        # Check description
        if any(word in query_lower for word in kpi_info["description"].lower().split()):
            score += 2

        if score > 0:
            matches.append({
                "kpi_id": kpi_id,
                "score": score,
                **kpi_info
            })

    # Sort by score descending
    matches.sort(key=lambda x: x["score"], reverse=True)

    return {
        "matches": matches[:3],  # Top 3 matches
        "total_matches": len(matches)
    }


@tool
def get_kpi_details(kpi_id: str) -> dict[str, Any] | None:
    """
    Get detailed information about a specific KPI.

    Args:
        kpi_id: The KPI identifier (e.g., 'batch_yield_avg_pct')

    Returns:
        KPI details including description, target, and SQL template
    """
    if kpi_id in KPI_CATALOGUE:
        return {
            "kpi_id": kpi_id,
            **KPI_CATALOGUE[kpi_id]
        }
    return None

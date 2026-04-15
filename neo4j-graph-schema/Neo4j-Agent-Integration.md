# Neo4j Integration — Analyst-to-Graph Delegation

## Overview

The Analyst Agent currently handles all COMPLEX queries by loading CSVs into pandas. For questions involving **multi-hop batch genealogy** (MLT, traceability, consumption chains), the Analyst should delegate to Neo4j instead of trying to compute these from flat files.

**Flow:**
```
Supervisor → route_type=COMPLEX → Analyst Agent
                                      │
                                      ├─ Flat query → pandas (existing)
                                      └─ Graph query → Neo4j tool → Cypher → results
```

The Analyst stays the entry point. No new routing from Supervisor. The Analyst itself decides whether to use CSV/pandas or Neo4j based on the question.

---

## Step 1: Graph Query Detector

Add detection logic inside the Analyst Agent to identify graph-worthy questions before loading CSV tables.

```python
# neo4j_detector.py

GRAPH_KEYWORDS = [
    # Multi-hop genealogy
    "mlt", "manufacturing lead time", "batch lead time",
    "formulation to packing", "batch genealogy", "batch trace",
    "trace batch", "traceability",
    # Consumption chains
    "consumed by", "consumption chain", "material flow",
    "inventory days on hand", "days on hand",
    # Impact analysis
    "recall impact", "affected batches", "affected products",
    "which batches", "which products are affected",
    # Relationship queries
    "relationship between", "connected to", "linked to",
    "upstream", "downstream", "supply chain",
    # MLT-specific patterns
    "exceeding mlt", "mlt target", "lead time by order",
    "formulation lead time", "packing lead time", "qa release",
    "warehouse time", "batch cycle",
]

GRAPH_QUESTION_IDS = {
    # Questions from ground truth that benefit from graph
    "Q10": ["exceeding mlt", "mlt target", "orders exceeding"],
    "Q14": ["inventory days on hand", "seloken", "days on hand"],
    "Q20": ["batch mlt", "mlt by order", "manufacturing lead time by order"],
}


def is_graph_query(query: str) -> tuple[bool, str]:
    """
    Determine if a query should go to Neo4j instead of CSV/pandas.
    Returns (should_use_graph, reason).
    """
    query_lower = query.lower()

    # Check direct keyword matches
    for keyword in GRAPH_KEYWORDS:
        if keyword in query_lower:
            return True, f"Matched graph keyword: '{keyword}'"

    # Check ground truth question patterns
    for qid, patterns in GRAPH_QUESTION_IDS.items():
        for pattern in patterns:
            if pattern in query_lower:
                return True, f"Matched {qid} pattern: '{pattern}'"

    return False, ""
```

---

## Step 2: Neo4j Connection

```python
# neo4j_client.py

from neo4j import GraphDatabase
from app.core.config import get_settings

settings = get_settings()

_driver = None

def get_neo4j_driver():
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(
            settings.neo4j_uri,       # e.g. "neo4j://127.0.0.1:7687"
            auth=(settings.neo4j_user, settings.neo4j_password)
        )
    return _driver


def execute_cypher(query: str, params: dict = None) -> list[dict]:
    """Execute a Cypher query and return list of dicts."""
    driver = get_neo4j_driver()
    with driver.session(database=settings.neo4j_database) as session:
        result = session.run(query, params or {})
        return [dict(record) for record in result]
```

Add to `config.py`:

```python
# In Settings class
neo4j_uri: str = "neo4j://127.0.0.1:7687"
neo4j_user: str = "neo4j"
neo4j_password: str = ""
neo4j_database: str = "neo4j"
```

---

## Step 3: Graph Schema + Domain Knowledge (System Prompt)

This is the critical piece. The LLM needs the schema and domain rules to generate correct Cypher.

```python
# graph_schema.py

GRAPH_SCHEMA = """
## Neo4j Graph Schema — MIA Manufacturing

### Nodes
- Batch (batchCode, plantCode, statusCode, localMaterialCode, materialName,
         productFamilyName, productSubFamilyName, totalQuantity, baseUnitOfMeasure,
         usageDecisionCode, usageDecisionDatetime,
         lastGoodsReceiptEntryDatetime, lastGoodsReceiptPostingDatetime,
         samplingEntryDatetime, releaseEntryDatetime,
         goodsIssueEntryDatetime, pickEntryDatetime,
         bestBeforeDate, manufactureDate, batchCreationDate,
         exclusionFromAnalysis, productLocationTypeCode)

- ProcessOrder (processOrderNumber, plantCode, orderTypeCode,
               productionSupervisorIdentifier, confirmedIndicator,
               cancelledIndicator, systemStatusesText, userStatusesText,
               actualStartDatetime, actualFinishDate,
               scheduledStartDatetime, scheduledFinishDatetime,
               totalOrderQuantity, enteredGoodsReceivedQuantity,
               baseTotalScrapQuantity, localMaterialCode, batchCode,
               orderReferenceRelativeWeekNumber, orderReferenceYearWeekNumber,
               finishedOperationsCount, totalOperationsCount)

- Material (localMaterialCode, globalMaterialCode, materialName,
           materialTypeCode, materialTypeName, procurementTypeCode)

- Plant (plantCode, productLocationTypeName)
- ProductFamily (name)
- ProductSubFamily (name)
- Operation (processOrderNumber, operationCode, statusName, operationDatetime)
- WorkCentre (code)
- InspectionLot (referenceNumber, usageDecisionCode, usageDecisionDatetime)
- LIMSLot (lotNumber, dispositionCode, dispositionDatetime,
          totalTestsCount, finishedTestsCount, sampleRecordDatetime)
- QualityEvent (identifier, typeCode)
- QualityNotification (identifier, typeCode)
- Vendor (accountNumber)
- StorageLocation (code, plantCode)
- PlannedOrder (plannedOrderNumber)
- SourceSystem (name, systemId)

### Relationships
- (Batch)-[:MADE_OF]->(Material)
- (Batch)-[:MANUFACTURED_AT]->(Plant)
- (Batch)-[:PRODUCED_BY]->(ProcessOrder)
- (Batch)-[:STORED_IN]->(StorageLocation)
- (Batch)-[:SUPPLIED_BY]->(Vendor)
- (Batch)-[:HAS_INSPECTION]->(InspectionLot)
- (Batch)-[:HAS_LIMS_LOT]->(LIMSLot)
- (Batch)-[:HAS_QUALITY_EVENT]->(QualityEvent)
- (Batch)-[:HAS_QUALITY_NOTIFICATION]->(QualityNotification)
- (Batch)-[:CONSUMED_BY {quantity, unitOfMeasure, relationshipType}]->(ProcessOrder)
- (Batch)-[:SOURCED_FROM]->(SourceSystem)
- (ProcessOrder)-[:EXECUTED_AT]->(Plant)
- (ProcessOrder)-[:PRODUCES]->(Material)
- (ProcessOrder)-[:HAS_OPERATION]->(Operation)
- (ProcessOrder)-[:HAS_INSPECTION]->(InspectionLot)
- (ProcessOrder)-[:ADJUSTS {quantity, unitOfMeasure}]->(Batch)
- (ProcessOrder)-[:ORIGINATES_FROM]->(PlannedOrder)
- (ProcessOrder)-[:SOURCED_FROM]->(SourceSystem)
- (Operation)-[:USES_WORK_CENTRE]->(WorkCentre)
- (Operation)-[:NEXT_OPERATION]->(Operation)
- (Material)-[:BELONGS_TO_SUBFAMILY]->(ProductSubFamily)
- (ProductSubFamily)-[:BELONGS_TO_FAMILY]->(ProductFamily)
- (Plant)-[:HAS_STORAGE]->(StorageLocation)
- (PlannedOrder)-[:RECOMMENDS {quantity}]->(Batch)
"""

DOMAIN_RULES = """
## Domain Rules — CN20 (China Plant)

### Supervisor Code Mapping
- Packing line supervisors: WN8, 100, WT6, WT7, WN7, WT8
- Formulation line supervisors: WN1, WN6, WT1, WT2, WN5
- Supervisor field has 'APC_' prefix that must be stripped:
  toUpper(replace(coalesce(po.productionSupervisorIdentifier, ''), 'APC_', ''))

### Batch Genealogy Traversal (for MLT)
Finding the formulation order for a packing order requires TWO paths:
- Path A (consumption): (consumedBatch)-[:CONSUMED_BY]->(packingOrder),
  then (consumedBatch)-[:PRODUCED_BY]->(formulationOrder)
  WHERE CONSUMED_BY.relationshipType IN ['Consumption', 'Allocation', 'Reservation']
- Path B (adjustment): (packingOrder)-[:ADJUSTS]->(adjBatch),
  then (adjBatch)-[:PRODUCED_BY]->(formulationOrder)
Take the EARLIER formulation start from either path.

### MLT Calculation (4 segments)
1. Formulation LT = formulationStart → formulationGoodsReceipt
2. Warehouse Time = formulationEnd → packingStart (WIP idle time)
3. Packing LT = packingStart → packingGoodsReceipt
4. QA Release LT = packingGoodsReceipt → usageDecisionDatetime
5. Batch MLT = sum of all four

### Working Days (weekend exclusion)
Neo4j has no business-day function. Approximate formula:
  workingDays = (rawHours - 2 * (totalDays / 7) * 24) / 24.0
  where rawHours = duration.inSeconds(start, end).hours
  and totalDays = duration.inDays(start, end).days

### Common Filters
- Confirmed order: toUpper(coalesce(po.confirmedIndicator, '')) = 'Y'
- Not cancelled: toUpper(coalesce(po.cancelledIndicator, '')) <> 'Y'
- Not TECO/CLSD: NOT po.systemStatusesText CONTAINS 'TECO'
- Last week: po.orderReferenceRelativeWeekNumber = -1
- This week: po.orderReferenceRelativeWeekNumber = 0
- Has actual start: po.actualStartDatetime IS NOT NULL

### MLT Targets by Material
| Material | Target (days) |
|----------|--------------|
| CN04-050 | 15.5 |
| 110025941 | 15.5 |
| CN04-010 | 14.4 |
| CN04-080 | 17.1 |
| 110025954 | 17.1 |
| CN08-160 | 15.4 |
| CN04-701 | 4.1 |
| 110022400 | 4.2 |
| CN09-200 | 7.4 |
| CN09-218 | 4.2 |
| CN04-601 | 10.5 |
| CN09-280 | 26.9 |
| 110020809 | 26.9 |
| CN04-070 | 16.5 |
| CN08-170 | 16.5 |
| CN04-015 | 5.3 |

### Deduplication
Neo4j has no ROW_NUMBER(). Use: ORDER BY ... DESC, collect(...)[0] to keep best row per group.
"""
```

---

## Step 4: Few-Shot Cypher Examples

```python
# graph_examples.py

FEW_SHOT_EXAMPLES = """
## Example Cypher Queries

### Count batches in packing today
```cypher
MATCH (po:ProcessOrder)-[:EXECUTED_AT]->(:Plant {plantCode: $plantCode})
WHERE toUpper(replace(coalesce(po.productionSupervisorIdentifier, ''), 'APC_', ''))
      IN $packingSupervisors
  AND po.confirmedIndicator <> 'Y'
  AND po.scheduledFinishDatetime IS NOT NULL
  AND po.scheduledFinishDatetime.truncate('day') = date()
MATCH (b:Batch)-[:PRODUCED_BY]->(po)
RETURN count(DISTINCT b.batchCode) AS batches_in_packing_today
```

### Batches in quality control
```cypher
MATCH (b:Batch)-[:MANUFACTURED_AT]->(:Plant {plantCode: $plantCode})
WHERE b.exclusionFromAnalysis <> 'Y'
  AND b.usageDecisionDatetime IS NULL
MATCH (b)-[:HAS_LIMS_LOT]->(ll:LIMSLot)
WHERE ll.sampleRecordDatetime IS NOT NULL
  AND ll.dispositionDatetime IS NULL
RETURN count(b) AS batches_in_qc
```

### Finish packs waiting for QA release
```cypher
MATCH (po:ProcessOrder)-[:EXECUTED_AT]->(:Plant {plantCode: $plantCode})
WHERE toUpper(replace(coalesce(po.productionSupervisorIdentifier, ''), 'APC_', ''))
      IN $packingSupervisors
  AND toUpper(coalesce(po.confirmedIndicator, '')) = 'Y'
  AND toUpper(coalesce(po.cancelledIndicator, '')) <> 'Y'
MATCH (b:Batch {batchCode: po.batchCode, plantCode: $plantCode})
WHERE b.lastGoodsReceiptEntryDatetime IS NOT NULL
  AND (b.usageDecisionCode IS NULL OR NOT toLower(b.usageDecisionCode) IN ['a','r'])
RETURN po.processOrderNumber AS order_id,
       b.batchCode AS batch, b.productFamilyName AS brand,
       b.lastGoodsReceiptEntryDatetime AS finish_pack_time
ORDER BY b.lastGoodsReceiptEntryDatetime DESC
```

### Raw materials expiring within 6 months
```cypher
MATCH (b:Batch)-[:MANUFACTURED_AT]->(:Plant {plantCode: $plantCode})
WHERE b.bestBeforeDate IS NOT NULL
  AND b.bestBeforeDate >= date()
  AND b.bestBeforeDate <= date() + duration({months: 6})
  AND b.totalQuantity > 0
  AND (b.exclusionFromAnalysis IS NULL OR b.exclusionFromAnalysis = 'N')
RETURN b.batchCode AS batch, b.localMaterialCode AS material,
       b.materialName AS description, toString(b.bestBeforeDate) AS expiry_date,
       b.totalQuantity AS stock
ORDER BY b.bestBeforeDate
```

### Inventory days on hand (consumption-based, graph traversal)
```cypher
MATCH (b:Batch)-[:MANUFACTURED_AT]->(:Plant {plantCode: $plantCode})
WHERE b.productFamilyName = $brand AND b.totalQuantity > 0
WITH sum(b.totalQuantity) AS currentStock
MATCH (consumed:Batch)-[rel:CONSUMED_BY]->(po:ProcessOrder)
WHERE po.plantCode = $plantCode
  AND rel.relationshipType = 'Consumption'
  AND po.actualStartDatetime >= datetime() - duration({months: 6})
MATCH (consumed)-[:MADE_OF]->(m:Material)
WHERE m.materialName CONTAINS $brand
WITH currentStock, sum(rel.quantity) AS totalConsumed6Mo
WITH currentStock, totalConsumed6Mo / 180.0 AS avgDailyConsumption
RETURN currentStock, avgDailyConsumption,
       CASE WHEN avgDailyConsumption > 0
            THEN round(currentStock / avgDailyConsumption)
            ELSE null END AS daysOnHand
```

### Batch MLT by order (Q20 — most complex, template recommended)
See CYPHER_TEMPLATES below — use the pre-built template for this.
"""
```

---

## Step 5: Pre-built Templates for Complex Queries

```python
# graph_templates.py

CYPHER_TEMPLATES = {

    "batch_mlt": {
        "description": "Batch Manufacturing Lead Time by order, 4 segments",
        "params": ["plantCode", "packingSupervisors", "formulationSupervisors"],
        "cypher": """
MATCH (po:ProcessOrder)-[:EXECUTED_AT]->(:Plant {plantCode: $plantCode})
WHERE po.orderReferenceRelativeWeekNumber >= -1
  AND toUpper(replace(coalesce(po.productionSupervisorIdentifier, ''), 'APC_', ''))
      IN $packingSupervisors
  AND toUpper(coalesce(po.confirmedIndicator, '')) = 'Y'
  AND po.actualStartDatetime IS NOT NULL
  AND po.batchCode IS NOT NULL
MATCH (b:Batch {batchCode: po.batchCode, plantCode: $plantCode})
WHERE b.lastGoodsReceiptEntryDatetime IS NOT NULL

OPTIONAL MATCH (cb:Batch)-[rel:CONSUMED_BY]->(po)
WHERE rel.relationshipType IN ['Consumption', 'Allocation', 'Reservation']
OPTIONAL MATCH (cb)-[:PRODUCED_BY]->(formOrd:ProcessOrder {plantCode: $plantCode})
WHERE toUpper(replace(coalesce(formOrd.productionSupervisorIdentifier, ''), 'APC_', ''))
      IN $formulationSupervisors

OPTIONAL MATCH (po)-[:ADJUSTS]->(adjB:Batch)
OPTIONAL MATCH (adjB)-[:PRODUCED_BY]->(adjFormOrd:ProcessOrder {plantCode: $plantCode})
WHERE toUpper(replace(coalesce(adjFormOrd.productionSupervisorIdentifier, ''), 'APC_', ''))
      IN $formulationSupervisors

WITH po, b,
     CASE
       WHEN formOrd.actualStartDatetime IS NOT NULL AND adjFormOrd.actualStartDatetime IS NOT NULL
         THEN CASE WHEN formOrd.actualStartDatetime < adjFormOrd.actualStartDatetime
                   THEN formOrd.actualStartDatetime ELSE adjFormOrd.actualStartDatetime END
       ELSE coalesce(formOrd.actualStartDatetime, adjFormOrd.actualStartDatetime)
     END AS formulationStart,
     CASE
       WHEN formOrd.actualStartDatetime IS NOT NULL THEN cb.lastGoodsReceiptEntryDatetime
       ELSE adjB.lastGoodsReceiptEntryDatetime
     END AS formulationEnd

WITH po, b, min(formulationStart) AS fStart, min(formulationEnd) AS fEnd

WITH po.processOrderNumber AS order_id, po.batchCode AS batch,
     b.productFamilyName AS brand, po.localMaterialCode AS material,
     round((duration.inSeconds(po.actualStartDatetime, b.lastGoodsReceiptEntryDatetime).hours
            - 2*(duration.inDays(po.actualStartDatetime, b.lastGoodsReceiptEntryDatetime).days/7)*24)
           / 24.0 * 10) / 10.0 AS packing_lt,
     CASE WHEN fStart IS NOT NULL AND fEnd IS NOT NULL THEN
       round((duration.inSeconds(fStart, fEnd).hours
              - 2*(duration.inDays(fStart, fEnd).days/7)*24) / 24.0 * 10) / 10.0
     ELSE 0 END AS formulation_lt,
     CASE WHEN fEnd IS NOT NULL AND fEnd < po.actualStartDatetime THEN
       round((duration.inSeconds(fEnd, po.actualStartDatetime).hours
              - 2*(duration.inDays(fEnd, po.actualStartDatetime).days/7)*24) / 24.0 * 10) / 10.0
     ELSE 0 END AS warehouse_lt,
     CASE WHEN b.usageDecisionDatetime IS NOT NULL
          AND b.usageDecisionDatetime > b.lastGoodsReceiptEntryDatetime THEN
       round((duration.inSeconds(b.lastGoodsReceiptEntryDatetime, b.usageDecisionDatetime).hours
              - 2*(duration.inDays(b.lastGoodsReceiptEntryDatetime, b.usageDecisionDatetime).days/7)*24)
             / 24.0 * 10) / 10.0
     ELSE 0 END AS qa_lt

WITH *, round((packing_lt + formulation_lt + warehouse_lt + qa_lt) * 10) / 10.0 AS batch_mlt
ORDER BY order_id, batch_mlt DESC
WITH order_id, collect({
  batch: batch, brand: brand, material: material,
  packing_lt: packing_lt, formulation_lt: formulation_lt,
  warehouse_lt: warehouse_lt, qa_lt: qa_lt, batch_mlt: batch_mlt
})[0] AS best

RETURN order_id, best.batch AS batch, best.brand AS brand,
       best.packing_lt AS packing_lead_time,
       best.formulation_lt AS formulation_lead_time,
       best.warehouse_lt AS warehouse_time,
       best.qa_lt AS qa_release_lead_time,
       best.batch_mlt AS batch_mlt
ORDER BY best.batch_mlt DESC
"""
    },

    "exceeding_mlt": {
        "description": "Orders exceeding MLT target last week",
        "params": ["plantCode", "packingSupervisors", "mltTargets"],
        "cypher": """
UNWIND $mltTargets AS t
MATCH (po:ProcessOrder)-[:EXECUTED_AT]->(:Plant {plantCode: $plantCode})
WHERE po.orderReferenceRelativeWeekNumber = -1
  AND toUpper(replace(coalesce(po.productionSupervisorIdentifier, ''), 'APC_', ''))
      IN $packingSupervisors
  AND toUpper(coalesce(po.confirmedIndicator, '')) = 'Y'
  AND po.actualStartDatetime IS NOT NULL
  AND po.localMaterialCode = t.mat
MATCH (b:Batch)-[:PRODUCED_BY]->(po)
WHERE b.lastGoodsReceiptEntryDatetime IS NOT NULL
WITH po, b, t,
     duration.inDays(po.actualStartDatetime, b.lastGoodsReceiptEntryDatetime).days AS totalDays
WITH po, b, t, totalDays - 2 * (totalDays / 7) AS workingDays
WHERE workingDays > t.mlt
RETURN po.processOrderNumber AS order_id,
       po.localMaterialCode AS material,
       workingDays AS actual_days,
       t.mlt AS target_days
"""
    },

    "inventory_doh": {
        "description": "Inventory days on hand via consumption chain traversal",
        "params": ["plantCode", "brand"],
        "cypher": """
MATCH (b:Batch)-[:MANUFACTURED_AT]->(:Plant {plantCode: $plantCode})
WHERE b.productFamilyName = $brand AND b.totalQuantity > 0
  AND (b.exclusionFromAnalysis IS NULL OR b.exclusionFromAnalysis <> 'Y')
WITH sum(b.totalQuantity) AS currentStock
MATCH (consumed:Batch)-[rel:CONSUMED_BY]->(po:ProcessOrder)
WHERE po.plantCode = $plantCode
  AND rel.relationshipType = 'Consumption'
  AND po.actualStartDatetime >= datetime() - duration({months: 6})
MATCH (consumed)-[:MADE_OF]->(m:Material)
WHERE m.materialName CONTAINS $brand
WITH currentStock, sum(rel.quantity) AS consumed6Mo
RETURN currentStock,
       round(consumed6Mo / 180.0 * 10) / 10.0 AS avg_daily_consumption,
       CASE WHEN consumed6Mo > 0
            THEN round(currentStock / (consumed6Mo / 180.0))
            ELSE null END AS days_on_hand
"""
    },
}

SUPERVISOR_MAPPINGS = {
    "CN20": {
        "packing": ["WN8", "100", "WT6", "WT7", "WN7", "WT8"],
        "formulation": ["WN1", "WN6", "WT1", "WT2", "WN5"],
    },
}

MLT_TARGETS = [
    {"mat": "CN04-050", "mlt": 15.5}, {"mat": "110025941", "mlt": 15.5},
    {"mat": "CN04-010", "mlt": 14.4}, {"mat": "CN04-080", "mlt": 17.1},
    {"mat": "110025954", "mlt": 17.1}, {"mat": "CN08-160", "mlt": 15.4},
    {"mat": "CN04-701", "mlt": 4.1},  {"mat": "110022400", "mlt": 4.2},
    {"mat": "CN09-200", "mlt": 7.4},  {"mat": "CN09-218", "mlt": 4.2},
    {"mat": "CN04-601", "mlt": 10.5}, {"mat": "CN09-280", "mlt": 26.9},
    {"mat": "110020809", "mlt": 26.9}, {"mat": "CN04-070", "mlt": 16.5},
    {"mat": "CN08-170", "mlt": 16.5}, {"mat": "CN04-015", "mlt": 5.3},
]
```

---

## Step 6: Neo4j Tool (called by Analyst)

```python
# graph_tool.py

from langchain_aws import ChatBedrock
from langchain_core.messages import HumanMessage, SystemMessage

from app.core.config import get_settings
from app.tools.neo4j_client import execute_cypher
from app.tools.graph_schema import GRAPH_SCHEMA, DOMAIN_RULES
from app.tools.graph_examples import FEW_SHOT_EXAMPLES
from app.tools.graph_templates import (
    CYPHER_TEMPLATES, SUPERVISOR_MAPPINGS, MLT_TARGETS
)

settings = get_settings()

CYPHER_GENERATION_PROMPT = f"""You generate Cypher queries for a Neo4j manufacturing graph database.
Return ONLY the Cypher query — no explanation, no markdown fences.
Use $paramName for parameters. Always specify relationship directions.

{GRAPH_SCHEMA}

{DOMAIN_RULES}

{FEW_SHOT_EXAMPLES}
"""


def _match_template(query: str) -> tuple[str | None, dict | None]:
    """Check if query matches a pre-built template. Returns (template_key, params) or (None, None)."""
    query_lower = query.lower()
    plant = "CN20"  # default; extract from query if needed
    mapping = SUPERVISOR_MAPPINGS.get(plant, SUPERVISOR_MAPPINGS["CN20"])

    if any(kw in query_lower for kw in ["batch mlt", "manufacturing lead time by order",
                                         "mlt by order", "mlt breakdown"]):
        return "batch_mlt", {
            "plantCode": plant,
            "packingSupervisors": mapping["packing"],
            "formulationSupervisors": mapping["formulation"],
        }

    if any(kw in query_lower for kw in ["exceeding mlt", "mlt target", "exceed mlt"]):
        return "exceeding_mlt", {
            "plantCode": plant,
            "packingSupervisors": mapping["packing"],
            "mltTargets": MLT_TARGETS,
        }

    if any(kw in query_lower for kw in ["days on hand", "inventory doh", "inventory days"]):
        # Extract brand from query
        brand = "Seloken"  # default; should extract from query
        return "inventory_doh", {
            "plantCode": plant,
            "brand": brand,
        }

    return None, None


def _generate_cypher(query: str) -> tuple[str, dict]:
    """Use LLM to generate Cypher for ad-hoc graph questions."""
    llm = ChatBedrock(
        model_id=settings.model_id,
        region_name=settings.aws_region,
        model_kwargs={"temperature": 0, "max_tokens": 2000}
    )

    response = llm.invoke([
        SystemMessage(content=CYPHER_GENERATION_PROMPT),
        HumanMessage(content=f"Generate a Cypher query for: {query}\n\nAssume plantCode = 'CN20'.")
    ])

    cypher = response.content.strip()
    # Strip markdown fences if LLM wraps them
    if cypher.startswith("```"):
        cypher = "\n".join(cypher.split("\n")[1:-1])

    return cypher, {"plantCode": "CN20"}


def run_graph_query(query: str) -> dict:
    """
    Execute a graph query — uses template if available, otherwise generates Cypher.
    Returns {cypher, params, results, source}.
    """
    # 1. Try pre-built template first
    template_key, params = _match_template(query)

    if template_key:
        cypher = CYPHER_TEMPLATES[template_key]["cypher"]
        source = f"template:{template_key}"
    else:
        # 2. Generate Cypher via LLM
        cypher, params = _generate_cypher(query)
        source = "llm_generated"

    # 3. Execute
    try:
        results = execute_cypher(cypher, params)
        return {
            "cypher": cypher,
            "params": params,
            "results": results,
            "source": source,
            "error": None,
        }
    except Exception as e:
        return {
            "cypher": cypher,
            "params": params,
            "results": [],
            "source": source,
            "error": str(e),
        }
```

---

## Step 7: Modify Analyst Agent

The key change — add Neo4j delegation inside the existing `analyst_agent` function.

```python
# In analyst_agent.py — add these imports at top
from app.tools.neo4j_detector import is_graph_query
from app.tools.graph_tool import run_graph_query

# Inside the analyst_agent function, BEFORE the existing CSV/pandas logic:

async def analyst_agent(state: MIAState) -> dict:
    query = state["user_query"]

    # ── Check if this is a graph query ──
    use_graph, reason = is_graph_query(query)

    if use_graph:
        # Delegate to Neo4j
        graph_result = run_graph_query(query)

        if graph_result["error"]:
            # Fall back to CSV/pandas if Neo4j fails
            print(f"Neo4j error: {graph_result['error']}, falling back to CSV")
        else:
            # Format results using LLM (same formatting as CSV path)
            context = _format_graph_results(graph_result)
            generated_cypher = graph_result["cypher"]

            llm = ChatBedrock(
                model_id=settings.model_id,
                region_name=settings.aws_region,
                model_kwargs={"temperature": 0, "max_tokens": 4000}
            )

            response = llm.invoke([
                SystemMessage(content=ANALYST_SYSTEM_PROMPT),
                HumanMessage(content=f"Question: {query}\n\nData from Neo4j graph:\n{context}")
            ])

            return {
                "analyst_result": AnalystResult(
                    content=response.content,
                    tables_used=["neo4j_graph"],
                    match_scores=[1.0],
                    generated_sql=generated_cypher,  # reuse field for Cypher
                ),
                "final_answer": response.content,
                "generated_sql": generated_cypher,
                "agent_logs": state.get("agent_logs", []) + [AgentLog(
                    agent_name="Analyst (Neo4j)",
                    input_summary=query[:100],
                    output_summary=f"Graph query via {graph_result['source']}, "
                                   f"{len(graph_result['results'])} rows returned",
                    status="success",
                    timestamp=datetime.now().isoformat()
                )]
            }

    # ── Existing CSV/pandas path (unchanged) ──
    matched_tables = _semantic_match_tables(query)
    # ... rest of existing code ...


def _format_graph_results(graph_result: dict) -> str:
    """Format Neo4j results as context string for the LLM."""
    results = graph_result["results"]
    if not results:
        return "No results returned from the graph query."

    # Convert to table format
    import pandas as pd
    df = pd.DataFrame(results)
    summary = f"Query returned {len(df)} rows.\n\n"
    summary += df.to_string(index=False, max_rows=50)

    # Add aggregations if numeric columns exist
    numeric_cols = df.select_dtypes(include="number").columns
    if len(numeric_cols) > 0:
        summary += "\n\nSummary statistics:\n"
        summary += df[numeric_cols].describe().to_string()

    return summary
```

---

## Decision Matrix

| Question Type | Detection | Execution |
|---|---|---|
| MLT by order (Q20) | keyword: "batch mlt" | Pre-built template |
| Exceeding MLT (Q10) | keyword: "exceeding mlt" | Pre-built template |
| Inventory DOH (Q14) | keyword: "days on hand" | Pre-built template |
| Batch traceability | keyword: "trace batch" | LLM-generated Cypher |
| Recall impact | keyword: "recall impact" | LLM-generated Cypher |
| Simple counts/filters | Not detected as graph | Existing CSV/pandas path |

---

## File Structure

```
mia-langgraph/backend/app/
├── agents/
│   └── analyst_agent.py        # Modified: add graph detection + delegation
├── tools/
│   ├── neo4j_client.py         # NEW: Neo4j driver connection
│   ├── neo4j_detector.py       # NEW: is_graph_query() detection
│   ├── graph_schema.py         # NEW: schema + domain rules for LLM prompt
│   ├── graph_examples.py       # NEW: few-shot Cypher examples
│   ├── graph_templates.py      # NEW: pre-built Cypher for complex KPIs
│   ├── graph_tool.py           # NEW: template matching + LLM generation + execution
│   ├── data_catalogue.py       # Unchanged
│   └── data_table_catalogue.py # Unchanged
├── core/
│   └── config.py               # Modified: add neo4j_uri, neo4j_user, neo4j_password
├── graph.py                    # Unchanged (no new routing needed)
└── models/
    └── state.py                # Unchanged (reuse generated_sql for Cypher)
```

**No changes to Supervisor, graph.py routing, or state model.** The Neo4j capability is encapsulated entirely within the Analyst Agent.

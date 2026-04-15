# Neo4j Schema Embedding Specification

## Purpose

Instead of passing the entire graph schema into every Cypher-generation prompt (and relying on fragile keyword matching to detect graph queries), we embed **rich, query-aligned descriptions** of nodes, relationships, and domain concepts into a vector store. At query time we retrieve only the relevant fragments, which:

1. **Replaces keyword-based graph detection** — semantic similarity catches paraphrased questions
2. **Reduces prompt size** — only relevant schema fragments go to the LLM
3. **Improves Cypher accuracy** — the LLM sees focused context, not the full schema

---

## What Gets Embedded

Three categories of chunks — **Nodes**, **Relationships**, and **Domain Concepts**. Each chunk is a self-contained text block with structured metadata.

---

## Category 1: Node Descriptions

One embedding per node type. Each includes the business meaning, key properties with valid values, and the kinds of questions users ask about this entity.

### Batch

```yaml
id: "node:Batch"
type: node
text: |
  Node: Batch
  Description: A manufacturing batch of material produced at a plant. Represents a
  discrete quantity of product that moves through the full lifecycle — creation,
  formulation, packing, quality testing, and release. This is the central entity
  in the manufacturing graph.

  Key Properties:
  - batchCode: unique batch identifier (e.g. "0004032851")
  - plantCode: plant where batch was manufactured (e.g. "CN20")
  - statusCode: current SAP batch status
  - localMaterialCode: material/SKU code (e.g. "CN04-050")
  - materialName: human-readable material name
  - productFamilyName: brand name (e.g. "Seloken", "Betaloc")
  - productSubFamilyName: sub-brand
  - totalQuantity: current stock quantity
  - baseUnitOfMeasure: unit (e.g. "EA", "KG")
  - usageDecisionCode: QA release decision — "A" = approved, "R" = rejected, NULL = pending
  - usageDecisionDatetime: when QA decision was made
  - lastGoodsReceiptEntryDatetime: when production output was received (packing completion)
  - lastGoodsReceiptPostingDatetime: when goods receipt was posted in SAP
  - samplingEntryDatetime: when QC sample was taken
  - releaseEntryDatetime: when batch was released for sale
  - goodsIssueEntryDatetime: when batch was issued/shipped
  - pickEntryDatetime: when batch was picked for shipping
  - bestBeforeDate: expiry date
  - manufactureDate: production date
  - batchCreationDate: SAP creation date
  - exclusionFromAnalysis: "Y" = exclude from KPI calculations (test batches, etc.)
  - productLocationTypeCode: FG (finished goods), SFG (semi-finished), RM (raw material)

  Common user questions this node helps answer:
  - "how many batches were produced last week"
  - "batch status", "pending batches"
  - "stock on hand", "current inventory"
  - "expiring batches", "shelf life"
  - "QA release pending", "batches waiting for release"
  - "which batches are in progress"

metadata:
  node: Batch
  properties: [batchCode, plantCode, statusCode, localMaterialCode, materialName,
               productFamilyName, totalQuantity, usageDecisionCode,
               lastGoodsReceiptEntryDatetime, bestBeforeDate, exclusionFromAnalysis]
```

### ProcessOrder

```yaml
id: "node:ProcessOrder"
type: node
text: |
  Node: ProcessOrder
  Description: A manufacturing work order that produces a batch. Each process order
  goes through scheduling, execution (with operations), and confirmation. Process
  orders are the "activity" in the graph — they consume input batches and produce
  output batches. Essential for MLT calculations, production tracking, and genealogy.

  Key Properties:
  - processOrderNumber: unique order ID
  - plantCode: plant where order is executed
  - orderTypeCode: SAP order type
  - productionSupervisorIdentifier: supervisor code with "APC_" prefix (must strip
    for comparison, e.g. "APC_WN8" → "WN8"). Supervisor code determines line type:
    Packing supervisors: WN8, 100, WT6, WT7, WN7, WT8
    Formulation supervisors: WN1, WN6, WT1, WT2, WN5
  - confirmedIndicator: "Y" = order is confirmed/completed
  - cancelledIndicator: "Y" = order was cancelled
  - systemStatusesText: SAP status string (check for "TECO", "CLSD")
  - actualStartDatetime: when production actually started
  - actualFinishDate: when production actually finished
  - scheduledStartDatetime / scheduledFinishDatetime: planned dates
  - totalOrderQuantity: planned production quantity
  - enteredGoodsReceivedQuantity: actual output quantity
  - baseTotalScrapQuantity: waste/scrap quantity
  - localMaterialCode: what material this order produces
  - batchCode: the batch this order produces
  - orderReferenceRelativeWeekNumber: -1 = last week, 0 = this week, 1 = next week
  - finishedOperationsCount / totalOperationsCount: progress tracking

  Common user questions this node helps answer:
  - "orders completed last week", "production orders this week"
  - "which orders are in progress", "order status"
  - "production volume", "output quantity"
  - "scrap rate", "yield"
  - "orders by supervisor", "packing line orders"
  - "scheduled vs actual production"

  Important filters:
  - Confirmed: toUpper(coalesce(po.confirmedIndicator, '')) = 'Y'
  - Not cancelled: toUpper(coalesce(po.cancelledIndicator, '')) <> 'Y'
  - Not technically complete: NOT po.systemStatusesText CONTAINS 'TECO'

metadata:
  node: ProcessOrder
  properties: [processOrderNumber, plantCode, productionSupervisorIdentifier,
               confirmedIndicator, cancelledIndicator, actualStartDatetime,
               localMaterialCode, batchCode, orderReferenceRelativeWeekNumber]
```

### Material

```yaml
id: "node:Material"
type: node
text: |
  Node: Material
  Description: A material master record (SKU). Represents a type of product or raw
  material — not a physical batch, but the definition. Linked to batches via MADE_OF
  and to the product hierarchy via ProductSubFamily → ProductFamily.

  Key Properties:
  - localMaterialCode: plant-specific code (e.g. "CN04-050")
  - globalMaterialCode: cross-plant material code
  - materialName: human-readable name
  - materialTypeCode / materialTypeName: type classification
  - procurementTypeCode: how material is sourced (in-house, external, both)

  Common user questions:
  - "which materials are produced", "material list"
  - "material type", "raw material vs finished good"
  - "product hierarchy", "which brand does this material belong to"

metadata:
  node: Material
  properties: [localMaterialCode, globalMaterialCode, materialName, materialTypeCode]
```

### Plant

```yaml
id: "node:Plant"
type: node
text: |
  Node: Plant
  Description: A manufacturing site. Currently CN20 (Wuxi, China) is the primary
  plant in the graph. All queries default to plantCode = "CN20" unless specified.

  Key Properties:
  - plantCode: unique plant identifier (e.g. "CN20")
  - productLocationTypeName: type of location

  Common user questions:
  - "which plant", "plant performance", "site"

metadata:
  node: Plant
  properties: [plantCode, productLocationTypeName]
```

### Operation

```yaml
id: "node:Operation"
type: node
text: |
  Node: Operation
  Description: A single step within a process order (e.g. weighing, mixing, filling,
  labelling). Operations are linked sequentially via NEXT_OPERATION and executed at
  a WorkCentre. Useful for tracking order progress and identifying bottleneck steps.

  Key Properties:
  - processOrderNumber: parent order
  - operationCode: step identifier
  - statusName: current status of the operation
  - operationDatetime: when the operation was performed

  Common user questions:
  - "which step is the order on", "operation status"
  - "bottleneck operation", "longest step"
  - "work centre utilisation"

metadata:
  node: Operation
  properties: [processOrderNumber, operationCode, statusName, operationDatetime]
```

### InspectionLot

```yaml
id: "node:InspectionLot"
type: node
text: |
  Node: InspectionLot
  Description: A quality inspection record from SAP QM. Created when a batch reaches
  a quality checkpoint. The usageDecisionCode indicates the QA outcome.

  Key Properties:
  - referenceNumber: lot identifier
  - usageDecisionCode: QA decision (A = accept, R = reject)
  - usageDecisionDatetime: when decision was made

  Common user questions:
  - "inspection results", "QA pass/fail"
  - "batches pending inspection"

metadata:
  node: InspectionLot
  properties: [referenceNumber, usageDecisionCode, usageDecisionDatetime]
```

### LIMSLot

```yaml
id: "node:LIMSLot"
type: node
text: |
  Node: LIMSLot
  Description: A lab testing record from the LIMS (Laboratory Information Management
  System). Tracks lab sample progress — when sampled, how many tests, when disposition
  is complete. Key for understanding QC queue and lab throughput.

  Key Properties:
  - lotNumber: LIMS lot ID
  - dispositionCode: final lab disposition
  - dispositionDatetime: when lab testing was completed
  - totalTestsCount: number of tests required
  - finishedTestsCount: number of tests completed
  - sampleRecordDatetime: when sample was recorded in LIMS

  Common user questions:
  - "batches in lab testing", "lab queue"
  - "how many tests remaining", "testing progress"
  - "lab turnaround time", "time in QC"
  - "batches in quality control"

metadata:
  node: LIMSLot
  properties: [lotNumber, dispositionCode, dispositionDatetime,
               totalTestsCount, finishedTestsCount, sampleRecordDatetime]
```

### QualityEvent / QualityNotification

```yaml
id: "node:QualityEvent"
type: node
text: |
  Node: QualityEvent
  Description: A quality event (deviation, OOS, complaint) linked to a batch.

  Key Properties:
  - identifier: event ID
  - typeCode: type of quality event

  Common user questions:
  - "deviations", "quality events", "OOS events"
  - "batches with quality issues"

metadata:
  node: QualityEvent
  properties: [identifier, typeCode]
```

```yaml
id: "node:QualityNotification"
type: node
text: |
  Node: QualityNotification
  Description: A SAP quality notification linked to a batch.

  Key Properties:
  - identifier: notification ID
  - typeCode: notification type

  Common user questions:
  - "quality notifications", "complaints", "NCRs"

metadata:
  node: QualityNotification
  properties: [identifier, typeCode]
```

### Vendor

```yaml
id: "node:Vendor"
type: node
text: |
  Node: Vendor
  Description: A supplier that provides raw materials. Linked to batches via SUPPLIED_BY.

  Key Properties:
  - accountNumber: vendor account ID

  Common user questions:
  - "which vendor supplied", "supplier", "vendor performance"

metadata:
  node: Vendor
  properties: [accountNumber]
```

### StorageLocation

```yaml
id: "node:StorageLocation"
type: node
text: |
  Node: StorageLocation
  Description: A warehouse or storage area within a plant where batches are stored.

  Key Properties:
  - code: storage location code
  - plantCode: parent plant

  Common user questions:
  - "where is the batch stored", "warehouse", "storage location"

metadata:
  node: StorageLocation
  properties: [code, plantCode]
```

### ProductFamily / ProductSubFamily

```yaml
id: "node:ProductFamily"
type: node
text: |
  Node: ProductFamily
  Description: Top-level product brand (e.g. "Seloken", "Betaloc", "Nexium").
  Materials belong to a ProductSubFamily which belongs to a ProductFamily.

  Key Properties:
  - name: brand name

  Common user questions:
  - "which brand", "product family", "Seloken batches", "Betaloc production"

metadata:
  node: ProductFamily
  properties: [name]
```

```yaml
id: "node:ProductSubFamily"
type: node
text: |
  Node: ProductSubFamily
  Description: Sub-brand grouping within a ProductFamily.

  Key Properties:
  - name: sub-family name

  Common user questions:
  - "product sub-family", "product variant"

metadata:
  node: ProductSubFamily
  properties: [name]
```

### PlannedOrder / SourceSystem / WorkCentre

```yaml
id: "node:PlannedOrder"
type: node
text: |
  Node: PlannedOrder
  Description: A planned (not yet converted) production order from MRP.

  Key Properties:
  - plannedOrderNumber: planned order ID

  Common user questions:
  - "planned production", "upcoming orders", "MRP"

metadata:
  node: PlannedOrder
  properties: [plannedOrderNumber]
```

```yaml
id: "node:SourceSystem"
type: node
text: |
  Node: SourceSystem
  Description: The source system that a record originated from (e.g. SAP, MES, LIMS).

  Key Properties:
  - name: system name
  - systemId: system identifier

  Common user questions:
  - "data source", "which system"

metadata:
  node: SourceSystem
  properties: [name, systemId]
```

```yaml
id: "node:WorkCentre"
type: node
text: |
  Node: WorkCentre
  Description: A machine or work station where an operation is performed.

  Key Properties:
  - code: work centre code

  Common user questions:
  - "which machine", "work centre", "equipment utilisation"

metadata:
  node: WorkCentre
  properties: [code]
```

---

## Category 2: Relationship Descriptions

One embedding per relationship type. Critically includes **both endpoint nodes**, the **business meaning**, and **traversal context** (when you'd follow this edge).

### CONSUMED_BY

```yaml
id: "rel:CONSUMED_BY"
type: relationship
text: |
  Relationship: (Batch)-[:CONSUMED_BY]->(ProcessOrder)
  Description: A batch of raw or intermediate material was consumed as input to a
  process order. This is THE core link for batch genealogy and traceability.
  Following CONSUMED_BY chains lets you trace material flow from raw material
  through formulation to final packing.

  Properties:
  - quantity: how much of the batch was consumed
  - unitOfMeasure: unit (e.g. "KG", "EA")
  - relationshipType: "Consumption" (actual), "Allocation" (reserved), "Reservation" (planned)

  When to traverse this relationship:
  - Batch genealogy / traceability: follow CONSUMED_BY to find which orders used a batch
  - MLT calculation: packing order ← CONSUMED_BY ← intermediate batch ← PRODUCED_BY ← formulation order
  - Recall impact: which downstream products contain a recalled raw material
  - Material flow: what inputs went into a finished batch
  - Consumption rate: sum quantities over time for days-on-hand calculations

  Important: Filter by relationshipType IN ['Consumption', 'Allocation', 'Reservation']
  for genealogy. 'Consumption' alone for actual usage quantities.

metadata:
  from_node: Batch
  to_node: ProcessOrder
  relationship: CONSUMED_BY
  properties: [quantity, unitOfMeasure, relationshipType]
```

### PRODUCED_BY

```yaml
id: "rel:PRODUCED_BY"
type: relationship
text: |
  Relationship: (Batch)-[:PRODUCED_BY]->(ProcessOrder)
  Description: A batch was produced as the output of a process order. This is the
  reverse of the production relationship — every finished batch links back to the
  order that created it.

  When to traverse:
  - Find which order made a batch
  - MLT calculation: batch → PRODUCED_BY → order → get actual start/finish times
  - Production history for a batch

metadata:
  from_node: Batch
  to_node: ProcessOrder
  relationship: PRODUCED_BY
```

### ADJUSTS

```yaml
id: "rel:ADJUSTS"
type: relationship
text: |
  Relationship: (ProcessOrder)-[:ADJUSTS]->(Batch)
  Description: A process order performed an inventory adjustment on a batch.
  This is an ALTERNATIVE path for batch genealogy — some packing orders link
  to their intermediate batches via ADJUSTS instead of CONSUMED_BY.

  Properties:
  - quantity: adjustment quantity
  - unitOfMeasure: unit

  When to traverse:
  - MLT calculation (alternative path): packing order → ADJUSTS → adjusted batch → PRODUCED_BY → formulation order
  - Always check BOTH CONSUMED_BY and ADJUSTS paths for complete genealogy
  - Take the EARLIER formulation start from either path

metadata:
  from_node: ProcessOrder
  to_node: Batch
  relationship: ADJUSTS
  properties: [quantity, unitOfMeasure]
```

### MADE_OF

```yaml
id: "rel:MADE_OF"
type: relationship
text: |
  Relationship: (Batch)-[:MADE_OF]->(Material)
  Description: Links a batch to its material master record. Every batch is made of
  exactly one material. Use this to join batch data with material attributes like
  name, type, and product hierarchy.

  When to traverse:
  - Filter batches by material name or code
  - Join to product family hierarchy
  - Group batches by material for aggregation

metadata:
  from_node: Batch
  to_node: Material
  relationship: MADE_OF
```

### MANUFACTURED_AT / EXECUTED_AT

```yaml
id: "rel:MANUFACTURED_AT"
type: relationship
text: |
  Relationship: (Batch)-[:MANUFACTURED_AT]->(Plant)
  Description: Links a batch to the plant where it was manufactured.
  Almost always filtered to plantCode = "CN20" for the Wuxi site.

  When to traverse:
  - Filter batches by plant (nearly every query starts here)

metadata:
  from_node: Batch
  to_node: Plant
  relationship: MANUFACTURED_AT
```

```yaml
id: "rel:EXECUTED_AT"
type: relationship
text: |
  Relationship: (ProcessOrder)-[:EXECUTED_AT]->(Plant)
  Description: Links a process order to the plant where it was executed.

  When to traverse:
  - Filter orders by plant (nearly every query starts here)

metadata:
  from_node: ProcessOrder
  to_node: Plant
  relationship: EXECUTED_AT
```

### PRODUCES

```yaml
id: "rel:PRODUCES"
type: relationship
text: |
  Relationship: (ProcessOrder)-[:PRODUCES]->(Material)
  Description: Which material a process order is set up to produce.

  When to traverse:
  - Find orders for a specific material
  - Production planning queries

metadata:
  from_node: ProcessOrder
  to_node: Material
  relationship: PRODUCES
```

### HAS_OPERATION / NEXT_OPERATION / USES_WORK_CENTRE

```yaml
id: "rel:HAS_OPERATION"
type: relationship
text: |
  Relationship: (ProcessOrder)-[:HAS_OPERATION]->(Operation)
  Description: Links an order to its individual production steps.

  When to traverse:
  - Order progress tracking
  - Bottleneck analysis by operation step

metadata:
  from_node: ProcessOrder
  to_node: Operation
  relationship: HAS_OPERATION
```

```yaml
id: "rel:NEXT_OPERATION"
type: relationship
text: |
  Relationship: (Operation)-[:NEXT_OPERATION]->(Operation)
  Description: Sequential link between operations within the same order.
  Forms a chain representing the production workflow.

  When to traverse:
  - Operation sequence / workflow analysis
  - Finding next/previous step

metadata:
  from_node: Operation
  to_node: Operation
  relationship: NEXT_OPERATION
```

```yaml
id: "rel:USES_WORK_CENTRE"
type: relationship
text: |
  Relationship: (Operation)-[:USES_WORK_CENTRE]->(WorkCentre)
  Description: Which machine/station an operation runs on.

  When to traverse:
  - Equipment utilisation, machine scheduling

metadata:
  from_node: Operation
  to_node: WorkCentre
  relationship: USES_WORK_CENTRE
```

### Quality Relationships

```yaml
id: "rel:HAS_INSPECTION"
type: relationship
text: |
  Relationship: (Batch)-[:HAS_INSPECTION]->(InspectionLot)
  Also: (ProcessOrder)-[:HAS_INSPECTION]->(InspectionLot)
  Description: Links a batch or order to its SAP QM inspection lot.

  When to traverse:
  - QA status, inspection results, pass/fail rates

metadata:
  from_node: [Batch, ProcessOrder]
  to_node: InspectionLot
  relationship: HAS_INSPECTION
```

```yaml
id: "rel:HAS_LIMS_LOT"
type: relationship
text: |
  Relationship: (Batch)-[:HAS_LIMS_LOT]->(LIMSLot)
  Description: Links a batch to its lab testing record. A batch with a LIMSLot
  where sampleRecordDatetime is set but dispositionDatetime is NULL is currently
  in quality control / lab testing.

  When to traverse:
  - "Batches in QC" — sampleRecordDatetime IS NOT NULL AND dispositionDatetime IS NULL
  - Lab testing progress, turnaround time

metadata:
  from_node: Batch
  to_node: LIMSLot
  relationship: HAS_LIMS_LOT
```

```yaml
id: "rel:HAS_QUALITY_EVENT"
type: relationship
text: |
  Relationship: (Batch)-[:HAS_QUALITY_EVENT]->(QualityEvent)
  Description: Links a batch to a quality event (deviation, OOS).

  When to traverse:
  - Deviation analysis, quality issue tracking

metadata:
  from_node: Batch
  to_node: QualityEvent
  relationship: HAS_QUALITY_EVENT
```

```yaml
id: "rel:HAS_QUALITY_NOTIFICATION"
type: relationship
text: |
  Relationship: (Batch)-[:HAS_QUALITY_NOTIFICATION]->(QualityNotification)
  Description: Links a batch to a SAP quality notification.

  When to traverse:
  - Quality notification tracking, complaint analysis

metadata:
  from_node: Batch
  to_node: QualityNotification
  relationship: HAS_QUALITY_NOTIFICATION
```

### Other Relationships

```yaml
id: "rel:STORED_IN"
type: relationship
text: |
  Relationship: (Batch)-[:STORED_IN]->(StorageLocation)
  Description: Where a batch is physically stored in the warehouse.

metadata:
  from_node: Batch
  to_node: StorageLocation
  relationship: STORED_IN
```

```yaml
id: "rel:SUPPLIED_BY"
type: relationship
text: |
  Relationship: (Batch)-[:SUPPLIED_BY]->(Vendor)
  Description: Which vendor supplied a raw material batch.

metadata:
  from_node: Batch
  to_node: Vendor
  relationship: SUPPLIED_BY
```

```yaml
id: "rel:BELONGS_TO_SUBFAMILY"
type: relationship
text: |
  Relationship: (Material)-[:BELONGS_TO_SUBFAMILY]->(ProductSubFamily)
  Description: Links a material to its product sub-family.

metadata:
  from_node: Material
  to_node: ProductSubFamily
  relationship: BELONGS_TO_SUBFAMILY
```

```yaml
id: "rel:BELONGS_TO_FAMILY"
type: relationship
text: |
  Relationship: (ProductSubFamily)-[:BELONGS_TO_FAMILY]->(ProductFamily)
  Description: Links a sub-family to the top-level brand/product family.

metadata:
  from_node: ProductSubFamily
  to_node: ProductFamily
  relationship: BELONGS_TO_FAMILY
```

```yaml
id: "rel:HAS_STORAGE"
type: relationship
text: |
  Relationship: (Plant)-[:HAS_STORAGE]->(StorageLocation)
  Description: Storage locations within a plant.

metadata:
  from_node: Plant
  to_node: StorageLocation
  relationship: HAS_STORAGE
```

```yaml
id: "rel:ORIGINATES_FROM"
type: relationship
text: |
  Relationship: (ProcessOrder)-[:ORIGINATES_FROM]->(PlannedOrder)
  Description: Which planned order a process order was converted from.

metadata:
  from_node: ProcessOrder
  to_node: PlannedOrder
  relationship: ORIGINATES_FROM
```

```yaml
id: "rel:RECOMMENDS"
type: relationship
text: |
  Relationship: (PlannedOrder)-[:RECOMMENDS]->(Batch)
  Description: MRP recommendation linking a planned order to a batch.
  Properties: quantity

metadata:
  from_node: PlannedOrder
  to_node: Batch
  relationship: RECOMMENDS
  properties: [quantity]
```

```yaml
id: "rel:SOURCED_FROM"
type: relationship
text: |
  Relationship: (Batch)-[:SOURCED_FROM]->(SourceSystem)
  Also: (ProcessOrder)-[:SOURCED_FROM]->(SourceSystem)
  Description: Which source system a record came from (SAP, MES, LIMS).

metadata:
  from_node: [Batch, ProcessOrder]
  to_node: SourceSystem
  relationship: SOURCED_FROM
```

---

## Category 3: Domain Concept Descriptions

These are the **most important embeddings**. They map business questions to multi-hop graph traversal patterns. A user asking "how long does Seloken take to make" won't match any single node or relationship — it matches the MLT *concept*.

### Manufacturing Lead Time (MLT)

```yaml
id: "concept:MLT"
type: concept
text: |
  Concept: Manufacturing Lead Time (MLT)
  Description: Total elapsed working time from the start of formulation to QA release
  of a finished batch. This is the primary manufacturing performance KPI.

  Calculated as 4 segments:
  1. Formulation Lead Time = formulation order actual start → formulation goods receipt
  2. Warehouse Time (WIP idle) = formulation end → packing order actual start
  3. Packing Lead Time = packing order start → packing goods receipt
  4. QA Release Lead Time = packing goods receipt → batch usage decision datetime
  5. Batch MLT = sum of all four segments

  Graph traversal required:
  - Start from a PACKING process order (supervisor IN [WN8, 100, WT6, WT7, WN7, WT8])
  - Find the corresponding FORMULATION order via TWO possible paths:
    Path A: (consumedBatch)-[:CONSUMED_BY]->(packingOrder), then (consumedBatch)-[:PRODUCED_BY]->(formulationOrder)
    Path B: (packingOrder)-[:ADJUSTS]->(adjBatch), then (adjBatch)-[:PRODUCED_BY]->(formulationOrder)
  - Take the EARLIER formulation start from either path
  - Calculate each segment in working days (exclude weekends)

  Nodes involved: Batch, ProcessOrder
  Relationships involved: CONSUMED_BY, PRODUCED_BY, ADJUSTS, EXECUTED_AT

  MLT targets by material:
  CN04-050: 15.5 days, CN04-010: 14.4, CN04-080: 17.1, CN08-160: 15.4,
  CN04-701: 4.1, CN09-200: 7.4, CN09-218: 4.2, CN04-601: 10.5,
  CN09-280: 26.9, CN04-070: 16.5, CN08-170: 16.5, CN04-015: 5.3

  Common user questions:
  - "what is the MLT for Seloken"
  - "manufacturing lead time by order"
  - "how long does it take to produce a batch"
  - "batch cycle time"
  - "formulation to packing time"
  - "lead time breakdown"
  - "MLT trend this month"

  NOT this concept:
  - Simple "how many batches" counts (use Batch node directly)
  - Single-order status checks (use ProcessOrder node)

metadata:
  nodes: [Batch, ProcessOrder]
  relationships: [CONSUMED_BY, PRODUCED_BY, ADJUSTS, EXECUTED_AT]
  kpi: true
  template: batch_mlt
```

### Exceeding MLT Target

```yaml
id: "concept:ExceedingMLT"
type: concept
text: |
  Concept: Orders Exceeding MLT Target
  Description: Identifies process orders where the actual manufacturing lead time
  exceeded the predefined target for that material. This is a compliance/performance
  alert KPI — management wants to know which orders took too long and by how much.

  Requires: Full MLT calculation (see concept:MLT) PLUS comparison against material-
  specific target days.

  Graph traversal: Same as MLT, with additional WHERE clause filtering results
  where actual working days > target days for the material.

  Nodes involved: Batch, ProcessOrder, Material
  Relationships involved: CONSUMED_BY, PRODUCED_BY, ADJUSTS, EXECUTED_AT

  Common user questions:
  - "which orders exceeded MLT target"
  - "orders exceeding MLT last week"
  - "MLT breaches", "MLT violations"
  - "batches over target lead time"
  - "worst performing orders"

metadata:
  nodes: [Batch, ProcessOrder]
  relationships: [CONSUMED_BY, PRODUCED_BY, ADJUSTS, EXECUTED_AT]
  kpi: true
  template: exceeding_mlt
```

### Batch Genealogy / Traceability

```yaml
id: "concept:BatchGenealogy"
type: concept
text: |
  Concept: Batch Genealogy and Traceability
  Description: Tracing the full lineage of a batch — which raw materials were used,
  which intermediate batches were produced, and which finished products they ended up
  in. This is a multi-hop graph traversal that is impossible with flat CSV files.

  Forward trace (raw → finished): follow CONSUMED_BY → ProcessOrder → PRODUCED_BY ← Batch, repeat
  Reverse trace (finished → raw): follow PRODUCED_BY → ProcessOrder ← CONSUMED_BY ← Batch, repeat

  Nodes involved: Batch, ProcessOrder, Material
  Relationships involved: CONSUMED_BY, PRODUCED_BY, ADJUSTS, MADE_OF

  Common user questions:
  - "trace batch X", "batch genealogy for X"
  - "which raw materials went into batch X"
  - "which finished products contain material from batch X"
  - "batch traceability", "material traceability"
  - "upstream batches", "downstream batches"
  - "full batch history"

metadata:
  nodes: [Batch, ProcessOrder, Material]
  relationships: [CONSUMED_BY, PRODUCED_BY, ADJUSTS, MADE_OF]
  kpi: false
```

### Recall Impact Analysis

```yaml
id: "concept:RecallImpact"
type: concept
text: |
  Concept: Recall Impact Analysis
  Description: Given a problematic raw material batch, identify ALL downstream
  finished product batches that may be affected. This is a forward trace through
  the consumption chain — critical for quality and regulatory compliance.

  Graph traversal:
  - Start at the recalled Batch
  - Follow (Batch)-[:CONSUMED_BY]->(ProcessOrder) to find orders that used it
  - Then (ProcessOrder)<-[:PRODUCED_BY]-(outputBatch) to find what was produced
  - Repeat for multi-stage production

  Nodes involved: Batch, ProcessOrder, Material, Plant
  Relationships involved: CONSUMED_BY, PRODUCED_BY, MADE_OF

  Common user questions:
  - "recall impact for batch X"
  - "which products are affected by batch X"
  - "affected batches", "affected products"
  - "downstream impact of quality issue"
  - "which finished goods used this raw material"

metadata:
  nodes: [Batch, ProcessOrder, Material]
  relationships: [CONSUMED_BY, PRODUCED_BY, MADE_OF]
  kpi: false
```

### Inventory Days on Hand

```yaml
id: "concept:InventoryDOH"
type: concept
text: |
  Concept: Inventory Days on Hand (DOH)
  Description: How many days the current stock of a product will last based on
  historical consumption rates. Requires two pieces of data:
  1. Current stock: sum of Batch.totalQuantity for the brand
  2. Consumption rate: sum of CONSUMED_BY quantities over the past 6 months, divided by 180

  Graph traversal:
  - Current stock: MATCH (b:Batch) WHERE b.productFamilyName = brand AND b.totalQuantity > 0
  - Consumption: MATCH (b)-[rel:CONSUMED_BY]->(po) WHERE rel.relationshipType = 'Consumption'
    AND po.actualStartDatetime >= 6 months ago
  - DOH = currentStock / avgDailyConsumption

  Nodes involved: Batch, ProcessOrder, Material
  Relationships involved: CONSUMED_BY, MADE_OF, MANUFACTURED_AT

  Common user questions:
  - "days on hand for Seloken"
  - "inventory DOH", "how long will stock last"
  - "inventory coverage", "stock coverage days"
  - "when will we run out of X"

metadata:
  nodes: [Batch, ProcessOrder, Material]
  relationships: [CONSUMED_BY, MADE_OF, MANUFACTURED_AT]
  kpi: true
  template: inventory_doh
```

### Batches in Quality Control

```yaml
id: "concept:BatchesInQC"
type: concept
text: |
  Concept: Batches Currently in Quality Control
  Description: Batches that have been sampled (have a LIMS lot with sample datetime)
  but have not yet received a final disposition. These are sitting in the QC lab queue.

  Graph traversal:
  - MATCH (b:Batch)-[:HAS_LIMS_LOT]->(ll:LIMSLot)
  - WHERE ll.sampleRecordDatetime IS NOT NULL AND ll.dispositionDatetime IS NULL
  - AND b.usageDecisionDatetime IS NULL (no QA decision yet)

  Nodes involved: Batch, LIMSLot
  Relationships involved: HAS_LIMS_LOT, MANUFACTURED_AT

  Common user questions:
  - "batches in QC", "batches in quality control"
  - "lab queue", "pending lab tests"
  - "how many batches waiting for lab results"

metadata:
  nodes: [Batch, LIMSLot]
  relationships: [HAS_LIMS_LOT, MANUFACTURED_AT]
  kpi: true
```

### Finished Packs Awaiting QA Release

```yaml
id: "concept:AwaitingQARelease"
type: concept
text: |
  Concept: Finished Packs Awaiting QA Release
  Description: Packing orders that are confirmed complete (goods receipt done) but
  the batch has not yet received a usage decision (QA release). These represent
  finished inventory waiting for quality sign-off before it can be shipped.

  Graph traversal:
  - MATCH (po:ProcessOrder) with packing supervisor codes, confirmed = 'Y'
  - MATCH (b:Batch) with lastGoodsReceiptEntryDatetime IS NOT NULL
  - WHERE usageDecisionCode IS NULL or not in ['a', 'r']

  Nodes involved: Batch, ProcessOrder, Plant
  Relationships involved: PRODUCED_BY, EXECUTED_AT

  Common user questions:
  - "finish packs waiting for QA"
  - "batches awaiting release"
  - "completed but not released"
  - "pending QA release"

metadata:
  nodes: [Batch, ProcessOrder]
  relationships: [PRODUCED_BY, EXECUTED_AT]
  kpi: true
```

### Raw Material Expiry

```yaml
id: "concept:RawMaterialExpiry"
type: concept
text: |
  Concept: Raw Materials Expiring Soon
  Description: Raw material batches with a bestBeforeDate approaching within a given
  window (e.g. 6 months). Important for procurement planning and waste reduction.

  Graph traversal:
  - MATCH (b:Batch) WHERE b.bestBeforeDate IS NOT NULL
    AND b.bestBeforeDate >= date() AND b.bestBeforeDate <= date() + duration({months: 6})
    AND b.totalQuantity > 0

  Nodes involved: Batch, Material, Plant
  Relationships involved: MANUFACTURED_AT, MADE_OF

  Common user questions:
  - "expiring raw materials", "materials expiring soon"
  - "shelf life", "best before date"
  - "materials expiring in the next 3 months"
  - "waste risk from expiry"

metadata:
  nodes: [Batch, Material]
  relationships: [MANUFACTURED_AT, MADE_OF]
  kpi: false
```

---

## Retrieval Flow

```
User query: "how long does Seloken take to make"
                │
                ▼
        Embed user query
                │
                ▼
    Semantic search against all chunks
                │
                ▼
    Top-k results (k=5):
      1. concept:MLT              (score: 0.92)  ← "how long to produce"
      2. node:ProcessOrder         (score: 0.78)  ← "production timing"
      3. rel:CONSUMED_BY           (score: 0.74)  ← genealogy traversal
      4. node:Batch                (score: 0.71)  ← batch entity
      5. concept:BatchGenealogy    (score: 0.65)  ← traceability
                │
                ▼
    Decision: concept:MLT score > 0.8 → this IS a graph query
              Use template "batch_mlt"
              Inject only MLT-relevant schema into Cypher prompt
```

---

## Embedding Chunk Design Principles

| Principle | What to include | Why |
|---|---|---|
| **Business language** | Plain English description of what the entity represents | Users ask in business terms, not schema terms |
| **Common questions / synonyms** | 5-10 example questions per chunk | Bridges "DOH" → "days on hand" → inventory concept |
| **Property descriptions with valid values** | e.g. `usageDecisionCode: A=approved, R=rejected` | Helps LLM generate correct WHERE filters |
| **Traversal context** | "When to traverse this relationship" section | Tells the retriever which relationships matter for a concept |
| **Negative signals** | "NOT this concept" section | Prevents false-positive matches |
| **Multi-hop patterns** | Full path description for concepts | MLT needs 4 hops — a single relationship embedding won't capture this |
| **Domain-specific filters** | Supervisor codes, status filters, date logic | Without these, generated Cypher will be wrong even with correct structure |

---

## What NOT to Embed

- Raw Cypher queries (put these in few-shot examples, not embeddings)
- Implementation details (connection strings, driver config)
- Data values (actual batch codes, order numbers — these change daily)
- Aggregation logic (working day formulas — put in domain rules prompt)

// ============================================================================
// MIA Ground Truth Questions — SQL → Cypher Conversion
// ============================================================================
// All queries target the `mia` Neo4j database (bolt://127.0.0.1:7687)
//
// KEY MAPPING NOTES:
//   SQL BATCH_STATUS         → :Batch node
//   SQL ORDER_STATUS         → :ProcessOrder node
//   SQL ORDER_BATCH_REL      → :CONSUMED_BY / :RECOMMENDS / :ADJUSTS relationships
//   b.PRODUCT_FAMILY_NAME    → b.productFamilyName  (on Batch)
//   po.PRODUCTION_SUPERVISOR → po.productionSupervisorIdentifier (on ProcessOrder)
//   po.CONFIRMED_INDICATOR   → po.confirmedIndicator (on ProcessOrder)
//   po.CANCELLED_INDICATOR   → po.cancelledIndicator (on ProcessOrder)
//   po.SYSTEM_STATUSES_TEXT  → po.systemStatusesText (on ProcessOrder)
//   po.SCHEDULED_FINISH_DT   → po.scheduledFinishDatetime (on ProcessOrder, datetime)
//   po.ACTUAL_START_DT       → po.actualStartDatetime (on ProcessOrder, datetime)
//   po.ACTUAL_FINISH_DATE    → po.actualFinishDate (on ProcessOrder, date)
//   b.BATCH_LAST_GOODS_RECEIPT_ENTRY_DATETIME → b.lastGoodsReceiptEntryDatetime (on Batch, datetime)
//   b.USAGE_DECISION_DATETIME → b.usageDecisionDatetime (on Batch, datetime)
//   b.USAGE_DECISION_CODE    → b.usageDecisionCode (on Batch)
//   b.LIMS_SAMPLE_RECORD_DT  → ll.sampleRecordDatetime (on LIMSLot via b-[:HAS_LIMS_LOT]->ll)
//   b.LIMS_DISPOSITION_DT    → ll.dispositionDatetime (on LIMSLot via b-[:HAS_LIMS_LOT]->ll)
//   b.BATCH_EXCLUSION_...    → b.exclusionFromAnalysis (on Batch)
//   b.BEST_BEFORE_DATE       → b.bestBeforeDate (on Batch, date)
//   b.BATCH_TOTAL_QUANTITY   → b.totalQuantity (on Batch, float)
//   b.BASE_UNIT_OF_MEASURE   → b.baseUnitOfMeasure (on Batch)
//   b.PRODUCT_LOCATION_TYPE  → b.productLocationTypeCode (on Batch)
//   po.LOCAL_MATERIAL_CODE   → po.localMaterialCode (on ProcessOrder)
//   po.WORK_CENTRE_CODE      → via (po)-[:HAS_OPERATION]->(op)-[:USES_WORK_CENTRE]->(wc:WorkCentre)
//   po.ORDER_REF_REL_WEEK    → po.orderReferenceRelativeWeekNumber (on ProcessOrder, int)
//   po.TOTAL_ORDER_QUANTITY  → po.totalOrderQuantity (on ProcessOrder, float)
//   po.ENTERED_GOODS_RECEIVED_QTY → po.enteredGoodsReceivedQuantity (on ProcessOrder, float)
//   b.PLANT_CODE / po.PRODUCTION_PLANT_CODE → :Plant {plantCode}
//     (via b-[:MANUFACTURED_AT]->p  or  po-[:EXECUTED_AT]->p)
//     Or directly: b.plantCode, po.productionPlantCode on the nodes
// ============================================================================


// ---------------------------------------------------------------------------
// Q2: How many batches are in packing today?
// ---------------------------------------------------------------------------
// SQL joins ORDER_STATUS + BATCH_STATUS on PROCESS_ORDER_NUMBER,
// filters packing supervisors, not confirmed, not TECO/CLSD,
// scheduled_finish = today
// ---------------------------------------------------------------------------
MATCH (po:ProcessOrder)-[:EXECUTED_AT]->(:Plant {plantCode: 'CN20'})
WHERE po.productionSupervisorIdentifier IS NOT NULL
  AND toUpper(replace(po.productionSupervisorIdentifier, 'APC_', ''))
      IN ['WN8','100','WT6','WT7','WN7','WT8']
  AND po.confirmedIndicator <> 'Y'
  AND (po.systemStatusesText IS NULL
       OR (NOT po.systemStatusesText CONTAINS 'TECO'
           AND NOT po.systemStatusesText CONTAINS 'CLSD'))
  AND po.scheduledFinishDatetime IS NOT NULL
  AND po.scheduledFinishDatetime.truncate('day') = date()
MATCH (b:Batch)-[:PRODUCED_BY]->(po)
RETURN count(DISTINCT b.batchCode) AS batches_in_packing_today;


// ---------------------------------------------------------------------------
// Q3: How many batches in quality control?
// ---------------------------------------------------------------------------
// Batch at CN20, has LIMS sample but no disposition, not excluded, no usage decision
// LIMS fields are on LIMSLot node (not Batch)
// ---------------------------------------------------------------------------
MATCH (b:Batch)-[:MANUFACTURED_AT]->(:Plant {plantCode: 'CN20'})
WHERE b.exclusionFromAnalysis <> 'Y'
  AND b.usageDecisionDatetime IS NULL
MATCH (b)-[:HAS_LIMS_LOT]->(ll:LIMSLot)
WHERE ll.sampleRecordDatetime IS NOT NULL
  AND ll.dispositionDatetime IS NULL
RETURN count(b) AS num_batches_in_qc;


// ---------------------------------------------------------------------------
// Q4: How many orders of CP (China Packing) are scheduled this week?
// ---------------------------------------------------------------------------
// ORDER_REF_REL_WEEK = 0, supervisor = WN8, not cancelled, plant = CN20
// ---------------------------------------------------------------------------
MATCH (po:ProcessOrder)-[:EXECUTED_AT]->(:Plant {plantCode: 'CN20'})
WHERE po.orderReferenceRelativeWeekNumber = 0
  AND toUpper(replace(coalesce(po.productionSupervisorIdentifier, ''), 'APC_', '')) = 'WN8'
  AND toUpper(coalesce(po.cancelledIndicator, '')) <> 'Y'
RETURN count(DISTINCT po.processOrderNumber) AS china_packing_orders_this_week;


// ---------------------------------------------------------------------------
// Q6: How many orders scheduled & finished this week? (Total, Packing, Formulation)
// ---------------------------------------------------------------------------
MATCH (po:ProcessOrder)-[:EXECUTED_AT]->(:Plant {plantCode: 'CN20'})
WHERE po.orderReferenceRelativeWeekNumber = 0
  AND toUpper(coalesce(po.cancelledIndicator, '')) <> 'Y'
WITH po,
     toUpper(replace(coalesce(po.productionSupervisorIdentifier, ''), 'APC_', '')) AS sup
WHERE sup IN ['WN8','100','WT6','WT7','WN7','WT8','WN1','WN6','WT1','WT2']
WITH po,
     CASE
       WHEN sup IN ['WN8','100','WT6','WT7','WN7','WT8'] THEN 'Packing'
       WHEN sup IN ['WN1','WN6','WT1','WT2']             THEN 'Formulation'
     END AS category,
     toUpper(replace(coalesce(po.productionSupervisorIdentifier, ''), 'APC_', '')) AS sup
// Per-category
WITH category,
     count(DISTINCT po.processOrderNumber) AS scheduled_orders_count,
     count(DISTINCT CASE WHEN toUpper(coalesce(po.confirmedIndicator, '')) = 'Y'
                         THEN po.processOrderNumber END) AS finished_orders_count
RETURN category, scheduled_orders_count, finished_orders_count
ORDER BY CASE category WHEN 'Total' THEN 1 WHEN 'Packing' THEN 2 ELSE 3 END;

// NOTE: For the "Total" row, run a second query or UNION isn't supported natively in Cypher.
// Alternative — get both in one query using collect + unwind:
MATCH (po:ProcessOrder)-[:EXECUTED_AT]->(:Plant {plantCode: 'CN20'})
WHERE po.orderReferenceRelativeWeekNumber = 0
  AND toUpper(coalesce(po.cancelledIndicator, '')) <> 'Y'
WITH po,
     toUpper(replace(coalesce(po.productionSupervisorIdentifier, ''), 'APC_', '')) AS sup
WHERE sup IN ['WN8','100','WT6','WT7','WN7','WT8','WN1','WN6','WT1','WT2']
WITH po,
     CASE
       WHEN sup IN ['WN8','100','WT6','WT7','WN7','WT8'] THEN 'Packing'
       WHEN sup IN ['WN1','WN6','WT1','WT2']             THEN 'Formulation'
     END AS category
WITH collect({id: po.processOrderNumber, cat: category,
              confirmed: toUpper(coalesce(po.confirmedIndicator,''))}) AS rows
UNWIND ['Total','Packing','Formulation'] AS cat
WITH cat, [r IN rows WHERE cat = 'Total' OR r.cat = cat] AS filtered
RETURN cat AS category,
       size(apoc.coll.toSet([r IN filtered | r.id])) AS scheduled_orders_count,
       size(apoc.coll.toSet([r IN filtered WHERE r.confirmed = 'Y' | r.id])) AS finished_orders_count
ORDER BY CASE cat WHEN 'Total' THEN 1 WHEN 'Packing' THEN 2 ELSE 3 END;


// ---------------------------------------------------------------------------
// Q7: How many orders missed scheduled finish date for Packing
//     during the week of February 4, 2026?
// ---------------------------------------------------------------------------
WITH date('2026-02-04') AS ref_date
WITH ref_date,
     date({year: ref_date.year, month: ref_date.month, day: ref_date.day})
       - duration({days: (ref_date.dayOfWeek - 1)}) AS week_start
WITH week_start, week_start + duration({days: 6}) AS week_end
MATCH (po:ProcessOrder)-[:EXECUTED_AT]->(:Plant {plantCode: 'CN20'})
WHERE toUpper(replace(coalesce(po.productionSupervisorIdentifier, ''), 'APC_', ''))
      IN ['WN8','100','WT6','WT7','WN7','WT8']
  AND po.scheduledFinishDatetime IS NOT NULL
  AND po.scheduledFinishDatetime.truncate('day') >= week_start
  AND po.scheduledFinishDatetime.truncate('day') <= week_end
  AND toUpper(coalesce(po.cancelledIndicator, '')) <> 'Y'
  AND (po.actualFinishDate IS NULL
       OR po.actualFinishDate > po.scheduledFinishDatetime.truncate('day'))
RETURN count(*) AS missed_finish_date_count;


// ---------------------------------------------------------------------------
// Q9: Is there any Formulation orders missing scheduled finish date last week?
// ---------------------------------------------------------------------------
// "missing" = orders that had a scheduled finish but didn't actually finish
// (or finished late), not TECO/CLSD, not cancelled
// ---------------------------------------------------------------------------
MATCH (po:ProcessOrder)-[:EXECUTED_AT]->(:Plant {plantCode: 'CN20'})
WHERE po.orderReferenceRelativeWeekNumber = -1
  AND toUpper(replace(coalesce(po.productionSupervisorIdentifier, ''), 'APC_', ''))
      IN ['WN1','WN6','WT1','WT2']
  AND po.scheduledFinishDatetime IS NOT NULL
  AND toUpper(coalesce(po.cancelledIndicator, '')) <> 'Y'
  AND (po.systemStatusesText IS NULL
       OR (NOT toUpper(po.systemStatusesText) CONTAINS 'TECO'
           AND NOT toUpper(po.systemStatusesText) CONTAINS 'CLSD'))
  AND (po.actualFinishDate IS NULL
       OR po.actualFinishDate > po.scheduledFinishDatetime.truncate('day'))
RETURN count(*) AS missing_finish_date_count;


// ---------------------------------------------------------------------------
// Q10: Is there any orders exceeding MLT target last week?
// ---------------------------------------------------------------------------
// This is a complex query with holiday tables, business day calculation,
// formulation+packing lead time, and target comparison.
// Simplified approach: calendar days minus weekends (no holiday deduction
// since Cypher doesn't have built-in business-day functions).
// For exact parity, you'd need APOC or a holidays list.
// ---------------------------------------------------------------------------
// MLT Targets (embedded as a WITH list)
WITH [
  {mat:'CN04-050', mlt:15.5}, {mat:'110025941', mlt:15.5},
  {mat:'CN04-010', mlt:14.4}, {mat:'CN04-080', mlt:17.1},
  {mat:'110025954', mlt:17.1}, {mat:'CN08-160', mlt:15.4},
  {mat:'CN04-701', mlt:4.1},  {mat:'110022400', mlt:4.2},
  {mat:'CN09-200', mlt:7.4},  {mat:'CN09-218', mlt:4.2},
  {mat:'CN04-601', mlt:10.5}, {mat:'CN09-280', mlt:26.9},
  {mat:'110020809', mlt:26.9},{mat:'CN04-070', mlt:16.5},
  {mat:'CN08-170', mlt:16.5}, {mat:'CN04-015', mlt:5.3}
] AS targets
UNWIND targets AS t
// Packing orders from last week (confirmed, with actual start + LPB on batch)
MATCH (po:ProcessOrder)-[:EXECUTED_AT]->(:Plant {plantCode: 'CN20'})
WHERE po.orderReferenceRelativeWeekNumber = -1
  AND toUpper(replace(coalesce(po.productionSupervisorIdentifier, ''), 'APC_', ''))
      IN ['WN8','100','WT6','WT7','WN7','WT8']
  AND toUpper(coalesce(po.confirmedIndicator, '')) = 'Y'
  AND po.actualStartDatetime IS NOT NULL
  AND po.localMaterialCode IS NOT NULL
// Match batch to get LPB datetime
MATCH (b:Batch)-[:PRODUCED_BY]->(po)
WHERE b.lastGoodsReceiptEntryDatetime IS NOT NULL
// Join on material
WITH po, b, t
WHERE po.localMaterialCode = t.mat
// Calculate packing lead time in working days (approximate: total hours minus weekend hours)
WITH po, b, t,
     duration.between(po.actualStartDatetime, b.lastGoodsReceiptEntryDatetime) AS dur,
     duration.inDays(po.actualStartDatetime, b.lastGoodsReceiptEntryDatetime).days AS totalDays
WITH po, b, t, totalDays,
     // Approximate weekend days = 2 * (totalDays / 7)
     totalDays - 2 * (totalDays / 7) AS approxWorkingDays
// Check if exceeds MLT target
WHERE approxWorkingDays > t.mlt
RETURN po.processOrderNumber AS order_id,
       po.localMaterialCode AS material,
       approxWorkingDays AS actual_working_days,
       t.mlt AS mlt_target;

// NOTE: For exact working-day parity with holidays, use APOC date functions or
// pass holiday dates as parameters. The SQL uses Snowflake's DAYOFWEEKISO + a
// holiday VALUES table. The above is an approximation.


// ---------------------------------------------------------------------------
// Q11: List all batches of raw material expiring within 6 months
// ---------------------------------------------------------------------------
MATCH (b:Batch)-[:MANUFACTURED_AT]->(:Plant {plantCode: 'CN20'})
WHERE b.bestBeforeDate IS NOT NULL
  AND b.bestBeforeDate >= date()
  AND b.bestBeforeDate <= date() + duration({months: 6})
  AND b.totalQuantity > 0
  AND (b.exclusionFromAnalysis IS NULL OR b.exclusionFromAnalysis = 'N')
  AND (b.productLocationTypeCode IS NULL
       OR b.productLocationTypeCode = ''
       OR toUpper(b.productLocationTypeCode) IN [
            'API@FORM','APITL@FORM','BULK@MTOP','BULK@PS','BULKFIN@FS',
            'BULKSH@FS','BULKTL@FS','BULKTL@PS','BULKWIP@FS','RAW@FORM'
          ])
RETURN DISTINCT
  b.batchCode AS batch,
  b.localMaterialCode AS material_number,
  b.materialName AS material_description_en,
  b.productLocationTypeCode AS apo_product_loc_type,
  toString(b.bestBeforeDate) AS expiry_date,
  b.totalQuantity AS current_stock
ORDER BY b.bestBeforeDate;


// ---------------------------------------------------------------------------
// Q12: List all finish packs waiting for QA release
// ---------------------------------------------------------------------------
// Packing orders that are confirmed, have goods receipt, but no usage decision (A/R)
// ---------------------------------------------------------------------------
MATCH (po:ProcessOrder)-[:EXECUTED_AT]->(:Plant {plantCode: 'CN20'})
WHERE toLower(replace(coalesce(po.productionSupervisorIdentifier, ''), 'APC_', ''))
      IN ['wn8','100','wt6','wt7','wn7','wt8']
  AND toUpper(coalesce(po.confirmedIndicator, '')) = 'Y'
  AND toUpper(coalesce(po.cancelledIndicator, '')) <> 'Y'
MATCH (b:Batch {batchCode: po.batchCode, plantCode: 'CN20'})
WHERE b.lastGoodsReceiptEntryDatetime IS NOT NULL
  AND (b.usageDecisionCode IS NULL
       OR NOT toLower(b.usageDecisionCode) IN ['a','r'])
RETURN po.processOrderNumber AS process_order_id,
       b.usageDecisionCode AS UD,
       b.localMaterialCode AS materialnumber,
       b.batchCode AS batch,
       b.productFamilyName AS brand,
       b.lastGoodsReceiptEntryDatetime AS finish_pack_time
ORDER BY b.lastGoodsReceiptEntryDatetime DESC;


// ---------------------------------------------------------------------------
// Q14: List all "Seloken" inventory days on hand (finish pack, bulk, API)
// ---------------------------------------------------------------------------
// This requires consumption calculation (6-month window). Simplified version
// shows stock grouped by material. Full DOH needs consumption from OBR.
// ---------------------------------------------------------------------------
// Step 1: Stock by material for Seloken/Betaloc
MATCH (b:Batch)-[:MANUFACTURED_AT]->(:Plant {plantCode: 'CN20'})
WHERE toLower(b.productFamilyName) IN ['seloken','betaloc']
  AND toLower(coalesce(b.exclusionFromAnalysis, '')) <> 'y'
WITH b.localMaterialCode AS material_number,
     max(b.materialName) AS material_description,
     max(b.productLocationTypeCode) AS product_type,
     sum(coalesce(b.totalQuantity, 0.0)) AS stock_quantity,
     CASE WHEN max(b.baseUnitOfMeasure) = 'EA' THEN 'TAB'
          ELSE max(b.baseUnitOfMeasure) END AS unit_of_measure
RETURN material_number, material_description, product_type,
       stock_quantity, unit_of_measure
ORDER BY material_number;

// NOTE: For full inventory-days-on-hand, you need to calculate consumption
// from CONSUMED_BY relationships over a 6-month window and divide stock by
// avg daily consumption. That requires:
//   MATCH (b2:Batch)-[cb:CONSUMED_BY]->(po2:ProcessOrder)
//   WHERE cb.localMaterialCode = material_number
//     AND po2.plantCode = 'CN20'
//     AND po2.orderReferenceDate BETWEEN ... AND ...
//   WITH sum(cb.quantity) / 180.0 AS avg_daily_consumption
// Then: stock_quantity / avg_daily_consumption AS inventory_days_on_hand


// ---------------------------------------------------------------------------
// Q18: What is the average quality release lead time for this week?
// ---------------------------------------------------------------------------
// Lead time = (usageDecisionDatetime - lastGoodsReceiptEntryDatetime) in working days
// Working days approximation: total_hours - (weeks_diff * 48) then / 24
// ---------------------------------------------------------------------------
MATCH (po:ProcessOrder)-[:EXECUTED_AT]->(:Plant {plantCode: 'CN20'})
WHERE po.orderReferenceRelativeWeekNumber = 0
MATCH (b:Batch {batchCode: po.batchCode, plantCode: 'CN20'})
WHERE b.usageDecisionDatetime IS NOT NULL
  AND b.lastGoodsReceiptEntryDatetime IS NOT NULL
  AND b.usageDecisionDatetime > b.lastGoodsReceiptEntryDatetime
WITH duration.between(b.lastGoodsReceiptEntryDatetime, b.usageDecisionDatetime) AS d,
     duration.inDays(b.lastGoodsReceiptEntryDatetime, b.usageDecisionDatetime).days AS totalDays,
     duration.inSeconds(b.lastGoodsReceiptEntryDatetime, b.usageDecisionDatetime).hours AS totalHours,
     b.lastGoodsReceiptEntryDatetime AS lpb,
     b.usageDecisionDatetime AS qa
// Approximate working hours: subtract 48h per full weekend
WITH totalHours,
     duration.inDays(
       datetime.truncate('week', lpb),
       datetime.truncate('week', qa)
     ).days / 7 AS weekDiff
WITH (totalHours - weekDiff * 48) / 24.0 AS workingDays
RETURN round(avg(workingDays) * 10) / 10.0 AS avg_qa_release_lead_time_days;


// ---------------------------------------------------------------------------
// Q19: Average formulation lead time by brand for China market last week
// ---------------------------------------------------------------------------
// China market materials mapped to brands
WITH [
  {mat:'CNC9-280', brand:'Brilinta'},  {mat:'CNC9-278', brand:'Brilinta'},
  {mat:'CNC8-170', brand:'Nexium Oral Solid'}, {mat:'CNC8-160', brand:'Nexium Oral Solid'},
  {mat:'CNC4-092', brand:'Plendil'},   {mat:'CNC4-080', brand:'Plendil'},
  {mat:'CNC4-070', brand:'Plendil'},   {mat:'CNC4-050', brand:'Seloken'},
  {mat:'CNC4-010', brand:'Seloken'}
] AS materials
UNWIND materials AS cm
MATCH (po:ProcessOrder)-[:EXECUTED_AT]->(:Plant {plantCode: 'CN20'})
WHERE po.orderReferenceRelativeWeekNumber = -1
  AND toUpper(replace(coalesce(po.productionSupervisorIdentifier, ''), 'APC_', ''))
      IN ['WN1','WN6','WT1','WT2']
  AND toUpper(coalesce(po.confirmedIndicator, '')) = 'Y'
  AND po.actualStartDatetime IS NOT NULL
  AND (po.systemStatusesText IS NULL
       OR (NOT toUpper(po.systemStatusesText) CONTAINS 'TECO'
           AND NOT toUpper(po.systemStatusesText) CONTAINS 'CLSD'))
MATCH (b:Batch {batchCode: po.batchCode, plantCode: 'CN20'})
WHERE b.lastGoodsReceiptEntryDatetime IS NOT NULL
  // Trim leading zeros from localMaterialCode to match china_materials
  AND replace(b.localMaterialCode, '0', '') = replace(cm.mat, '0', '')
// Actually: use ltrim equivalent — Cypher doesn't have LTRIM for leading zeros.
// Better approach: exact match on the material code as stored.
// If codes are stored without leading zeros:
WITH cm, po, b
WHERE b.localMaterialCode = cm.mat
   OR po.localMaterialCode = cm.mat
WITH cm.brand AS brand,
     duration.inSeconds(po.actualStartDatetime, b.lastGoodsReceiptEntryDatetime).hours AS totalHours,
     duration.inDays(
       datetime.truncate('week', po.actualStartDatetime),
       datetime.truncate('week', b.lastGoodsReceiptEntryDatetime)
     ).days / 7 AS weekDiff
WITH brand,
     round(((totalHours - weekDiff * 48) / 24.0) * 10) / 10.0 AS leadTimeDays
RETURN brand,
       round(avg(leadTimeDays) * 10) / 10.0 AS avg_formulation_lead_time_workingday
ORDER BY brand;


// ---------------------------------------------------------------------------
// Q20: Batch MLT of last week by order
// ---------------------------------------------------------------------------
// Full MLT = formulation start → packing LPB, computed in working days.
// SQL uses ORDER_STATUS flat table (batch fields are on the order row),
// joins ORDER_BATCH_RELATIONSHIP for formulation orders, then deduplicates
// with ROW_NUMBER() per process_order_id.
//
// Graph mapping:
//   - Packing orders: ProcessOrder node has batchCode, productFamilyName,
//     lastGoodsReceiptEntryDatetime (mirrored from Batch), usageDecisionDatetime
//   - Formulation link: (consumedBatch)-[:CONSUMED_BY]->(packingOrder) from OBR
//     with relationshipType IN ['Consumption','Allocation','Reservation']
//     PLUS (packingOrder)-[:ADJUSTS]->(consumedBatch) for Adjustment rows
//   - Formulation order: (consumedBatch)-[:PRODUCED_BY]->(formulationOrder)
//     matched on consumedBatch.localMaterialCode = formulationOrder.localMaterialCode
// ---------------------------------------------------------------------------

// ── Packing orders (mirrors SQL packing_orders CTE) ──
// SQL reads from ORDER_STATUS flat table. In the graph, batch-level fields
// (lastGoodsReceiptEntryDatetime, productFamilyName) live on Batch nodes,
// NOT on ProcessOrder. We join Batch via batchCode (like SQL) rather than
// requiring a :PRODUCED_BY relationship (which may not exist for all orders).
MATCH (po:ProcessOrder)-[:EXECUTED_AT]->(:Plant {plantCode: 'CN20'})
WHERE po.orderReferenceRelativeWeekNumber >= -1
  AND toUpper(replace(coalesce(po.productionSupervisorIdentifier, ''), 'APC_', ''))
      IN ['WN8','100','WT6','WT7','WN7','WT8']
  AND toUpper(coalesce(po.confirmedIndicator, '')) = 'Y'
  AND po.actualStartDatetime IS NOT NULL
  AND po.batchCode IS NOT NULL
// Join Batch by batchCode + plantCode (mirrors SQL self-join on BATCH_CODE)
MATCH (b:Batch {batchCode: po.batchCode, plantCode: 'CN20'})
WHERE b.lastGoodsReceiptEntryDatetime IS NOT NULL

// ── Formulation orders via CONSUMED_BY (consumption/allocation/reservation) ──
// SQL joins ORDER_BATCH_RELATIONSHIP on CONSUMED_BATCH_CODE + CONSUMED_LOCAL_MATERIAL_CODE
OPTIONAL MATCH (consumedBatch:Batch)-[cb:CONSUMED_BY]->(po)
WHERE cb.relationshipType IN ['Consumption', 'Allocation', 'Reservation']
OPTIONAL MATCH (consumedBatch)-[:PRODUCED_BY]->(formOrd:ProcessOrder)
WHERE formOrd.plantCode = 'CN20'
  AND toUpper(replace(coalesce(formOrd.productionSupervisorIdentifier, ''), 'APC_', ''))
      IN ['WN1','WN6','WT1','WT2','WN5']

// ── Also check ADJUSTS relationships (SQL includes 'adjustment') ──
OPTIONAL MATCH (po)-[:ADJUSTS]->(adjBatch:Batch)
OPTIONAL MATCH (adjBatch)-[:PRODUCED_BY]->(adjFormOrd:ProcessOrder)
WHERE adjFormOrd.plantCode = 'CN20'
  AND toUpper(replace(coalesce(adjFormOrd.productionSupervisorIdentifier, ''), 'APC_', ''))
      IN ['WN1','WN6','WT1','WT2','WN5']

// ── Combine formulation starts from both paths ──
WITH po, b,
     po.batchCode AS batch,
     b.productFamilyName AS brand,
     po.localMaterialCode AS material,
     po.actualStartDatetime AS packingStart,
     b.lastGoodsReceiptEntryDatetime AS lpb,
     b.usageDecisionDatetime AS qaReleaseTime,
     CASE
       WHEN formOrd.actualStartDatetime IS NOT NULL AND adjFormOrd.actualStartDatetime IS NOT NULL
         THEN CASE WHEN formOrd.actualStartDatetime < adjFormOrd.actualStartDatetime
                   THEN formOrd.actualStartDatetime ELSE adjFormOrd.actualStartDatetime END
       WHEN formOrd.actualStartDatetime IS NOT NULL THEN formOrd.actualStartDatetime
       WHEN adjFormOrd.actualStartDatetime IS NOT NULL THEN adjFormOrd.actualStartDatetime
       ELSE null
     END AS formulationStart,
     // Formulation end = the consumed batch's LPB (= formulation order's goods receipt)
     // In SQL this is os.BATCH_LAST_GOODS_RECEIPT_ENTRY_DATETIME from the formulation order row
     // In the graph, this field lives on the Batch node (consumedBatch / adjBatch)
     CASE
       WHEN formOrd.actualStartDatetime IS NOT NULL THEN consumedBatch.lastGoodsReceiptEntryDatetime
       WHEN adjFormOrd.actualStartDatetime IS NOT NULL THEN adjBatch.lastGoodsReceiptEntryDatetime
       ELSE null
     END AS formulationEnd

// ── Aggregate per (po, batch) to get earliest formulation start ──
WITH po, batch, brand, material, packingStart, lpb, qaReleaseTime,
     min(formulationStart) AS formulationStart,
     min(formulationEnd) AS formulationEnd

// ── Compute segment hours (pack, formulation, warehouse, QA) ──
WITH po, batch, brand, material,
     // Packing: actual_start → LPB
     duration.inSeconds(packingStart, lpb).hours AS packRawHours,
     duration.inDays(packingStart, lpb).days AS packTotalDays,
     // Formulation: formulation_start → formulation_end
     CASE WHEN formulationStart IS NOT NULL AND formulationEnd IS NOT NULL
       THEN duration.inSeconds(formulationStart, formulationEnd).hours END AS formRawHours,
     CASE WHEN formulationStart IS NOT NULL AND formulationEnd IS NOT NULL
       THEN duration.inDays(formulationStart, formulationEnd).days END AS formTotalDays,
     // Warehouse: formulation_end → packing_start
     CASE WHEN formulationEnd IS NOT NULL AND formulationEnd < packingStart
       THEN duration.inSeconds(formulationEnd, packingStart).hours END AS whRawHours,
     CASE WHEN formulationEnd IS NOT NULL AND formulationEnd < packingStart
       THEN duration.inDays(formulationEnd, packingStart).days END AS whTotalDays,
     // QA: LPB → QA release
     CASE WHEN qaReleaseTime IS NOT NULL AND qaReleaseTime > lpb
       THEN duration.inSeconds(lpb, qaReleaseTime).hours END AS qaRawHours,
     CASE WHEN qaReleaseTime IS NOT NULL AND qaReleaseTime > lpb
       THEN duration.inDays(lpb, qaReleaseTime).days END AS qaTotalDays

// ── Approximate working days per segment (subtract weekends) ──
WITH po, batch, brand, material,
     round(toFloat(coalesce(packRawHours - 2 * (packTotalDays / 7) * 24, 0)) / 24.0 * 10) / 10.0 AS packingLeadTime,
     round(toFloat(coalesce(formRawHours - 2 * (formTotalDays / 7) * 24, 0)) / 24.0 * 10) / 10.0 AS formulationLeadTime,
     round(toFloat(coalesce(whRawHours - 2 * (whTotalDays / 7) * 24, 0)) / 24.0 * 10) / 10.0 AS warehouseTime,
     round(toFloat(coalesce(qaRawHours - 2 * (qaTotalDays / 7) * 24, 0)) / 24.0 * 10) / 10.0 AS qaLeadTime

WITH po, batch, brand, material,
     packingLeadTime, formulationLeadTime, warehouseTime, qaLeadTime,
     round((packingLeadTime + formulationLeadTime + warehouseTime + qaLeadTime) * 10) / 10.0 AS batchMLT

// ── Deduplicate: keep highest MLT per process_order_id (matches SQL ROW_NUMBER) ──
// SQL: ROW_NUMBER() OVER (PARTITION BY process_order_id ORDER BY batch_mlt DESC) WHERE rn = 1
WITH po.processOrderNumber AS order_id,
     batch, brand, material,
     packingLeadTime, formulationLeadTime, warehouseTime, qaLeadTime, batchMLT
ORDER BY batchMLT DESC
WITH order_id,
     collect({
       batch: batch, brand: brand, material: material,
       packingLeadTime: packingLeadTime, formulationLeadTime: formulationLeadTime,
       warehouseTime: warehouseTime, qaLeadTime: qaLeadTime, batchMLT: batchMLT
     }) AS rows
WITH order_id, rows[0] AS best

RETURN order_id,
       best.batch AS batch,
       best.brand AS brand,
       best.packingLeadTime AS packing_lead_time,
       best.formulationLeadTime AS formulation_lead_time,
       best.warehouseTime AS formulation_warehouse_time,
       best.qaLeadTime AS qa_release_lead_time,
       best.batchMLT AS batch_mlt
ORDER BY best.batchMLT DESC;


// ---------------------------------------------------------------------------
// Q21: Average formulation yield for Brilinta in 2026
// ---------------------------------------------------------------------------
WITH [
  {mat:'CNC9-280', target:0.9766},
  {mat:'CNC9-278', target:0.934}
] AS targets
UNWIND targets AS yt
MATCH (po:ProcessOrder)-[:EXECUTED_AT]->(:Plant {plantCode: 'CN20'})
WHERE po.localMaterialCode = yt.mat
  AND po.enteredGoodsReceivedQuantity IS NOT NULL
  AND po.totalOrderQuantity IS NOT NULL
  AND po.totalOrderQuantity > 0
  AND po.actualFinishDate IS NOT NULL
  AND po.actualFinishDate.year = 2026
  AND toUpper(coalesce(po.confirmedIndicator, '')) = 'Y'
  AND (po.systemStatusesText IS NULL
       OR (NOT toUpper(po.systemStatusesText) CONTAINS 'TECO'
           AND NOT toUpper(po.systemStatusesText) CONTAINS 'CLSD'))
  AND toUpper(replace(coalesce(po.productionSupervisorIdentifier, ''), 'APC_', ''))
      IN ['WN1','WN6','WT1','WT2']
WITH po.enteredGoodsReceivedQuantity / po.totalOrderQuantity AS orderYield,
     yt.target AS yieldTarget
RETURN 'Brilinta' AS brand,
       toString(round(avg(orderYield) * 10000) / 100.0) + '%' AS avg_formulation_yield,
       toString(round(avg(yieldTarget) * 10000) / 100.0) + '%' AS yield_target,
       toString(round((avg(orderYield) - avg(yieldTarget)) * 10000) / 100.0) + '%' AS delta_vs_target;


// ---------------------------------------------------------------------------
// Q22: Average lead time for Formulation Seroquel IR in last month
// ---------------------------------------------------------------------------
WITH date.truncate('month', date()) - duration({months: 1}) AS monthStart,
     date.truncate('month', date()) - duration({days: 1}) AS monthEnd
MATCH (po:ProcessOrder)-[:EXECUTED_AT]->(:Plant {plantCode: 'CN20'})
WHERE toUpper(replace(coalesce(po.productionSupervisorIdentifier, ''), 'APC_', ''))
      IN ['WN1','WN6','WT1','WT2']
  AND toUpper(coalesce(po.confirmedIndicator, '')) = 'Y'
  AND po.actualStartDatetime IS NOT NULL
MATCH (b:Batch {batchCode: po.batchCode, plantCode: 'CN20'})
WHERE toLower(b.productFamilyName) = 'seroquel ir'
  AND b.lastGoodsReceiptEntryDatetime IS NOT NULL
  AND b.lastGoodsReceiptEntryDatetime.truncate('day') >= monthStart
  AND b.lastGoodsReceiptEntryDatetime.truncate('day') <= monthEnd
WITH duration.inSeconds(po.actualStartDatetime, b.lastGoodsReceiptEntryDatetime).hours AS totalHours,
     duration.inDays(
       datetime.truncate('week', po.actualStartDatetime),
       datetime.truncate('week', b.lastGoodsReceiptEntryDatetime)
     ).days / 7 AS weekDiff
WITH round(((totalHours - weekDiff * 48) / 24.0) * 10) / 10.0 AS workingDays
RETURN count(*) AS row_count,
       round(avg(workingDays) * 10) / 10.0 AS avg_formulation_lead_time_workingday;


// ---------------------------------------------------------------------------
// Q23: Yield adherence of Formulation Brilinta from 2026-02-01 to 2026-02-28
// ---------------------------------------------------------------------------
WITH [
  {mat:'CNC9-280', target:0.9766},
  {mat:'CNC9-278', target:0.934}
] AS targets
UNWIND targets AS yt
MATCH (po:ProcessOrder)-[:EXECUTED_AT]->(:Plant {plantCode: 'CN20'})
WHERE po.localMaterialCode = yt.mat
  AND toUpper(coalesce(po.confirmedIndicator, '')) = 'Y'
  AND po.actualFinishDate IS NOT NULL
  AND po.actualFinishDate >= date('2026-02-01')
  AND po.actualFinishDate <= date('2026-02-28')
  AND toUpper(replace(coalesce(po.productionSupervisorIdentifier, ''), 'APC_', ''))
      IN ['WN1','WN6','WT1','WT2']
  AND po.enteredGoodsReceivedQuantity IS NOT NULL
  AND po.totalOrderQuantity IS NOT NULL
  AND po.totalOrderQuantity > 0
MATCH (b:Batch {batchCode: po.batchCode, plantCode: 'CN20'})
WHERE toLower(b.productFamilyName) = 'brilinta'
WITH po.enteredGoodsReceivedQuantity / po.totalOrderQuantity AS actualYield,
     yt.target AS yieldTarget
RETURN count(*) AS total_orders,
       count(CASE WHEN actualYield >= yieldTarget THEN 1 END) AS passed_orders,
       round(
         toFloat(count(CASE WHEN actualYield >= yieldTarget THEN 1 END))
         / toFloat(count(*)) * 10000
       ) / 100.0 AS pass_rate_percentage;


// ---------------------------------------------------------------------------
// Q25: Formulation process lead time for CNC9-280 in February 2026
// ---------------------------------------------------------------------------
MATCH (po:ProcessOrder)-[:EXECUTED_AT]->(:Plant {plantCode: 'CN20'})
WHERE po.localMaterialCode = 'CNC9-280'
  AND toUpper(coalesce(po.confirmedIndicator, '')) = 'Y'
  AND po.actualStartDatetime IS NOT NULL
MATCH (b:Batch {batchCode: po.batchCode, plantCode: 'CN20'})
WHERE b.lastGoodsReceiptEntryDatetime IS NOT NULL
  AND b.lastGoodsReceiptEntryDatetime.truncate('day') >= date('2026-02-01')
  AND b.lastGoodsReceiptEntryDatetime.truncate('day') <= date('2026-02-28')
WITH duration.inSeconds(po.actualStartDatetime, b.lastGoodsReceiptEntryDatetime).hours AS totalHours,
     duration.inDays(
       datetime.truncate('week', po.actualStartDatetime),
       datetime.truncate('week', b.lastGoodsReceiptEntryDatetime)
     ).days / 7 AS weekDiff
WITH round(((totalHours - weekDiff * 48) / 24.0) * 10) / 10.0 AS workingDays
RETURN avg(workingDays) AS avg_lead_time_working_days;


// ---------------------------------------------------------------------------
// Q27: How many hours did the last order delay in L13?
// ---------------------------------------------------------------------------
// Work centre code 'PL13', packing supervisors, confirmed, last order by LPB
// WorkCentre is a separate node: (po)-[:HAS_OPERATION]->(op)-[:USES_WORK_CENTRE]->(wc)
// But po also has workCentreCodesText which may contain the code.
// ---------------------------------------------------------------------------
MATCH (po:ProcessOrder)-[:EXECUTED_AT]->(:Plant {plantCode: 'CN20'})
WHERE toUpper(replace(coalesce(po.productionSupervisorIdentifier, ''), 'APC_', ''))
      IN ['WN8','100','WT6','WT7','WN7','WT8']
  AND toUpper(coalesce(po.confirmedIndicator, '')) = 'Y'
// Check work centre via operations
MATCH (po)-[:HAS_OPERATION]->(op:Operation)-[:USES_WORK_CENTRE]->(wc:WorkCentre {code: 'PL13'})
MATCH (b:Batch {batchCode: po.batchCode, plantCode: 'CN20'})
WHERE b.lastGoodsReceiptEntryDatetime IS NOT NULL
WITH po, b,
     duration.inSeconds(po.scheduledFinishDatetime, b.lastGoodsReceiptEntryDatetime).hours AS delay_in_hours
RETURN po.processOrderNumber AS order_id,
       po.scheduledFinishDatetime AS scheduled_finish,
       b.lastGoodsReceiptEntryDatetime AS last_goods_receipt,
       delay_in_hours
ORDER BY b.lastGoodsReceiptEntryDatetime DESC
LIMIT 1;

// Alternative using workCentreCodesText if the above doesn't match:
// MATCH (po:ProcessOrder)-[:EXECUTED_AT]->(:Plant {plantCode: 'CN20'})
// WHERE po.workCentreCodesText CONTAINS 'PL13'
//   AND ... (same filters)


// ---------------------------------------------------------------------------
// Q29: Overall lead time adherence of different brands for last week
// ---------------------------------------------------------------------------
// MLT target table + working-day calculation per order, then brand-level adherence
// ---------------------------------------------------------------------------
WITH [
  {mat:'CN04-050', mlt:15.5}, {mat:'110025941', mlt:15.5},
  {mat:'CN04-010', mlt:14.4}, {mat:'CN04-080', mlt:17.1},
  {mat:'110025954', mlt:17.1}, {mat:'CN08-160', mlt:15.4},
  {mat:'CN04-701', mlt:4.1},  {mat:'110022400', mlt:4.2},
  {mat:'CN09-200', mlt:7.4},  {mat:'CN09-218', mlt:4.2},
  {mat:'CN04-601', mlt:10.5}, {mat:'CN09-280', mlt:26.9},
  {mat:'110020809', mlt:26.9},{mat:'CN04-070', mlt:16.5},
  {mat:'CN08-170', mlt:16.5}, {mat:'CN04-015', mlt:5.3}
] AS targets
UNWIND targets AS t
MATCH (po:ProcessOrder)-[:EXECUTED_AT]->(:Plant {plantCode: 'CN20'})
WHERE po.orderReferenceRelativeWeekNumber = -1
  AND toUpper(coalesce(po.confirmedIndicator, '')) = 'Y'
  AND po.actualStartDatetime IS NOT NULL
  AND po.localMaterialCode = t.mat
MATCH (b:Batch {batchCode: po.batchCode, plantCode: 'CN20'})
WHERE b.lastGoodsReceiptEntryDatetime IS NOT NULL
WITH po, b, t,
     duration.inSeconds(po.actualStartDatetime, b.lastGoodsReceiptEntryDatetime).hours AS totalHours,
     duration.inDays(po.actualStartDatetime, b.lastGoodsReceiptEntryDatetime).days AS totalDays
WITH po, b, t,
     // Approximate working days: subtract weekends
     round(((totalHours - 2 * (totalDays / 7) * 24) / 24.0) * 10) / 10.0 AS actualLeadTime,
     t.mlt AS mltTarget,
     b.productFamilyName AS brand
WHERE mltTarget IS NOT NULL
WITH brand,
     count(*) AS total_orders,
     sum(CASE WHEN actualLeadTime <= mltTarget THEN 1 ELSE 0 END) AS hit_target_orders
RETURN brand,
       total_orders AS number_of_orders,
       hit_target_orders AS number_of_hit_target,
       round(toFloat(hit_target_orders) / toFloat(total_orders) * 10000) / 100.0
         AS overall_lead_time_adherence_percentage
ORDER BY overall_lead_time_adherence_percentage DESC;

"""
Load Manufacturing CSV Data into Neo4j Graph
=============================================
Maps CSV columns from batch_status, order_status, and order_batch_relationship
to the MIA Ontology classes and relationships.

Usage:
    python load_csv_to_neo4j.py --uri neo4j://127.0.0.1:7687 --user neo4j --password <pwd>

Requires:
    pip install neo4j
"""

import argparse
import csv
import os
import sys
import time
from neo4j import GraphDatabase

# ── Configuration ─────────────────────────────────────────────────────
BATCH_SIZE = 1000  # rows per UNWIND transaction
FOLDER = os.path.join(os.path.dirname(__file__), "FOLDER")

# Auto-detect CSV files in FOLDER
def find_csv(prefix):
    for f in os.listdir(FOLDER):
        if f.startswith(prefix) and f.endswith(".csv"):
            return os.path.join(FOLDER, f)
    return None


# ── Helpers ───────────────────────────────────────────────────────────

def read_csv(path):
    """Read CSV and yield dicts, stripping whitespace from values."""
    with open(path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield {k: (v.strip() if v else "") for k, v in row.items()}


def split_multi(value):
    """Split comma-separated text field into a list of trimmed strings."""
    if not value:
        return []
    return [v.strip() for v in value.split(",") if v.strip()]


def safe_float(v):
    try:
        return float(v) if v else None
    except (ValueError, TypeError):
        return None


def safe_int(v):
    try:
        return int(v) if v else None
    except (ValueError, TypeError):
        return None


def run_batched(session, cypher, rows, label=""):
    """Execute cypher via UNWIND in batches."""
    batch = []
    total = 0
    for row in rows:
        batch.append(row)
        if len(batch) >= BATCH_SIZE:
            session.run(cypher, {"rows": batch})
            total += len(batch)
            batch = []
    if batch:
        session.run(cypher, {"rows": batch})
        total += len(batch)
    print(f"  {label}: {total:,} rows processed")
    return total


# ── Constraints & Indexes (from ontology) ─────────────────────────────

CONSTRAINTS = [
    "CREATE CONSTRAINT batch_unique IF NOT EXISTS FOR (b:Batch) REQUIRE (b.batchCode, b.plantCode) IS UNIQUE",
    "CREATE CONSTRAINT material_unique IF NOT EXISTS FOR (m:Material) REQUIRE m.localMaterialCode IS UNIQUE",
    "CREATE CONSTRAINT plant_unique IF NOT EXISTS FOR (p:Plant) REQUIRE p.plantCode IS UNIQUE",
    "CREATE CONSTRAINT process_order_unique IF NOT EXISTS FOR (po:ProcessOrder) REQUIRE po.processOrderNumber IS UNIQUE",
    "CREATE CONSTRAINT product_family_unique IF NOT EXISTS FOR (pf:ProductFamily) REQUIRE pf.name IS UNIQUE",
    "CREATE CONSTRAINT product_sub_family_unique IF NOT EXISTS FOR (psf:ProductSubFamily) REQUIRE psf.name IS UNIQUE",
    "CREATE CONSTRAINT storage_location_unique IF NOT EXISTS FOR (sl:StorageLocation) REQUIRE (sl.code, sl.plantCode) IS UNIQUE",
    "CREATE CONSTRAINT inspection_lot_unique IF NOT EXISTS FOR (il:InspectionLot) REQUIRE il.referenceNumber IS UNIQUE",
    "CREATE CONSTRAINT source_system_unique IF NOT EXISTS FOR (ss:SourceSystem) REQUIRE ss.name IS UNIQUE",
    "CREATE CONSTRAINT work_centre_unique IF NOT EXISTS FOR (wc:WorkCentre) REQUIRE wc.code IS UNIQUE",
    "CREATE CONSTRAINT operation_unique IF NOT EXISTS FOR (op:Operation) REQUIRE (op.processOrderNumber, op.operationCode) IS UNIQUE",
    "CREATE CONSTRAINT vendor_unique IF NOT EXISTS FOR (v:Vendor) REQUIRE v.accountNumber IS UNIQUE",
    "CREATE CONSTRAINT planned_order_unique IF NOT EXISTS FOR (plo:PlannedOrder) REQUIRE plo.plannedOrderNumber IS UNIQUE",
    "CREATE CONSTRAINT quality_event_unique IF NOT EXISTS FOR (qe:QualityEvent) REQUIRE qe.identifier IS UNIQUE",
    "CREATE CONSTRAINT lims_lot_unique IF NOT EXISTS FOR (ll:LIMSLot) REQUIRE ll.lotNumber IS UNIQUE",
    "CREATE CONSTRAINT quality_notification_unique IF NOT EXISTS FOR (qn:QualityNotification) REQUIRE qn.identifier IS UNIQUE",
]

INDEXES = [
    "CREATE INDEX batch_material_idx IF NOT EXISTS FOR (b:Batch) ON (b.localMaterialCode)",
    "CREATE INDEX batch_status_idx IF NOT EXISTS FOR (b:Batch) ON (b.statusCode)",
    "CREATE INDEX order_plant_idx IF NOT EXISTS FOR (po:ProcessOrder) ON (po.plantCode)",
    "CREATE INDEX order_type_idx IF NOT EXISTS FOR (po:ProcessOrder) ON (po.orderTypeCode)",
    "CREATE INDEX material_global_idx IF NOT EXISTS FOR (m:Material) ON (m.globalMaterialCode)",
    "CREATE INDEX material_name_idx IF NOT EXISTS FOR (m:Material) ON (m.materialName)",
]


# ══════════════════════════════════════════════════════════════════════
# PHASE 1: BATCH_STATUS CSV → Nodes & Relationships
# ══════════════════════════════════════════════════════════════════════

def transform_batch_status(row):
    """Transform a batch_status CSV row into params for Cypher."""
    return {
        # Batch (def-ops:Batch)
        "batchCode": row.get("BATCH_CODE", ""),
        "plantCode": row.get("PLANT_CODE", ""),
        "batchRecordIdentifier": row.get("BATCH_RECORD_IDENTIFIER", ""),
        "batchStatusCode": row.get("BATCH_STATUS_CODE", ""),
        "batchCreationDate": row.get("BATCH_CREATION_DATE", "") or None,
        "plantLevelBatchCreationDate": row.get("PLANT_LEVEL_BATCH_CREATION_DATE", "") or None,
        "manufactureDate": row.get("MANUFACTURE_DATE", "") or None,
        "availabilityDate": row.get("AVAILABILITY_DATE", "") or None,
        "bestBeforeDate": row.get("BEST_BEFORE_DATE", "") or None,
        "lastChangeDate": row.get("LAST_CHANGE_DATE", "") or None,
        "lastGoodsReceiptDate": row.get("LAST_GOODS_RECEIPT_DATE", "") or None,
        "plantLevelLastGoodsReceiptDate": row.get("PLANT_LEVEL_LAST_GOODS_RECEIPT_DATE", "") or None,
        "batchTotalQuantity": safe_float(row.get("BATCH_TOTAL_QUANTITY", "")),
        "baseUnitOfMeasureCode": row.get("BASE_UNIT_OF_MEASURE_CODE", ""),
        "deletionIndicator": row.get("DELETION_INDICATOR", ""),
        "restrictedUseStockIndicator": row.get("BATCH_IN_RESTRICTED_USE_STOCK_INDICATOR", ""),
        "vendorBatchCode": row.get("VENDOR_BATCH_CODE", ""),
        "countryOfOrigin": row.get("COUNTRY_OF_ORIGIN_COUNTRY_CODE", ""),
        "shelfLifePeriodNumber": safe_int(row.get("SHELF_LIFE_PERIOD_NUMBER", "")),
        "shelfLifeUnit": row.get("SHELF_LIFE_PERIOD_UNIT_OF_MEASURE_DESCRIPTION", ""),
        "batchExclusionIndicator": row.get("BATCH_EXCLUSION_FROM_ANALYSIS_INDICATOR", ""),
        "stockStatusesText": row.get("STOCK_STATUSES_TEXT", ""),
        "storageLocationCodesText": row.get("STORAGE_LOCATION_CODES_TEXT", ""),
        "marketsText": row.get("MARKETS_TEXT", ""),
        "roundingRuleDescription": row.get("ROUNDING_RULE_DESCRIPTION", ""),
        "lotSizeCode": row.get("LOT_SIZE_CODE", ""),
        "erpMinimumLotSizeQuantity": safe_float(row.get("ERP_MINIMUM_LOT_SIZE_QUANTITY", "")),
        "erpMaximumLotSizeQuantity": safe_float(row.get("ERP_MAXIMUM_LOT_SIZE_QUANTITY", "")),
        "apoMinimumLotSizeQuantity": safe_float(row.get("APO_MINIMUM_LOT_SIZE_QUANTITY", "")),
        "apoMaximumLotSizeQuantity": safe_float(row.get("APO_MAXIMUM_LOT_SIZE_QUANTITY", "")),
        "erpGoodsReceiptProcessingDays": safe_int(row.get("ERP_GOODS_RECEIPT_PROCESSING_DAYS_NUMBER", "")),
        "apoGoodsIssueProcessingDays": safe_int(row.get("APO_GOODS_ISSUE_PROCESSING_DAYS_NUMBER", "")),
        "apoGoodsReceiptProcessingDays": safe_int(row.get("APO_GOODS_RECEIPT_PROCESSING_DAYS_NUMBER", "")),
        "supplyNetworkPlannerCode": row.get("SUPPLY_NETWORK_PLANNER_CODE", ""),
        "globalSupplyPlannerName": row.get("GLOBAL_SUPPLY_PLANNER_NAME", ""),
        "materialAuthorisationGroupDescription": row.get("MATERIAL_AUTHORISATION_GROUP_DESCRIPTION", ""),
        "purchasingGroupCode": row.get("PURCHASING_GROUP_CODE", ""),
        "profitCentreCode": row.get("PROFIT_CENTRE_CODE", ""),
        "segmentCode": row.get("SEGMENT_CODE", ""),
        "planningTechniqueCode": row.get("PLANNING_TECHNIQUE_CODE", ""),
        "plantSpecificMaterialStatusName": row.get("PLANT_SPECIFIC_MATERIAL_STATUS_NAME", ""),
        "mrpTypeDescription": row.get("MRP_TYPE_DESCRIPTION", ""),
        "formulationPlantCode": row.get("FORMULATION_PLANT_CODE", ""),
        "packingPlantCode": row.get("PACKING_PLANT_CODE", ""),

        # Batch lifecycle timestamps
        "batchLastGREntryDt": row.get("BATCH_LAST_GOODS_RECEIPT_ENTRY_DATETIME", "") or None,
        "batchLastGRPostingDt": row.get("BATCH_LAST_GOODS_RECEIPT_POSTING_DATETIME", "") or None,
        "batchSamplingEntryDt": row.get("BATCH_SAMPLING_ENTRY_DATETIME", "") or None,
        "batchSamplingPostingDt": row.get("BATCH_SAMPLING_POSTING_DATETIME", "") or None,
        "batchReleaseEntryDt": row.get("BATCH_RELEASE_ENTRY_DATETIME", "") or None,
        "batchReleasePostingDt": row.get("BATCH_RELEASE_POSTING_DATETIME", "") or None,
        "batchGoodsIssueEntryDt": row.get("BATCH_GOODS_ISSUE_ENTRY_DATETIME", "") or None,
        "batchGoodsIssuePostingDt": row.get("BATCH_GOODS_ISSUE_POSTING_DATETIME", "") or None,
        "batchPickEntryDt": row.get("BATCH_PICK_ENTRY_DATETIME", "") or None,
        "batchPickPostingDt": row.get("BATCH_PICK_POSTING_DATETIME", "") or None,

        # Material (def-ops:Material)
        "localMaterialCode": row.get("LOCAL_MATERIAL_CODE", ""),
        "globalMaterialCode": row.get("GLOBAL_MATERIAL_CODE", ""),
        "cleanedLocalMaterialCode": row.get("CLEANED_LOCAL_MATERIAL_CODE", ""),
        "materialName": row.get("MATERIAL_NAME", ""),
        "materialTypeCode": row.get("MATERIAL_TYPE_CODE", ""),
        "materialTypeName": row.get("MATERIAL_TYPE_NAME", ""),
        "materialGroupName": row.get("MATERIAL_GROUP_NAME", ""),
        "materialIdentifier": row.get("MATERIAL_IDENTIFIER", ""),
        "strengthText": row.get("STRENGTH_TEXT", ""),
        "procurementTypeCode": row.get("PROCUREMENT_TYPE_CODE", ""),
        "procurementTypeName": row.get("PROCUREMENT_TYPE_NAME", ""),

        # Plant
        "productLocationTypeCode": row.get("PRODUCT_LOCATION_TYPE_CODE", ""),
        "productLocationTypeName": row.get("PRODUCT_LOCATION_TYPE_NAME", ""),

        # Product hierarchy
        "productFamilyName": row.get("PRODUCT_FAMILY_NAME", ""),
        "productSubFamilyName": row.get("PRODUCT_SUB_FAMILY_NAME", ""),

        # Storage location
        "storageLocationCode": row.get("STORAGE_LOCATION_CODE", ""),

        # Inspection lot
        "referenceInspectionLotNumber": row.get("REFERENCE_INSPECTION_LOT_NUMBER", ""),
        "inspectionTypeCode": row.get("INSPECTION_TYPE_CODE", ""),
        "plannedInspectionLotQuantity": safe_float(row.get("PLANNED_INSPECTION_LOT_QUANTITY", "")),
        "inspectionLotCreationDatetime": row.get("INSPECTION_LOT_CREATION_DATETIME", "") or None,
        "recordCreationDatetime": row.get("RECORD_CREATION_DATETIME", "") or None,
        "inspectionLotOriginText": row.get("INSPECTION_LOT_ORIGIN_TEXT", ""),
        "usageDecisionCode": row.get("USAGE_DECISION_CODE", ""),
        "usageDecisionDatetime": row.get("USAGE_DECISION_DATETIME", "") or None,
        "expectedUsageDecisionDate": row.get("EXPECTED_USAGE_DECISION_DATE", "") or None,
        "averageInspectionDuration": safe_float(row.get("AVERAGE_INSPECTION_DURATION_NUMBER", "")),
        "goodsReceiptProcessingTimeInDays": safe_int(row.get("GOODS_RECEIPT_PROCESSING_TIME_IN_DAYS_NUMBER", "")),
        "originalFullReleaseDate": row.get("ORIGINAL_FULL_RELEASE_DATE", "") or None,
        "expectedGoodsReceiptFinishDate": row.get("EXPECTED_GOODS_RECEIPT_FINISH_DATE", "") or None,
        "processOrderActualFinishDate": row.get("PROCESS_ORDER_ACTUAL_FINISH_DATE", "") or None,
        "processOrderScheduledFinishDate": row.get("PROCESS_ORDER_SCHEDULED_FINISH_DATE", "") or None,
        "keyCharacteristicsText": row.get("KEY_CHARACTERISTICS_TEXT", ""),
        "keyCharacteristicsResultsText": row.get("KEY_CHARACTERISTICS_RESULTS_TEXT", ""),
        "validInspectionLotNumbersText": row.get("VALID_INSPECTION_LOT_NUMBERS_TEXT", ""),

        # Vendor
        "vendorAccountNumber": row.get("VENDOR_ACCOUNT_NUMBER", ""),

        # Process order (from batch_status)
        "processOrderNumber": row.get("PROCESS_ORDER_NUMBER", ""),
        "purchaseOrderNumber": row.get("PURCHASE_ORDER_NUMBER", ""),
        "purchaseOrderItemNumber": row.get("PURCHASE_ORDER_ITEM_NUMBER", ""),

        # LIMS Lot
        "limsLotNumber": row.get("LIMS_LOT_NUMBER", ""),
        "limsLotName": row.get("LIMS_LOT_NAME", ""),
        "limsDispositionCode": row.get("LIMS_DISPOSITION_CODE", ""),
        "limsDispositionDatetime": row.get("LIMS_DISPOSITION_DATETIME", "") or None,
        "limsSamplesText": row.get("LIMS_SAMPLES_TEXT", ""),
        "limsSamplesStatusesText": row.get("LIMS_SAMPLES_STATUSES_TEXT", ""),
        "limsSampleRecordDatetime": row.get("LIMS_SAMPLE_RECORD_DATETIME", "") or None,
        "limsTotalTestsCount": safe_int(row.get("LIMS_TOTAL_TESTS_COUNT", "")),
        "limsFinishedTestsCount": safe_int(row.get("LIMS_FINISHED_TESTS_COUNT", "")),

        # Quality events (multi-value)
        "qualityEventIdentifiersText": row.get("QUALITY_EVENT_IDENTIFIERS_TEXT", ""),
        "qualityEventTypeCodesText": row.get("QUALITY_EVENT_TYPE_CODES_TEXT", ""),
        "lifecycleStateCodesText": row.get("LIFECYCLE_STATE_CODES_TEXT", ""),

        # Quality notifications (multi-value)
        "qualityNotificationsText": row.get("QUALITY_NOTIFICATIONS_TEXT", ""),
        "qualityNotificationsTypeCodesText": row.get("QUALITY_NOTIFICATIONS_TYPE_CODES_TEXT", ""),
        "qualityNotificationsSystemStatusesText": row.get("QUALITY_NOTIFICATIONS_SYSTEM_STATUSES_TEXT", ""),
        "qualityNotificationsUserStatusesText": row.get("QUALITY_NOTIFICATIONS_USER_STATUSES_TEXT", ""),

        # Source system
        "srcSysNm": row.get("SRC_SYS_NM", ""),
        "srcSysId": row.get("SRC_SYS_ID", ""),
        "etlCreTs": row.get("ETL_CRE_TS", "") or None,
        "etlUpdtTs": row.get("ETL_UPDT_TS", "") or None,
    }


# ── BATCH_STATUS: Node creation queries ──────────────────────────────

BATCH_NODE_CYPHER = """
UNWIND $rows AS r
MERGE (b:Batch {batchCode: r.batchCode, plantCode: r.plantCode})
SET b.batchRecordIdentifier           = r.batchRecordIdentifier,
    b.statusCode                      = r.batchStatusCode,
    b.localMaterialCode               = r.localMaterialCode,
    b.globalMaterialCode              = r.globalMaterialCode,
    b.materialName                    = r.materialName,
    b.batchCreationDate               = CASE WHEN r.batchCreationDate IS NOT NULL THEN date(r.batchCreationDate) END,
    b.plantLevelBatchCreationDate     = CASE WHEN r.plantLevelBatchCreationDate IS NOT NULL THEN date(r.plantLevelBatchCreationDate) END,
    b.manufactureDate                 = CASE WHEN r.manufactureDate IS NOT NULL THEN date(r.manufactureDate) END,
    b.availabilityDate                = CASE WHEN r.availabilityDate IS NOT NULL THEN date(r.availabilityDate) END,
    b.bestBeforeDate                  = CASE WHEN r.bestBeforeDate IS NOT NULL THEN date(r.bestBeforeDate) END,
    b.lastChangeDate                  = CASE WHEN r.lastChangeDate IS NOT NULL THEN date(r.lastChangeDate) END,
    b.lastGoodsReceiptDate            = CASE WHEN r.lastGoodsReceiptDate IS NOT NULL THEN date(r.lastGoodsReceiptDate) END,
    b.plantLevelLastGoodsReceiptDate  = CASE WHEN r.plantLevelLastGoodsReceiptDate IS NOT NULL THEN date(r.plantLevelLastGoodsReceiptDate) END,
    b.totalQuantity                   = r.batchTotalQuantity,
    b.baseUnitOfMeasure               = r.baseUnitOfMeasureCode,
    b.deletionIndicator               = r.deletionIndicator,
    b.restrictedUseStockIndicator     = r.restrictedUseStockIndicator,
    b.exclusionFromAnalysis           = r.batchExclusionIndicator,
    b.vendorBatchCode                 = r.vendorBatchCode,
    b.countryOfOrigin                 = r.countryOfOrigin,
    b.shelfLifePeriod                 = r.shelfLifePeriodNumber,
    b.shelfLifeUnit                   = r.shelfLifeUnit,
    b.stockStatusesText               = r.stockStatusesText,
    b.storageLocationCodesText        = r.storageLocationCodesText,
    b.marketsText                     = r.marketsText,
    b.roundingRuleDescription         = r.roundingRuleDescription,
    b.lotSizeCode                     = r.lotSizeCode,
    b.erpMinimumLotSizeQuantity       = r.erpMinimumLotSizeQuantity,
    b.erpMaximumLotSizeQuantity       = r.erpMaximumLotSizeQuantity,
    b.apoMinimumLotSizeQuantity       = r.apoMinimumLotSizeQuantity,
    b.apoMaximumLotSizeQuantity       = r.apoMaximumLotSizeQuantity,
    b.erpGoodsReceiptProcessingDays   = r.erpGoodsReceiptProcessingDays,
    b.apoGoodsIssueProcessingDays     = r.apoGoodsIssueProcessingDays,
    b.apoGoodsReceiptProcessingDays   = r.apoGoodsReceiptProcessingDays,
    b.supplyNetworkPlannerCode        = r.supplyNetworkPlannerCode,
    b.globalSupplyPlannerName         = r.globalSupplyPlannerName,
    b.materialAuthorisationGroupDesc  = r.materialAuthorisationGroupDescription,
    b.purchasingGroupCode             = r.purchasingGroupCode,
    b.profitCentreCode                = r.profitCentreCode,
    b.segmentCode                     = r.segmentCode,
    b.planningTechniqueCode           = r.planningTechniqueCode,
    b.plantSpecificMaterialStatus     = r.plantSpecificMaterialStatusName,
    b.mrpTypeDescription              = r.mrpTypeDescription,
    b.formulationPlantCode            = r.formulationPlantCode,
    b.packingPlantCode                = r.packingPlantCode,
    b.processOrderNumber              = r.processOrderNumber,
    b.purchaseOrderNumber             = r.purchaseOrderNumber,
    b.purchaseOrderItemNumber         = r.purchaseOrderItemNumber,
    b.productLocationTypeCode         = r.productLocationTypeCode,
    b.productLocationTypeName         = r.productLocationTypeName,
    b.procurementTypeCode             = r.procurementTypeCode,
    b.procurementTypeName             = r.procurementTypeName,
    b.productFamilyName               = r.productFamilyName,
    b.productSubFamilyName            = r.productSubFamilyName,
    b.inspectionTypeCode              = r.inspectionTypeCode,
    b.usageDecisionCode               = r.usageDecisionCode,
    b.usageDecisionDatetime           = CASE WHEN r.usageDecisionDatetime IS NOT NULL THEN datetime(replace(r.usageDecisionDatetime, ' ', 'T')) END,
    b.expectedUsageDecisionDate       = CASE WHEN r.expectedUsageDecisionDate IS NOT NULL THEN date(r.expectedUsageDecisionDate) END,
    b.averageInspectionDuration       = r.averageInspectionDuration,
    b.goodsReceiptProcessingTimeInDays = r.goodsReceiptProcessingTimeInDays,
    b.originalFullReleaseDate         = CASE WHEN r.originalFullReleaseDate IS NOT NULL THEN date(r.originalFullReleaseDate) END,
    b.expectedGoodsReceiptFinishDate  = CASE WHEN r.expectedGoodsReceiptFinishDate IS NOT NULL THEN date(r.expectedGoodsReceiptFinishDate) END,
    b.processOrderActualFinishDate    = CASE WHEN r.processOrderActualFinishDate IS NOT NULL THEN date(r.processOrderActualFinishDate) END,
    b.processOrderScheduledFinishDate = CASE WHEN r.processOrderScheduledFinishDate IS NOT NULL THEN date(r.processOrderScheduledFinishDate) END,
    b.keyCharacteristicsText          = r.keyCharacteristicsText,
    b.keyCharacteristicsResultsText   = r.keyCharacteristicsResultsText,
    b.validInspectionLotNumbersText   = r.validInspectionLotNumbersText,
    b.qualityEventIdentifiersText     = r.qualityEventIdentifiersText,
    b.qualityEventTypeCodesText       = r.qualityEventTypeCodesText,
    b.lifecycleStateCodesText         = r.lifecycleStateCodesText,
    b.qualityNotificationsText        = r.qualityNotificationsText,
    b.qualityNotificationsTypeCodesText = r.qualityNotificationsTypeCodesText,
    b.qualityNotificationsSystemStatusesText = r.qualityNotificationsSystemStatusesText,
    b.qualityNotificationsUserStatusesText   = r.qualityNotificationsUserStatusesText,
    b.limsSamplesText                 = r.limsSamplesText,
    b.limsSamplesStatusesText         = r.limsSamplesStatusesText,
    b.samplingEntryDatetime           = CASE WHEN r.batchSamplingEntryDt IS NOT NULL THEN datetime(replace(r.batchSamplingEntryDt, ' ', 'T')) END,
    b.samplingPostingDatetime         = CASE WHEN r.batchSamplingPostingDt IS NOT NULL THEN datetime(replace(r.batchSamplingPostingDt, ' ', 'T')) END,
    b.releaseEntryDatetime            = CASE WHEN r.batchReleaseEntryDt IS NOT NULL THEN datetime(replace(r.batchReleaseEntryDt, ' ', 'T')) END,
    b.releasePostingDatetime          = CASE WHEN r.batchReleasePostingDt IS NOT NULL THEN datetime(replace(r.batchReleasePostingDt, ' ', 'T')) END,
    b.goodsIssueEntryDatetime         = CASE WHEN r.batchGoodsIssueEntryDt IS NOT NULL THEN datetime(replace(r.batchGoodsIssueEntryDt, ' ', 'T')) END,
    b.goodsIssuePostingDatetime       = CASE WHEN r.batchGoodsIssuePostingDt IS NOT NULL THEN datetime(replace(r.batchGoodsIssuePostingDt, ' ', 'T')) END,
    b.pickEntryDatetime               = CASE WHEN r.batchPickEntryDt IS NOT NULL THEN datetime(replace(r.batchPickEntryDt, ' ', 'T')) END,
    b.pickPostingDatetime             = CASE WHEN r.batchPickPostingDt IS NOT NULL THEN datetime(replace(r.batchPickPostingDt, ' ', 'T')) END,
    b.lastGoodsReceiptEntryDatetime   = CASE WHEN r.batchLastGREntryDt IS NOT NULL THEN datetime(replace(r.batchLastGREntryDt, ' ', 'T')) END,
    b.lastGoodsReceiptPostingDatetime = CASE WHEN r.batchLastGRPostingDt IS NOT NULL THEN datetime(replace(r.batchLastGRPostingDt, ' ', 'T')) END,
    b.etlCreatedDatetime              = CASE WHEN r.etlCreTs IS NOT NULL THEN datetime(replace(r.etlCreTs, ' ', 'T')) END,
    b.etlUpdatedDatetime              = CASE WHEN r.etlUpdtTs IS NOT NULL THEN datetime(replace(r.etlUpdtTs, ' ', 'T')) END
"""

MATERIAL_NODE_CYPHER = """
UNWIND $rows AS r
WITH r WHERE r.localMaterialCode <> ''
MERGE (m:Material {localMaterialCode: r.localMaterialCode})
SET m.globalMaterialCode    = r.globalMaterialCode,
    m.cleanedLocalCode      = r.cleanedLocalMaterialCode,
    m.materialName          = r.materialName,
    m.materialTypeCode      = r.materialTypeCode,
    m.materialTypeName      = r.materialTypeName,
    m.materialGroupName     = r.materialGroupName,
    m.materialIdentifier    = r.materialIdentifier,
    m.strengthText          = r.strengthText,
    m.baseUnitOfMeasure     = r.baseUnitOfMeasureCode,
    m.procurementTypeCode   = r.procurementTypeCode,
    m.procurementTypeName   = r.procurementTypeName
"""

PLANT_NODE_CYPHER = """
UNWIND $rows AS r
WITH r WHERE r.plantCode <> ''
MERGE (p:Plant {plantCode: r.plantCode})
SET p.productLocationTypeCode = r.productLocationTypeCode,
    p.productLocationTypeName = r.productLocationTypeName
"""

PRODUCT_FAMILY_CYPHER = """
UNWIND $rows AS r
WITH r WHERE r.productFamilyName <> ''
MERGE (pf:ProductFamily {name: r.productFamilyName})
"""

PRODUCT_SUB_FAMILY_CYPHER = """
UNWIND $rows AS r
WITH r WHERE r.productSubFamilyName <> ''
MERGE (psf:ProductSubFamily {name: r.productSubFamilyName})
"""

STORAGE_LOCATION_CYPHER = """
UNWIND $rows AS r
WITH r WHERE r.storageLocationCode <> '' AND r.plantCode <> ''
MERGE (sl:StorageLocation {code: r.storageLocationCode, plantCode: r.plantCode})
"""

INSPECTION_LOT_CYPHER = """
UNWIND $rows AS r
WITH r WHERE r.referenceInspectionLotNumber <> ''
MERGE (il:InspectionLot {referenceNumber: r.referenceInspectionLotNumber})
SET il.inspectionTypeCode    = r.inspectionTypeCode,
    il.plannedQuantity       = r.plannedInspectionLotQuantity,
    il.creationDatetime      = CASE WHEN r.inspectionLotCreationDatetime IS NOT NULL THEN datetime(replace(r.inspectionLotCreationDatetime, ' ', 'T')) END,
    il.recordCreationDatetime = CASE WHEN r.recordCreationDatetime IS NOT NULL THEN datetime(replace(r.recordCreationDatetime, ' ', 'T')) END,
    il.originText            = r.inspectionLotOriginText,
    il.usageDecisionCode     = r.usageDecisionCode,
    il.usageDecisionDatetime = CASE WHEN r.usageDecisionDatetime IS NOT NULL THEN datetime(replace(r.usageDecisionDatetime, ' ', 'T')) END,
    il.expectedUsageDecisionDate = CASE WHEN r.expectedUsageDecisionDate IS NOT NULL THEN date(r.expectedUsageDecisionDate) END,
    il.storageLocationCode   = r.storageLocationCode
"""

SOURCE_SYSTEM_CYPHER = """
UNWIND $rows AS r
WITH r WHERE r.srcSysNm <> ''
MERGE (ss:SourceSystem {name: r.srcSysNm})
SET ss.systemId = r.srcSysId
"""

VENDOR_CYPHER = """
UNWIND $rows AS r
WITH r WHERE r.vendorAccountNumber <> ''
MERGE (v:Vendor {accountNumber: r.vendorAccountNumber})
"""

LIMS_LOT_CYPHER = """
UNWIND $rows AS r
WITH r WHERE r.limsLotNumber <> ''
MERGE (ll:LIMSLot {lotNumber: r.limsLotNumber})
SET ll.lotName            = r.limsLotName,
    ll.dispositionCode    = r.limsDispositionCode,
    ll.dispositionDatetime = CASE WHEN r.limsDispositionDatetime IS NOT NULL THEN datetime(replace(r.limsDispositionDatetime, ' ', 'T')) END,
    ll.totalTestsCount    = r.limsTotalTestsCount,
    ll.finishedTestsCount = r.limsFinishedTestsCount,
    ll.sampleRecordDatetime = CASE WHEN r.limsSampleRecordDatetime IS NOT NULL THEN datetime(replace(r.limsSampleRecordDatetime, ' ', 'T')) END
"""

# ── BATCH_STATUS: Relationship queries ────────────────────────────────

BATCH_MADE_OF_MATERIAL = """
UNWIND $rows AS r
WITH r WHERE r.batchCode <> '' AND r.localMaterialCode <> ''
MATCH (b:Batch {batchCode: r.batchCode, plantCode: r.plantCode})
MATCH (m:Material {localMaterialCode: r.localMaterialCode})
MERGE (b)-[:MADE_OF]->(m)
"""

BATCH_MANUFACTURED_AT_PLANT = """
UNWIND $rows AS r
WITH r WHERE r.batchCode <> '' AND r.plantCode <> ''
MATCH (b:Batch {batchCode: r.batchCode, plantCode: r.plantCode})
MATCH (p:Plant {plantCode: r.plantCode})
MERGE (b)-[:MANUFACTURED_AT]->(p)
"""

BATCH_STORED_IN = """
UNWIND $rows AS r
WITH r WHERE r.batchCode <> '' AND r.storageLocationCode <> '' AND r.plantCode <> ''
MATCH (b:Batch {batchCode: r.batchCode, plantCode: r.plantCode})
MATCH (sl:StorageLocation {code: r.storageLocationCode, plantCode: r.plantCode})
MERGE (b)-[:STORED_IN]->(sl)
"""

BATCH_SUPPLIED_BY_VENDOR = """
UNWIND $rows AS r
WITH r WHERE r.batchCode <> '' AND r.vendorAccountNumber <> ''
MATCH (b:Batch {batchCode: r.batchCode, plantCode: r.plantCode})
MATCH (v:Vendor {accountNumber: r.vendorAccountNumber})
MERGE (b)-[:SUPPLIED_BY]->(v)
"""

BATCH_HAS_INSPECTION = """
UNWIND $rows AS r
WITH r WHERE r.batchCode <> '' AND r.referenceInspectionLotNumber <> ''
MATCH (b:Batch {batchCode: r.batchCode, plantCode: r.plantCode})
MATCH (il:InspectionLot {referenceNumber: r.referenceInspectionLotNumber})
MERGE (b)-[:HAS_INSPECTION]->(il)
"""

BATCH_HAS_LIMS_LOT = """
UNWIND $rows AS r
WITH r WHERE r.batchCode <> '' AND r.limsLotNumber <> ''
MATCH (b:Batch {batchCode: r.batchCode, plantCode: r.plantCode})
MATCH (ll:LIMSLot {lotNumber: r.limsLotNumber})
MERGE (b)-[:HAS_LIMS_LOT]->(ll)
"""

BATCH_PRODUCED_BY_ORDER = """
UNWIND $rows AS r
WITH r WHERE r.batchCode <> '' AND r.processOrderNumber <> ''
MATCH (b:Batch {batchCode: r.batchCode, plantCode: r.plantCode})
MERGE (po:ProcessOrder {processOrderNumber: r.processOrderNumber})
MERGE (b)-[rel:PRODUCED_BY]->(po)
SET rel.goodsReceiptEntryDatetime   = CASE WHEN r.batchLastGREntryDt IS NOT NULL THEN datetime(replace(r.batchLastGREntryDt, ' ', 'T')) END,
    rel.goodsReceiptPostingDatetime = CASE WHEN r.batchLastGRPostingDt IS NOT NULL THEN datetime(replace(r.batchLastGRPostingDt, ' ', 'T')) END
"""

BATCH_SOURCED_FROM = """
UNWIND $rows AS r
WITH r WHERE r.batchCode <> '' AND r.srcSysNm <> ''
MATCH (b:Batch {batchCode: r.batchCode, plantCode: r.plantCode})
MATCH (ss:SourceSystem {name: r.srcSysNm})
MERGE (b)-[:SOURCED_FROM]->(ss)
"""

MATERIAL_BELONGS_TO_SUBFAMILY = """
UNWIND $rows AS r
WITH r WHERE r.localMaterialCode <> '' AND r.productSubFamilyName <> ''
MATCH (m:Material {localMaterialCode: r.localMaterialCode})
MATCH (psf:ProductSubFamily {name: r.productSubFamilyName})
MERGE (m)-[:BELONGS_TO_SUBFAMILY]->(psf)
"""

SUBFAMILY_BELONGS_TO_FAMILY = """
UNWIND $rows AS r
WITH r WHERE r.productSubFamilyName <> '' AND r.productFamilyName <> ''
MATCH (psf:ProductSubFamily {name: r.productSubFamilyName})
MATCH (pf:ProductFamily {name: r.productFamilyName})
MERGE (psf)-[:BELONGS_TO_FAMILY]->(pf)
"""

PLANT_HAS_STORAGE = """
UNWIND $rows AS r
WITH r WHERE r.plantCode <> '' AND r.storageLocationCode <> ''
MATCH (p:Plant {plantCode: r.plantCode})
MATCH (sl:StorageLocation {code: r.storageLocationCode, plantCode: r.plantCode})
MERGE (p)-[:HAS_STORAGE]->(sl)
"""


# ══════════════════════════════════════════════════════════════════════
# PHASE 2: ORDER_STATUS CSV → Nodes & Relationships
# ══════════════════════════════════════════════════════════════════════

def transform_order_status(row):
    """Transform an order_status CSV row into params for Cypher."""
    return {
        # ProcessOrder (mia:ProcessOrder)
        "processOrderNumber": row.get("PROCESS_ORDER_NUMBER", ""),
        "processOrderIdentifier": row.get("PROCESS_ORDER_IDENTIFIER", ""),
        "processOrderItemNumber": row.get("PROCESS_ORDER_ITEM_NUMBER", ""),
        "orderTypeCode": row.get("PROCESS_ORDER_TYPE_CODE", ""),
        "orderTypeIdentifier": row.get("PROCESS_ORDER_TYPE_IDENTIFIER", ""),
        "orderCategoryCode": row.get("PROCESS_ORDER_CATEGORY_CODE", ""),
        "orderCategoryName": row.get("ORDER_CATEGORY_NAME", ""),
        "routingKeyIdentifier": row.get("ROUTING_KEY_IDENTIFIER", ""),
        "billOfMaterialsIdentifier": row.get("BILL_OF_MATERIALS_IDENTIFIER", ""),
        "productionVersionNumber": row.get("PRODUCTION_VERSION_NUMBER", ""),
        "productionVersionDescription": row.get("PRODUCTION_VERSION_DESCRIPTION", ""),
        "scheduledStartDatetime": row.get("SCHEDULED_START_DATETIME", "") or None,
        "scheduledFinishDatetime": row.get("SCHEDULED_FINISH_DATETIME", "") or None,
        "basicStartDatetime": row.get("BASIC_START_DATETIME", "") or None,
        "basicFinishDatetime": row.get("BASIC_FINISH_DATETIME", "") or None,
        "actualStartDatetime": row.get("ACTUAL_START_DATETIME", "") or None,
        "actualFinishDate": row.get("ACTUAL_FINISH_DATE", "") or None,
        "actualReleaseDate": row.get("ACTUAL_RELEASE_DATE", "") or None,
        "actualDeliveryFinishDate": row.get("ACTUAL_DELIVERY_FINISH_DATE", "") or None,
        "orderCreationDate": row.get("ORDER_CREATION_DATE", "") or None,
        "scheduledReleaseDate": row.get("SCHEDULED_RELEASE_DATE", "") or None,
        "plannedReleaseDate": row.get("PLANNED_RELEASE_DATE", "") or None,
        "plannedOrderStartDate": row.get("PLANNED_ORDER_START_DATE", "") or None,
        "confirmedOrderFinishDatetime": row.get("CONFIRMED_ORDER_FINISH_DATETIME", "") or None,
        "totalOrderQuantity": safe_float(row.get("TOTAL_ORDER_QUANTITY", "")),
        "enteredOrderItemQuantity": safe_float(row.get("ENTERED_ORDER_ITEM_QUANTITY", "")),
        "enteredGoodsReceivedQuantity": safe_float(row.get("ENTERED_GOODS_RECEIVED_QUANTITY", "")),
        "enteredTotalScrapQuantity": safe_float(row.get("ENTERED_TOTAL_SCRAP_QUANTITY", "")),
        "enteredUnitOfMeasureIdentifier": row.get("ENTERED_UNIT_OF_MEASURE_IDENTIFIER", ""),
        "baseOrderItemQuantity": safe_float(row.get("BASE_ORDER_ITEM_QUANTITY", "")),
        "baseGoodsReceivedQuantity": safe_float(row.get("BASE_GOODS_RECEIVED_QUANTITY", "")),
        "baseTotalScrapQuantity": safe_float(row.get("BASE_TOTAL_SCRAP_QUANTITY", "")),
        "baseTotalPlannedQuantity": safe_float(row.get("BASE_TOTAL_PLANNED_QUANTITY", "")),
        "baseUnitOfMeasureIdentifier": row.get("BASE_UNIT_OF_MEASURE_IDENTIFIER", ""),
        "baseUnitOfMeasureCode": row.get("BASE_UNIT_OF_MEASURE_CODE", ""),
        "reworkOrderIndicator": row.get("REWORK_ORDER_INDICATOR", ""),
        "closedIndicator": row.get("CLOSED_INDICATOR", ""),
        "closedLastUpdatedDatetime": row.get("CLOSED_LAST_UPDATED_DATETIME", "") or None,
        "lockedIndicator": row.get("LOCKED_INDICATOR", ""),
        "lockedLastUpdatedDatetime": row.get("LOCKED_LAST_UPDATED_DATETIME", "") or None,
        "techCompletedIndicator": row.get("TECHNICALLY_COMPLETED_INDICATOR", ""),
        "techCompletedLastUpdatedDatetime": row.get("TECHNICALLY_COMPLETED_LAST_UPDATED_DATETIME", "") or None,
        "deliveryCompletedIndicator": row.get("DELIVERY_COMPLETED_INDICATOR", ""),
        "deliveryLastUpdatedDatetime": row.get("DELIVERY_LAST_UPDATED_DATETIME", "") or None,
        "createdIndicator": row.get("CREATED_INDICATOR", ""),
        "createdLastUpdatedDatetime": row.get("CREATED_LAST_UPDATED_DATETIME", "") or None,
        "releasedIndicator": row.get("RELEASED_INDICATOR", ""),
        "releasedLastUpdatedDatetime": row.get("RELEASED_LAST_UPDATED_DATETIME", "") or None,
        "confirmedIndicator": row.get("CONFIRMED_INDICATOR", ""),
        "confirmedLastUpdatedDatetime": row.get("CONFIRMED_LAST_UPDATED_DATETIME", "") or None,
        "cancelledIndicator": row.get("CANCELLED_INDICATOR", ""),
        "deletionIndicator": row.get("DELETION_INDICATOR", ""),
        "orderItemHasActualFinishDate": row.get("ORDER_ITEM_HAS_ACTUAL_FINISH_DATE_INDICATOR", ""),
        "productionSupervisorIdentifier": row.get("PRODUCTION_SUPERVISOR_IDENTIFIER", ""),
        "reservationNumber": row.get("RESERVATION_NUMBER", ""),
        "productionPlannerControllerCode": row.get("PRODUCTION_PLANNER_CONTROLLER_CODE", ""),
        "processingOfGoodsReceiptInDays": safe_int(row.get("PROCESSING_OF_GOODS_RECEIPT_IN_DAYS_NUMBER", "")),
        "sapObjectCode": row.get("SAP_OBJECT_CODE", ""),
        "systemStatusesText": row.get("SYSTEM_STATUSES_TEXT", ""),
        "userStatusesText": row.get("USER_STATUSES_TEXT", ""),
        "sourceSystemCode": row.get("SOURCE_SYSTEM_CODE", ""),

        # Material (from order_status)
        "localMaterialCode": row.get("LOCAL_MATERIAL_CODE", ""),
        "globalMaterialCode": row.get("GLOBAL_MATERIAL_CODE", ""),
        "cleanedLocalMaterialCode": row.get("CLEANED_LOCAL_MATERIAL_CODE", ""),
        "materialName": row.get("MATERIAL_NAME", ""),
        "materialTypeCode": row.get("MATERIAL_TYPE_CODE", ""),
        "materialIdentifier": row.get("MATERIAL_IDENTIFIER", ""),
        "materialTradeCode": row.get("MATERIAL_TRADE_CODE", ""),
        "materialGroupCode": row.get("MATERIAL_GROUP_CODE", ""),
        "procurementTypeCode": row.get("PROCUREMENT_TYPE_CODE", ""),
        "productLocationTypeCode": row.get("PRODUCT_LOCATION_TYPE_CODE", ""),
        "productLocationTypeName": row.get("PRODUCT_LOCATION_TYPE_NAME", ""),

        # Plant
        "planningPlantCode": row.get("PLANNING_PLANT_CODE", ""),
        "productionPlantCode": row.get("PRODUCTION_PLANT_CODE", ""),
        "plantCode": row.get("PLANT_CODE", ""),
        "storageLocationCode": row.get("STORAGE_LOCATION_CODE", ""),

        # Batch (from order_status)
        "batchCode": row.get("BATCH_CODE", ""),
        "batchIdentifier": row.get("BATCH_IDENTIFIER", ""),

        # Planned order
        "plannedOrderIdentifier": row.get("PLANNED_ORDER_IDENTIFIER", ""),

        # Product hierarchy
        "productFamilyName": row.get("PRODUCT_FAMILY_NAME", ""),
        "productSubFamilyName": row.get("PRODUCT_SUB_FAMILY_NAME", ""),

        # Operation
        "operationName": row.get("OPERATION_NAME", ""),
        "operationCode": row.get("OPERATION_CODE", ""),
        "workCentreCode": row.get("WORK_CENTRE_CODE", ""),
        "operationStatusName": row.get("OPERATION_STATUS_NAME", ""),
        "operationDatetime": row.get("OPERATION_DATETIME", "") or None,
        "nextOperationName": row.get("NEXT_OPERATION_NAME", ""),
        "nextOperationCode": row.get("NEXT_OPERATION_CODE", ""),
        "finishedOperationsCount": safe_int(row.get("FINISHED_OPERATIONS_COUNT", "")),
        "totalOperationsCount": safe_int(row.get("TOTAL_OPERATIONS_COUNT", "")),
        "operationsText": row.get("OPERATIONS_TEXT", ""),
        "workCentreCodesText": row.get("WORK_CENTRE_CODES_TEXT", ""),

        # Inspection lot (from order)
        "referenceInspectionLotNumber": row.get("REFERENCE_INSPECTION_LOT_NUMBER", ""),
        "inspectionLotStorageLocationCode": row.get("INSPECTION_LOT_STORAGE_LOCATION_CODE", ""),
        "plannedInspectionLotQuantity": safe_float(row.get("PLANNED_INSPECTION_LOT_QUANTITY", "")),
        "inspectionTypeCode": row.get("INSPECTION_TYPE_CODE", ""),
        "inspectionLotCreationDatetime": row.get("INSPECTION_LOT_CREATION_DATETIME", "") or None,
        "usageDecisionCode": row.get("USAGE_DECISION_CODE", ""),
        "usageDecisionDatetime": row.get("USAGE_DECISON_DATETIME", "") or None,

        # Quality (from order)
        "qualityEventIdentifiersText": row.get("QUALITY_EVENT_IDENTIFIERS_TEXT", ""),
        "qualityEventTypeCodesText": row.get("QUALITY_EVENT_TYPE_CODES_TEXT", ""),
        "lifecycleStateCodesText": row.get("LIFECYCLE_STATE_CODES_TEXT", ""),
        "workflowLogEntryDescription": row.get("WORKFLOW_LOG_ENTRY_DESCRIPTION", ""),
        "workflowEntryExecutionDatetime": row.get("WORKFLOW_ENTRY_EXECUTION_DATETIME", "") or None,
        "qualityNotificationsText": row.get("QUALITY_NOTIFICATIONS_TEXT", ""),
        "qualityNotificationsTypeCodesText": row.get("QUALITY_NOTIFICATIONS_TYPE_CODES_TEXT", ""),
        "qualityNotificationsSystemStatusesText": row.get("QUALITY_NOTIFICATIONS_SYSTEM_STATUSES_TEXT", ""),
        "qualityNotificationsUserStatusesText": row.get("QUALITY_NOTIFICATIONS_USER_STATUSES_TEXT", ""),

        # Batch lifecycle (from order_status)
        "batchExclusionIndicator": row.get("BATCH_EXCLUSION_FROM_ANALYSIS_INDICATOR", ""),
        "batchLastGREntryDt": row.get("BATCH_LAST_GOODS_RECEIPT_ENTRY_DATETIME", "") or None,
        "batchLastGRPostingDt": row.get("BATCH_LAST_GOODS_RECEIPT_POSTING_DATETIME", "") or None,
        "batchSamplingEntryDt": row.get("BATCH_SAMPLING_ENTRY_DATETIME", "") or None,
        "batchSamplingPostingDt": row.get("BATCH_SAMPLING_POSTING_DATETIME", "") or None,
        "batchReleaseEntryDt": row.get("BATCH_RELEASE_ENTRY_DATETIME", "") or None,
        "batchReleasePostingDt": row.get("BATCH_RELEASE_POSTING_DATETIME", "") or None,
        "batchGoodsIssueEntryDt": row.get("BATCH_GOODS_ISSUE_ENTRY_DATETIME", "") or None,
        "batchGoodsIssuePostingDt": row.get("BATCH_GOODS_ISSUE_POSTING_DATETIME", "") or None,
        "batchPickEntryDt": row.get("BATCH_PICK_ENTRY_DATETIME", "") or None,
        "batchPickPostingDt": row.get("BATCH_PICK_POSTING_DATETIME", "") or None,

        # Order reference
        "orderReferenceYearWeekNumber": row.get("ORDER_REFERENCE_YEAR_WEEK_NUMBER", ""),
        "orderReferenceRelativeWeekNumber": safe_int(row.get("ORDER_REFERENCE_RELATIVE_WEEK_NUMBER", "")),

        # Source system
        "srcSysNm": row.get("SRC_SYS_NM", ""),
        "srcSysId": row.get("SRC_SYS_ID", ""),
        "etlCreTs": row.get("ETL_CRE_TS", "") or None,
        "etlUpdtTs": row.get("ETL_UPDT_TS", "") or None,
    }


PROCESS_ORDER_NODE_CYPHER = """
UNWIND $rows AS r
WITH r WHERE r.processOrderNumber <> ''
MERGE (po:ProcessOrder {processOrderNumber: r.processOrderNumber})
SET po.processOrderIdentifier      = r.processOrderIdentifier,
    po.orderTypeCode               = r.orderTypeCode,
    po.orderTypeIdentifier         = r.orderTypeIdentifier,
    po.orderCategoryCode           = r.orderCategoryCode,
    po.orderCategoryName           = r.orderCategoryName,
    po.routingKeyIdentifier        = r.routingKeyIdentifier,
    po.billOfMaterialsIdentifier   = r.billOfMaterialsIdentifier,
    po.productionVersionNumber     = r.productionVersionNumber,
    po.productionVersionDescription = r.productionVersionDescription,
    po.scheduledStartDatetime      = CASE WHEN r.scheduledStartDatetime IS NOT NULL THEN datetime(replace(r.scheduledStartDatetime, ' ', 'T')) END,
    po.scheduledFinishDatetime     = CASE WHEN r.scheduledFinishDatetime IS NOT NULL THEN datetime(replace(r.scheduledFinishDatetime, ' ', 'T')) END,
    po.basicStartDatetime          = CASE WHEN r.basicStartDatetime IS NOT NULL THEN datetime(replace(r.basicStartDatetime, ' ', 'T')) END,
    po.basicFinishDatetime         = CASE WHEN r.basicFinishDatetime IS NOT NULL THEN datetime(replace(r.basicFinishDatetime, ' ', 'T')) END,
    po.actualStartDatetime         = CASE WHEN r.actualStartDatetime IS NOT NULL THEN datetime(replace(r.actualStartDatetime, ' ', 'T')) END,
    po.actualFinishDate            = CASE WHEN r.actualFinishDate IS NOT NULL THEN date(r.actualFinishDate) END,
    po.actualReleaseDate           = CASE WHEN r.actualReleaseDate IS NOT NULL THEN date(r.actualReleaseDate) END,
    po.actualDeliveryFinishDate    = CASE WHEN r.actualDeliveryFinishDate IS NOT NULL THEN date(r.actualDeliveryFinishDate) END,
    po.orderCreationDate           = CASE WHEN r.orderCreationDate IS NOT NULL THEN date(r.orderCreationDate) END,
    po.scheduledReleaseDate        = CASE WHEN r.scheduledReleaseDate IS NOT NULL THEN date(r.scheduledReleaseDate) END,
    po.confirmedOrderFinishDatetime = CASE WHEN r.confirmedOrderFinishDatetime IS NOT NULL THEN datetime(replace(r.confirmedOrderFinishDatetime, ' ', 'T')) END,
    po.totalOrderQuantity          = r.totalOrderQuantity,
    po.enteredOrderItemQuantity    = r.enteredOrderItemQuantity,
    po.enteredGoodsReceivedQuantity = r.enteredGoodsReceivedQuantity,
    po.enteredTotalScrapQuantity   = r.enteredTotalScrapQuantity,
    po.enteredUnitOfMeasureIdentifier = r.enteredUnitOfMeasureIdentifier,
    po.baseOrderItemQuantity       = r.baseOrderItemQuantity,
    po.baseGoodsReceivedQuantity   = r.baseGoodsReceivedQuantity,
    po.baseTotalScrapQuantity      = r.baseTotalScrapQuantity,
    po.baseTotalPlannedQuantity    = r.baseTotalPlannedQuantity,
    po.baseUnitOfMeasureIdentifier = r.baseUnitOfMeasureIdentifier,
    po.baseUnitOfMeasureCode       = r.baseUnitOfMeasureCode,
    po.reworkOrderIndicator        = r.reworkOrderIndicator,
    po.closedIndicator             = r.closedIndicator,
    po.closedLastUpdatedDatetime   = CASE WHEN r.closedLastUpdatedDatetime IS NOT NULL THEN datetime(replace(r.closedLastUpdatedDatetime, ' ', 'T')) END,
    po.lockedIndicator             = r.lockedIndicator,
    po.lockedLastUpdatedDatetime   = CASE WHEN r.lockedLastUpdatedDatetime IS NOT NULL THEN datetime(replace(r.lockedLastUpdatedDatetime, ' ', 'T')) END,
    po.techCompletedIndicator      = r.techCompletedIndicator,
    po.techCompletedLastUpdatedDatetime = CASE WHEN r.techCompletedLastUpdatedDatetime IS NOT NULL THEN datetime(replace(r.techCompletedLastUpdatedDatetime, ' ', 'T')) END,
    po.deliveryCompletedIndicator  = r.deliveryCompletedIndicator,
    po.deliveryLastUpdatedDatetime = CASE WHEN r.deliveryLastUpdatedDatetime IS NOT NULL THEN datetime(replace(r.deliveryLastUpdatedDatetime, ' ', 'T')) END,
    po.createdIndicator            = r.createdIndicator,
    po.createdLastUpdatedDatetime  = CASE WHEN r.createdLastUpdatedDatetime IS NOT NULL THEN datetime(replace(r.createdLastUpdatedDatetime, ' ', 'T')) END,
    po.releasedIndicator           = r.releasedIndicator,
    po.releasedLastUpdatedDatetime = CASE WHEN r.releasedLastUpdatedDatetime IS NOT NULL THEN datetime(replace(r.releasedLastUpdatedDatetime, ' ', 'T')) END,
    po.confirmedIndicator          = r.confirmedIndicator,
    po.confirmedLastUpdatedDatetime = CASE WHEN r.confirmedLastUpdatedDatetime IS NOT NULL THEN datetime(replace(r.confirmedLastUpdatedDatetime, ' ', 'T')) END,
    po.cancelledIndicator          = r.cancelledIndicator,
    po.deletionIndicator           = r.deletionIndicator,
    po.orderItemHasActualFinishDate = r.orderItemHasActualFinishDate,
    po.productionSupervisorIdentifier = r.productionSupervisorIdentifier,
    po.reservationNumber           = r.reservationNumber,
    po.productionPlannerControllerCode = r.productionPlannerControllerCode,
    po.processingOfGoodsReceiptInDays = r.processingOfGoodsReceiptInDays,
    po.sapObjectCode               = r.sapObjectCode,
    po.systemStatusesText          = r.systemStatusesText,
    po.userStatusesText            = r.userStatusesText,
    po.sourceSystemCode            = r.sourceSystemCode,
    po.localMaterialCode           = r.localMaterialCode,
    po.globalMaterialCode          = r.globalMaterialCode,
    po.materialName                = r.materialName,
    po.materialTypeCode            = r.materialTypeCode,
    po.materialTradeCode           = r.materialTradeCode,
    po.materialGroupCode           = r.materialGroupCode,
    po.procurementTypeCode         = r.procurementTypeCode,
    po.productLocationTypeCode     = r.productLocationTypeCode,
    po.productLocationTypeName     = r.productLocationTypeName,
    po.plantCode                   = r.plantCode,
    po.planningPlantCode           = r.planningPlantCode,
    po.productionPlantCode         = r.productionPlantCode,
    po.batchCode                   = r.batchCode,
    po.finishedOperationsCount     = r.finishedOperationsCount,
    po.totalOperationsCount        = r.totalOperationsCount,
    po.operationsText              = r.operationsText,
    po.workCentreCodesText         = r.workCentreCodesText,
    po.orderReferenceYearWeekNumber = r.orderReferenceYearWeekNumber,
    po.orderReferenceRelativeWeekNumber = r.orderReferenceRelativeWeekNumber,
    po.qualityEventIdentifiersText = r.qualityEventIdentifiersText,
    po.qualityEventTypeCodesText   = r.qualityEventTypeCodesText,
    po.lifecycleStateCodesText     = r.lifecycleStateCodesText,
    po.workflowLogEntryDescription = r.workflowLogEntryDescription,
    po.workflowEntryExecutionDatetime = CASE WHEN r.workflowEntryExecutionDatetime IS NOT NULL THEN datetime(replace(r.workflowEntryExecutionDatetime, ' ', 'T')) END,
    po.qualityNotificationsText    = r.qualityNotificationsText,
    po.qualityNotificationsTypeCodesText = r.qualityNotificationsTypeCodesText,
    po.qualityNotificationsSystemStatusesText = r.qualityNotificationsSystemStatusesText,
    po.qualityNotificationsUserStatusesText = r.qualityNotificationsUserStatusesText,
    po.etlCreatedDatetime          = CASE WHEN r.etlCreTs IS NOT NULL THEN datetime(replace(r.etlCreTs, ' ', 'T')) END,
    po.etlUpdatedDatetime          = CASE WHEN r.etlUpdtTs IS NOT NULL THEN datetime(replace(r.etlUpdtTs, ' ', 'T')) END
"""

OPERATION_NODE_CYPHER = """
UNWIND $rows AS r
WITH r WHERE r.processOrderNumber <> '' AND r.operationCode <> ''
MERGE (op:Operation {processOrderNumber: r.processOrderNumber, operationCode: r.operationCode})
SET op.operationName   = r.operationName,
    op.statusName      = r.operationStatusName,
    op.operationDatetime = CASE WHEN r.operationDatetime IS NOT NULL THEN datetime(replace(r.operationDatetime, ' ', 'T')) END,
    op.nextOperationName = r.nextOperationName,
    op.nextOperationCode = r.nextOperationCode
"""

WORK_CENTRE_NODE_CYPHER = """
UNWIND $rows AS r
WITH r WHERE r.workCentreCode <> ''
MERGE (wc:WorkCentre {code: r.workCentreCode})
"""

PLANNED_ORDER_NODE_CYPHER = """
UNWIND $rows AS r
WITH r WHERE r.plannedOrderIdentifier <> ''
MERGE (plo:PlannedOrder {plannedOrderNumber: r.plannedOrderIdentifier})
"""

# ── ORDER_STATUS: Relationship queries ────────────────────────────────

ORDER_EXECUTED_AT_PLANT = """
UNWIND $rows AS r
WITH r WHERE r.processOrderNumber <> '' AND r.productionPlantCode <> ''
MATCH (po:ProcessOrder {processOrderNumber: r.processOrderNumber})
MERGE (p:Plant {plantCode: r.productionPlantCode})
MERGE (po)-[:EXECUTED_AT]->(p)
"""

ORDER_PRODUCES_MATERIAL = """
UNWIND $rows AS r
WITH r WHERE r.processOrderNumber <> '' AND r.localMaterialCode <> ''
MATCH (po:ProcessOrder {processOrderNumber: r.processOrderNumber})
MATCH (m:Material {localMaterialCode: r.localMaterialCode})
MERGE (po)-[:PRODUCES]->(m)
"""

ORDER_HAS_OPERATION = """
UNWIND $rows AS r
WITH r WHERE r.processOrderNumber <> '' AND r.operationCode <> ''
MATCH (po:ProcessOrder {processOrderNumber: r.processOrderNumber})
MATCH (op:Operation {processOrderNumber: r.processOrderNumber, operationCode: r.operationCode})
MERGE (po)-[:HAS_OPERATION]->(op)
"""

ORDER_ORIGINATES_FROM_PLANNED = """
UNWIND $rows AS r
WITH r WHERE r.processOrderNumber <> '' AND r.plannedOrderIdentifier <> ''
MATCH (po:ProcessOrder {processOrderNumber: r.processOrderNumber})
MATCH (plo:PlannedOrder {plannedOrderNumber: r.plannedOrderIdentifier})
MERGE (po)-[:ORIGINATES_FROM]->(plo)
"""

ORDER_HAS_INSPECTION = """
UNWIND $rows AS r
WITH r WHERE r.processOrderNumber <> '' AND r.referenceInspectionLotNumber <> ''
MATCH (po:ProcessOrder {processOrderNumber: r.processOrderNumber})
MERGE (il:InspectionLot {referenceNumber: r.referenceInspectionLotNumber})
SET il.inspectionTypeCode          = r.inspectionTypeCode,
    il.inspectionLotStorageLocation = r.inspectionLotStorageLocationCode,
    il.plannedQuantity             = r.plannedInspectionLotQuantity,
    il.creationDatetime            = CASE WHEN r.inspectionLotCreationDatetime IS NOT NULL THEN datetime(replace(r.inspectionLotCreationDatetime, ' ', 'T')) END,
    il.usageDecisionCode           = r.usageDecisionCode,
    il.usageDecisionDatetime       = CASE WHEN r.usageDecisionDatetime IS NOT NULL THEN datetime(replace(r.usageDecisionDatetime, ' ', 'T')) END
MERGE (po)-[:HAS_INSPECTION]->(il)
"""

OPERATION_USES_WORK_CENTRE = """
UNWIND $rows AS r
WITH r WHERE r.processOrderNumber <> '' AND r.operationCode <> '' AND r.workCentreCode <> ''
MATCH (op:Operation {processOrderNumber: r.processOrderNumber, operationCode: r.operationCode})
MATCH (wc:WorkCentre {code: r.workCentreCode})
MERGE (op)-[:USES_WORK_CENTRE]->(wc)
"""

OPERATION_NEXT_OPERATION = """
UNWIND $rows AS r
WITH r WHERE r.processOrderNumber <> '' AND r.operationCode <> '' AND r.nextOperationCode <> ''
MATCH (op1:Operation {processOrderNumber: r.processOrderNumber, operationCode: r.operationCode})
MERGE (op2:Operation {processOrderNumber: r.processOrderNumber, operationCode: r.nextOperationCode})
MERGE (op1)-[:NEXT_OPERATION]->(op2)
"""

ORDER_SOURCED_FROM = """
UNWIND $rows AS r
WITH r WHERE r.processOrderNumber <> '' AND r.srcSysNm <> ''
MATCH (po:ProcessOrder {processOrderNumber: r.processOrderNumber})
MERGE (ss:SourceSystem {name: r.srcSysNm})
SET ss.systemId = r.srcSysId
MERGE (po)-[:SOURCED_FROM]->(ss)
"""


# ══════════════════════════════════════════════════════════════════════
# PHASE 3: ORDER_BATCH_RELATIONSHIP CSV → Relationships
# ══════════════════════════════════════════════════════════════════════

def transform_order_batch_relationship(row):
    """Transform an order_batch_relationship CSV row."""
    return {
        "processOrderNumber": row.get("PROCESS_ORDER_NUMBER", ""),
        "plannedOrderNumber": row.get("PLANNED_ORDER_NUMBER", ""),
        "plantCode": row.get("PLANT_CODE", ""),
        "batchCode": row.get("BATCH_CODE", ""),
        "localMaterialCode": row.get("LOCAL_MATERIAL_CODE", ""),
        "orderReferenceDate": row.get("ORDER_REFERENCE_DATE", "") or None,
        "goodsIssueEntryDatetime": row.get("GOODS_ISSUE_ENTRY_DATETIME", "") or None,
        "goodsIssuePostingDatetime": row.get("GOODS_ISSUE_POSTING_DATETIME", "") or None,
        "consumedBatchCode": row.get("CONSUMED_BATCH_CODE", ""),
        "consumedLocalMaterialCode": row.get("CONSUMED_LOCAL_MATERIAL_CODE", ""),
        "consumedBatchStorageLocationCode": row.get("CONSUMED_BATCH_STORAGE_LOCATION_CODE", ""),
        "unitOfMeasureCode": row.get("UNIT_OF_MEASURE_CODE", ""),
        "quantity": safe_float(row.get("QUANTITY", "")),
        "relationshipTypeName": row.get("RELATIONSHIP_TYPE_NAME", ""),
        "srcSysNm": row.get("SRC_SYS_NM", ""),
        "srcSysId": row.get("SRC_SYS_ID", ""),
        "etlCreTs": row.get("ETL_CRE_TS", "") or None,
        "etlUpdtTs": row.get("ETL_UPDT_TS", "") or None,
    }


# Consumption: consumed batch → process order (def-ops:consumes inverse)
CONSUMED_BY_CYPHER = """
UNWIND $rows AS r
WITH r WHERE r.consumedBatchCode <> '' AND r.processOrderNumber <> ''
             AND r.relationshipTypeName IN ['Consumption', 'Allocation', 'Reservation']
MERGE (b:Batch {batchCode: r.consumedBatchCode, plantCode: r.plantCode})
MATCH (po:ProcessOrder {processOrderNumber: r.processOrderNumber})
MERGE (b)-[rel:CONSUMED_BY]->(po)
SET rel.quantity                  = r.quantity,
    rel.unitOfMeasure             = r.unitOfMeasureCode,
    rel.relationshipType          = r.relationshipTypeName,
    rel.consumedLocalMaterialCode = r.consumedLocalMaterialCode,
    rel.storageLocationCode       = r.consumedBatchStorageLocationCode,
    rel.goodsIssueEntryDatetime   = CASE WHEN r.goodsIssueEntryDatetime IS NOT NULL THEN datetime(replace(r.goodsIssueEntryDatetime, ' ', 'T')) END,
    rel.goodsIssuePostingDatetime = CASE WHEN r.goodsIssuePostingDatetime IS NOT NULL THEN datetime(replace(r.goodsIssuePostingDatetime, ' ', 'T')) END
"""

# Recommendation: planned order → consumed batch (mia:recommends)
RECOMMENDS_CYPHER = """
UNWIND $rows AS r
WITH r WHERE r.consumedBatchCode <> '' AND r.plannedOrderNumber <> ''
             AND r.relationshipTypeName = 'Recommendation'
MERGE (plo:PlannedOrder {plannedOrderNumber: r.plannedOrderNumber})
MERGE (b:Batch {batchCode: r.consumedBatchCode, plantCode: r.plantCode})
MERGE (plo)-[rel:RECOMMENDS]->(b)
SET rel.quantity                  = r.quantity,
    rel.unitOfMeasure             = r.unitOfMeasureCode,
    rel.consumedLocalMaterialCode = r.consumedLocalMaterialCode,
    rel.storageLocationCode       = r.consumedBatchStorageLocationCode,
    rel.orderReferenceDate        = CASE WHEN r.orderReferenceDate IS NOT NULL THEN date(r.orderReferenceDate) END
"""

# Adjustment: process order → consumed batch (mia:adjusts)
ADJUSTS_CYPHER = """
UNWIND $rows AS r
WITH r WHERE r.consumedBatchCode <> '' AND r.processOrderNumber <> ''
             AND r.relationshipTypeName = 'Adjustment'
MATCH (po:ProcessOrder {processOrderNumber: r.processOrderNumber})
MERGE (b:Batch {batchCode: r.consumedBatchCode, plantCode: r.plantCode})
MERGE (po)-[rel:ADJUSTS]->(b)
SET rel.quantity                  = r.quantity,
    rel.unitOfMeasure             = r.unitOfMeasureCode,
    rel.consumedLocalMaterialCode = r.consumedLocalMaterialCode,
    rel.storageLocationCode       = r.consumedBatchStorageLocationCode,
    rel.goodsIssueEntryDatetime   = CASE WHEN r.goodsIssueEntryDatetime IS NOT NULL THEN datetime(replace(r.goodsIssueEntryDatetime, ' ', 'T')) END,
    rel.goodsIssuePostingDatetime = CASE WHEN r.goodsIssuePostingDatetime IS NOT NULL THEN datetime(replace(r.goodsIssuePostingDatetime, ' ', 'T')) END
"""


# ══════════════════════════════════════════════════════════════════════
# PHASE 4: Multi-value fields → QualityEvent & QualityNotification nodes
# ══════════════════════════════════════════════════════════════════════

QUALITY_EVENTS_FROM_BATCH = """
UNWIND $rows AS r
WITH r WHERE r.qualityEventIdentifiersText <> ''
WITH r, split(r.qualityEventIdentifiersText, ',') AS ids,
     CASE WHEN r.qualityEventTypeCodesText <> '' THEN split(r.qualityEventTypeCodesText, ',') ELSE [] END AS types
UNWIND range(0, size(ids)-1) AS i
WITH r, trim(ids[i]) AS eid,
     CASE WHEN i < size(types) THEN trim(types[i]) ELSE '' END AS etype
WHERE eid <> ''
MERGE (qe:QualityEvent {identifier: eid})
SET qe.typeCode = CASE WHEN etype <> '' THEN etype ELSE qe.typeCode END
WITH r, qe
MATCH (b:Batch {batchCode: r.batchCode, plantCode: r.plantCode})
MERGE (b)-[:HAS_QUALITY_EVENT]->(qe)
"""

QUALITY_NOTIFICATIONS_FROM_BATCH = """
UNWIND $rows AS r
WITH r WHERE r.qualityNotificationsText <> ''
WITH r, split(r.qualityNotificationsText, ',') AS ids,
     CASE WHEN r.qualityNotificationsTypeCodesText <> '' THEN split(r.qualityNotificationsTypeCodesText, ',') ELSE [] END AS types
UNWIND range(0, size(ids)-1) AS i
WITH r, trim(ids[i]) AS qnid,
     CASE WHEN i < size(types) THEN trim(types[i]) ELSE '' END AS qntype
WHERE qnid <> ''
MERGE (qn:QualityNotification {identifier: qnid})
SET qn.typeCode = CASE WHEN qntype <> '' THEN qntype ELSE qn.typeCode END
WITH r, qn
MATCH (b:Batch {batchCode: r.batchCode, plantCode: r.plantCode})
MERGE (b)-[:HAS_QUALITY_NOTIFICATION]->(qn)
"""


# ══════════════════════════════════════════════════════════════════════
# MAIN LOADER
# ══════════════════════════════════════════════════════════════════════

def load(uri, user, password, database="neo4j"):
    batch_csv = find_csv("batch_status")
    order_csv = find_csv("order_status")
    obr_csv = find_csv("order_batch_relationship")

    if not batch_csv:
        sys.exit("ERROR: batch_status CSV not found in FOLDER/")
    if not order_csv:
        sys.exit("ERROR: order_status CSV not found in FOLDER/")
    if not obr_csv:
        sys.exit("ERROR: order_batch_relationship CSV not found in FOLDER/")

    print(f"Files found:")
    print(f"  batch_status:             {os.path.basename(batch_csv)}")
    print(f"  order_status:             {os.path.basename(order_csv)}")
    print(f"  order_batch_relationship: {os.path.basename(obr_csv)}")
    print()

    driver = GraphDatabase.driver(uri, auth=(user, password))

    with driver.session(database=database) as session:
        # ── Step 0: Constraints & Indexes ──
        print("═══ Step 0: Creating constraints & indexes ═══")
        for stmt in CONSTRAINTS:
            try:
                session.run(stmt)
            except Exception as e:
                print(f"  WARN: {e}")
        for stmt in INDEXES:
            try:
                session.run(stmt)
            except Exception as e:
                print(f"  WARN: {e}")
        print("  Done.\n")

        # ── Step 1: batch_status → Nodes ──
        print("═══ Step 1: Loading batch_status → Nodes ═══")
        t0 = time.time()

        batch_rows = [transform_batch_status(r) for r in read_csv(batch_csv)]
        print(f"  Read {len(batch_rows):,} rows from batch_status")

        run_batched(session, BATCH_NODE_CYPHER, batch_rows, "Batch nodes")
        run_batched(session, MATERIAL_NODE_CYPHER, batch_rows, "Material nodes")
        run_batched(session, PLANT_NODE_CYPHER, batch_rows, "Plant nodes")
        run_batched(session, PRODUCT_FAMILY_CYPHER, batch_rows, "ProductFamily nodes")
        run_batched(session, PRODUCT_SUB_FAMILY_CYPHER, batch_rows, "ProductSubFamily nodes")
        run_batched(session, STORAGE_LOCATION_CYPHER, batch_rows, "StorageLocation nodes")
        run_batched(session, INSPECTION_LOT_CYPHER, batch_rows, "InspectionLot nodes")
        run_batched(session, SOURCE_SYSTEM_CYPHER, batch_rows, "SourceSystem nodes")
        run_batched(session, VENDOR_CYPHER, batch_rows, "Vendor nodes")
        run_batched(session, LIMS_LOT_CYPHER, batch_rows, "LIMSLot nodes")
        print(f"  Elapsed: {time.time() - t0:.1f}s\n")

        # ── Step 2: batch_status → Relationships ──
        print("═══ Step 2: Loading batch_status → Relationships ═══")
        t0 = time.time()
        run_batched(session, BATCH_MADE_OF_MATERIAL, batch_rows, "Batch-MADE_OF->Material")
        run_batched(session, BATCH_MANUFACTURED_AT_PLANT, batch_rows, "Batch-MANUFACTURED_AT->Plant")
        run_batched(session, BATCH_STORED_IN, batch_rows, "Batch-STORED_IN->StorageLocation")
        run_batched(session, BATCH_SUPPLIED_BY_VENDOR, batch_rows, "Batch-SUPPLIED_BY->Vendor")
        run_batched(session, BATCH_HAS_INSPECTION, batch_rows, "Batch-HAS_INSPECTION->InspectionLot")
        run_batched(session, BATCH_HAS_LIMS_LOT, batch_rows, "Batch-HAS_LIMS_LOT->LIMSLot")
        run_batched(session, BATCH_PRODUCED_BY_ORDER, batch_rows, "Batch-PRODUCED_BY->ProcessOrder")
        run_batched(session, BATCH_SOURCED_FROM, batch_rows, "Batch-SOURCED_FROM->SourceSystem")
        run_batched(session, MATERIAL_BELONGS_TO_SUBFAMILY, batch_rows, "Material-BELONGS_TO_SUBFAMILY->ProductSubFamily")
        run_batched(session, SUBFAMILY_BELONGS_TO_FAMILY, batch_rows, "ProductSubFamily-BELONGS_TO_FAMILY->ProductFamily")
        run_batched(session, PLANT_HAS_STORAGE, batch_rows, "Plant-HAS_STORAGE->StorageLocation")
        print(f"  Elapsed: {time.time() - t0:.1f}s\n")

        # ── Step 3: batch_status → QualityEvents & Notifications ──
        print("═══ Step 3: Loading batch_status → Quality Events & Notifications ═══")
        t0 = time.time()
        run_batched(session, QUALITY_EVENTS_FROM_BATCH, batch_rows, "QualityEvent nodes + relationships")
        run_batched(session, QUALITY_NOTIFICATIONS_FROM_BATCH, batch_rows, "QualityNotification nodes + relationships")
        print(f"  Elapsed: {time.time() - t0:.1f}s\n")

        # Free memory
        del batch_rows

        # ── Step 4: order_status → Nodes ──
        print("═══ Step 4: Loading order_status → Nodes ═══")
        t0 = time.time()

        order_rows = [transform_order_status(r) for r in read_csv(order_csv)]
        print(f"  Read {len(order_rows):,} rows from order_status")

        run_batched(session, PROCESS_ORDER_NODE_CYPHER, order_rows, "ProcessOrder nodes")
        run_batched(session, OPERATION_NODE_CYPHER, order_rows, "Operation nodes")
        run_batched(session, WORK_CENTRE_NODE_CYPHER, order_rows, "WorkCentre nodes")
        run_batched(session, PLANNED_ORDER_NODE_CYPHER, order_rows, "PlannedOrder nodes")
        # Also create Material/Plant/SourceSystem from order data
        run_batched(session, MATERIAL_NODE_CYPHER, order_rows, "Material nodes (from orders)")
        run_batched(session, SOURCE_SYSTEM_CYPHER, order_rows, "SourceSystem nodes (from orders)")
        run_batched(session, PRODUCT_FAMILY_CYPHER, order_rows, "ProductFamily nodes (from orders)")
        run_batched(session, PRODUCT_SUB_FAMILY_CYPHER, order_rows, "ProductSubFamily nodes (from orders)")
        print(f"  Elapsed: {time.time() - t0:.1f}s\n")

        # ── Step 5: order_status → Relationships ──
        print("═══ Step 5: Loading order_status → Relationships ═══")
        t0 = time.time()
        run_batched(session, ORDER_EXECUTED_AT_PLANT, order_rows, "ProcessOrder-EXECUTED_AT->Plant")
        run_batched(session, ORDER_PRODUCES_MATERIAL, order_rows, "ProcessOrder-PRODUCES->Material")
        run_batched(session, ORDER_HAS_OPERATION, order_rows, "ProcessOrder-HAS_OPERATION->Operation")
        run_batched(session, ORDER_ORIGINATES_FROM_PLANNED, order_rows, "ProcessOrder-ORIGINATES_FROM->PlannedOrder")
        run_batched(session, ORDER_HAS_INSPECTION, order_rows, "ProcessOrder-HAS_INSPECTION->InspectionLot")
        run_batched(session, OPERATION_USES_WORK_CENTRE, order_rows, "Operation-USES_WORK_CENTRE->WorkCentre")
        run_batched(session, OPERATION_NEXT_OPERATION, order_rows, "Operation-NEXT_OPERATION->Operation")
        run_batched(session, ORDER_SOURCED_FROM, order_rows, "ProcessOrder-SOURCED_FROM->SourceSystem")
        run_batched(session, MATERIAL_BELONGS_TO_SUBFAMILY, order_rows, "Material-BELONGS_TO_SUBFAMILY (from orders)")
        run_batched(session, SUBFAMILY_BELONGS_TO_FAMILY, order_rows, "SubFamily-BELONGS_TO_FAMILY (from orders)")
        print(f"  Elapsed: {time.time() - t0:.1f}s\n")

        # Free memory
        del order_rows

        # ── Step 6: order_batch_relationship → Relationships ──
        print("═══ Step 6: Loading order_batch_relationship → Relationships ═══")
        t0 = time.time()

        obr_rows = [transform_order_batch_relationship(r) for r in read_csv(obr_csv)]
        print(f"  Read {len(obr_rows):,} rows from order_batch_relationship")

        run_batched(session, CONSUMED_BY_CYPHER, obr_rows, "Batch-CONSUMED_BY->ProcessOrder")
        run_batched(session, RECOMMENDS_CYPHER, obr_rows, "PlannedOrder-RECOMMENDS->Batch")
        run_batched(session, ADJUSTS_CYPHER, obr_rows, "ProcessOrder-ADJUSTS->Batch")
        print(f"  Elapsed: {time.time() - t0:.1f}s\n")

        del obr_rows

        # ── Step 7: Graph Summary ──
        print("═══ Graph Summary ═══")
        result = session.run(
            "MATCH (n) RETURN labels(n)[0] AS label, count(n) AS count ORDER BY count DESC"
        )
        for record in result:
            print(f"  {record['label']:25s} {record['count']:>10,} nodes")

        print()
        result = session.run(
            "MATCH ()-[r]->() RETURN type(r) AS type, count(r) AS count ORDER BY count DESC"
        )
        for record in result:
            print(f"  {record['type']:30s} {record['count']:>10,} relationships")

    driver.close()
    print("\nLoad complete!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Load manufacturing CSV data into Neo4j (mapped to MIA Ontology)"
    )
    parser.add_argument("--uri", default="neo4j://127.0.0.1:7687",
                        help="Neo4j connection URI (default: neo4j://127.0.0.1:7687)")
    parser.add_argument("--user", default="neo4j",
                        help="Neo4j username (default: neo4j)")
    parser.add_argument("--password", required=True,
                        help="Neo4j password")
    parser.add_argument("--database", default="neo4j",
                        help="Neo4j database name (default: neo4j)")
    args = parser.parse_args()

    load(args.uri, args.user, args.password, args.database)

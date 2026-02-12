# Manufacturing Insight Agent - Data Dictionary

## Overview

This document provides a comprehensive data dictionary for all tables used by the Manufacturing Insight Agent (MIA) system. The data is organized into four categories:

1. **KPI Data Products** - Pre-aggregated metrics for quick lookups
2. **Analytical Data Products** - Enriched batch and order analytics
3. **Transactional Data Products** - Raw operational data from source systems
4. **Master Data Products** - Reference data for entities

---

## 1. KPI Data Products

### 1.1 KPI_STORE_MONTHLY

**Purpose**: Pre-aggregated monthly KPI metrics for site-level performance tracking

| Field Name | Data Type | Description | Unit | Target | Example Values |
|------------|-----------|-------------|------|--------|----------------|
| `MONTH` | datetime64[ns] | Calendar month for the reporting period | - | - | `2025-01`, `2025-12` |
| `SITE_ID` | string | Manufacturing site identifier | - | - | `FCTN-PLANT-01` |
| `PRODUCTION_VOLUME` | int64 | Total units produced in the month | units | - | `125000`, `98500` |
| `BATCH_COUNT` | int64 | Number of batches completed | count | - | `45`, `52` |
| `BATCH_YIELD_AVG_PCT` | float64 | Average batch yield percentage | % | 98% | `97.3`, `96.8` |
| `RFT_PCT` | float64 | Right First Time percentage | % | 92% | `64.0`, `78.5` |
| `SCHEDULE_ADHERENCE_PCT` | float64 | Percentage of batches meeting schedule | % | 95% | `88.2`, `91.5` |
| `AVG_CYCLE_TIME_HR` | float64 | Average batch cycle time | hours | - | `18.2`, `16.8` |
| `DEVIATIONS_PER_100_BATCHES` | float64 | Quality deviation rate | per 100 batches | <5 | `3.2`, `4.8` |
| `ALARMS_PER_1000_HOURS` | float64 | Equipment alarm frequency | per 1000 hours | - | `12.5`, `8.3` |
| `LAB_TURNAROUND_MEDIAN_DAYS` | float64 | Median LIMS turnaround time | days | - | `2.5`, `3.1` |
| `SUPPLIER_OTIF_PCT` | float64 | Supplier On-Time In-Full percentage | % | 95% | `92.3`, `88.7` |
| `OEE_PACKAGING_PCT` | float64 | Overall Equipment Effectiveness - Packaging | % | 80% | `76.0`, `74.5` |
| `TARGET_OTIF_PCT` | int64 | Target for OTIF metric | % | - | `95` |
| `TARGET_RFT_PCT` | int64 | Target for RFT metric | % | - | `92` |
| `TARGET_OEE_PACKAGING_PCT` | int64 | Target for OEE Packaging | % | - | `80` |
| `OTIF_RAG` | string | OTIF Red/Amber/Green status | - | - | `Green`, `Amber`, `Red` |
| `RFT_RAG` | string | RFT Red/Amber/Green status | - | - | `Green`, `Amber`, `Red` |
| `OEE_RAG` | string | OEE Red/Amber/Green status | - | - | `Green`, `Amber`, `Red` |

**Record Count**: ~13 records (monthly aggregates)

**Primary Key**: `MONTH` + `SITE_ID`

**Refresh Frequency**: Weekly from Collibra

---

### 1.2 KPI_STORE_WEEKLY

**Purpose**: Pre-aggregated weekly KPI metrics for more granular performance tracking

| Field Name | Data Type | Description | Unit | Target | Example Values |
|------------|-----------|-------------|------|--------|----------------|
| `ISO_WEEK` | int64 | ISO week number (1-52) | - | - | `1`, `26`, `52` |
| `SITE_ID` | string | Manufacturing site identifier | - | - | `FCTN-PLANT-01` |
| `PRODUCTION_VOLUME` | int64 | Total units produced in the week | units | - | `31250`, `28500` |
| `BATCH_COUNT` | int64 | Number of batches completed | count | - | `11`, `13` |
| `BATCH_YIELD_AVG_PCT` | float64 | Average batch yield percentage | % | 98% | `97.5`, `96.2` |
| `RFT_PCT` | float64 | Right First Time percentage | % | 92% | `66.0`, `72.5` |
| `SCHEDULE_ADHERENCE_PCT` | float64 | Percentage of batches meeting schedule | % | 95% | `87.5`, `93.2` |
| `AVG_CYCLE_TIME_HR` | float64 | Average batch cycle time | hours | - | `17.8`, `19.1` |
| `DEVIATIONS_PER_100_BATCHES` | float64 | Quality deviation rate | per 100 batches | <5 | `2.8`, `5.2` |
| `ALARMS_PER_1000_HOURS` | float64 | Equipment alarm frequency | per 1000 hours | - | `11.2`, `9.8` |
| `STOCKOUTS_COUNT` | int64 | Number of material stockout events | count | 0 | `0`, `2`, `5` |
| `OEE_PACKAGING_PCT` | float64 | Overall Equipment Effectiveness - Packaging | % | 80% | `78.2`, `73.8` |
| `MONTH` | datetime64[ns] | Parent month for the week | - | - | `2025-01`, `2025-12` |

**Record Count**: ~52 records (weekly aggregates per year)

**Primary Key**: `ISO_WEEK` + `SITE_ID`

**Refresh Frequency**: Weekly from Collibra

---

## 2. Analytical Data Products

### 2.1 ANALYTICS_BATCH_STATUS

**Purpose**: Enriched batch-level analytics combining MES, LIMS, and alarm data

| Field Name | Data Type | Description | Unit | Example Values |
|------------|-----------|-------------|------|----------------|
| `BATCH_ID` | string | Unique batch identifier | - | `B2025-00007`, `B2025-00123` |
| `ORDER_ID` | string | Parent production order | - | `ORD-2025-001` |
| `MATERIAL_ID` | string | Material/SKU being produced | - | `SKU_123`, `SKU_456` |
| `BATCH_SIZE` | int64 | Planned batch quantity | units | `5000`, `10000` |
| `UOM` | string | Unit of measure | - | `KG`, `L`, `EA` |
| `ROUTE` | string | Manufacturing route/recipe | - | `FORM-COAT-PACK` |
| `ACTUAL_START` | int64 | Actual batch start timestamp | epoch | - |
| `ACTUAL_END` | int64 | Actual batch end timestamp | epoch | - |
| `CYCLE_TIME_HR` | float64 | Total batch cycle time | hours | `18.2`, `22.5` |
| `YIELD_QTY` | int64 | Actual yield quantity | units | `4850`, `9720` |
| `YIELD_PCT` | float64 | Yield as percentage of batch size | % | `97.0`, `97.2` |
| `STATUS` | string | Final batch status | - | `Released`, `Quarantined`, `Rejected` |
| `DEVIATIONS_COUNT` | int64 | Number of quality deviations | count | `0`, `1`, `3` |
| `REWORK_FLAG` | boolean | Whether batch required rework | - | `true`, `false` |
| `PRIMARY_EQUIPMENT_ID` | string | Main equipment used | - | `VIAL-1`, `TAB-1` |
| `SCHEDULED_START` | int64 | Planned batch start timestamp | epoch | - |
| `SCHEDULED_END` | int64 | Planned batch end timestamp | epoch | - |
| `STD_YIELD_PCT` | float64 | Standard/expected yield | % | `98.0` |
| `STD_CYCLE_TIME_HR` | float64 | Standard/expected cycle time | hours | `16.0` |
| `STEPS` | int64 | Number of process steps | count | `6`, `8` |
| `WAIT_TIME_MIN` | int64 | Total wait/idle time | minutes | `120`, `180` |
| `ACTIVE_TIME_MIN` | int64 | Total active processing time | minutes | `960`, `1200` |
| `LIMS_FIRST_PASS` | int64 | LIMS test first pass indicator | 0/1 | `1`, `0` |
| `ALARM_COUNT` | float64 | Number of alarms during batch | count | `2.0`, `5.0` |
| `WAIT_TIME_HR` | float64 | Total wait/idle time | hours | `2.0`, `3.0` |
| `ACTIVE_TIME_HR` | float64 | Total active processing time | hours | `16.0`, `20.0` |
| `DELAY_VS_SCHEDULE_HR` | float64 | Delay from scheduled completion | hours | `-0.5`, `2.3` |
| `ON_TIME` | int64 | On-time completion indicator | 0/1 | `1`, `0` |
| `RFT` | int64 | Right First Time indicator | 0/1 | `1`, `0` |
| `ALARMS_PER_HR` | float64 | Alarm rate during batch | per hour | `0.11`, `0.28` |
| `MONTH` | datetime64[ns] | Month of batch completion | - | `2025-01` |
| `ISO_WEEK` | int64 | ISO week of batch completion | - | `1`, `52` |

**Record Count**: 376 batches

**Primary Key**: `BATCH_ID`

**Derived From**: MES_PASX_BATCHES + SAP_ORDERS + LIMS_RESULTS + EVENTS_ALARMS

---

### 2.2 ANALYTICS_ORDER_STATUS

**Purpose**: Order-level analytics with aggregated batch performance

| Field Name | Data Type | Description | Unit | Example Values |
|------------|-----------|-------------|------|----------------|
| `SITE_ID` | string | Manufacturing site identifier | - | `FCTN-PLANT-01` |
| `PLANT` | string | Plant name/code | - | `FCTN-PLANT-01` |
| `ORDER_ID` | string | Production order identifier | - | `ORD-2025-001` |
| `ORDER_TYPE` | string | Type of production order | - | `ZPRM`, `ZPRD` |
| `MATERIAL_ID` | string | Material/SKU being produced | - | `SKU_123` |
| `MATERIAL_DESC` | string | Material description | - | `Aspirin 500mg Tablets` |
| `UOM` | string | Unit of measure | - | `KG`, `EA` |
| `QTY_ORDERED` | int64 | Ordered quantity | units | `50000` |
| `SCHEDULED_START` | int64 | Planned order start | epoch | - |
| `SCHEDULED_END` | int64 | Planned order end | epoch | - |
| `PRIORITY` | string | Order priority | - | `High`, `Normal`, `Low` |
| `WORK_CENTER` | string | Production work center | - | `WC-FORM-01` |
| `BOM_VERSION` | string | Bill of Materials version | - | `BOM-V2.1` |
| `STD_YIELD_PCT` | float64 | Standard expected yield | % | `98.0` |
| `STD_CYCLE_TIME_HR` | float64 | Standard cycle time per batch | hours | `16.0` |
| `STATUS` | string | Order status | - | `Completed`, `In Progress`, `Planned` |
| `BATCHES` | int64 | Number of batches in order | count | `5`, `10` |
| `QTY_PRODUCED` | int64 | Actual quantity produced | units | `48500` |
| `RELEASED` | int64 | Number of released batches | count | `4` |
| `PCT_BATCHES_ON_TIME` | float64 | Percentage of on-time batches | % | `80.0` |
| `AVG_CYCLE_TIME_HR` | float64 | Average cycle time across batches | hours | `17.5` |
| `DEVIATION_COUNT` | int64 | Total deviations across batches | count | `3` |
| `QTY_IN_FULL` | boolean | Full quantity delivered | - | `true`, `false` |
| `ON_TIME` | int64 | Order on-time indicator | 0/1 | `1`, `0` |
| `OTIF` | int64 | On-Time In-Full indicator | 0/1 | `1`, `0` |
| `SCHEDULE_ADHERENCE_PCT` | float64 | Schedule adherence percentage | % | `85.0` |

**Record Count**: 107 orders

**Primary Key**: `ORDER_ID`

**Derived From**: SAP_ORDERS + MES_PASX_BATCHES (aggregated)

---

## 3. Transactional Data Products

### 3.1 SAP_ORDERS

**Purpose**: Production orders from SAP ERP

| Field Name | Data Type | Description | Unit | Example Values |
|------------|-----------|-------------|------|----------------|
| `site_id` | string | Manufacturing site identifier | - | `FCTN-PLANT-01` |
| `plant` | string | Plant code | - | `FCTN-PLANT-01` |
| `order_id` | string | Production order number | - | `ORD-2025-001` |
| `order_type` | string | Order type code | - | `ZPRM`, `ZPRD` |
| `material_id` | string | Material number | - | `SKU_123` |
| `material_desc` | string | Material description | - | `Aspirin 500mg` |
| `uom` | string | Unit of measure | - | `KG`, `EA` |
| `qty_ordered` | int64 | Order quantity | units | `50000` |
| `scheduled_start` | string | Planned start date/time | ISO 8601 | `2025-01-15T08:00:00` |
| `scheduled_end` | string | Planned end date/time | ISO 8601 | `2025-01-18T16:00:00` |
| `priority` | string | Order priority | - | `High`, `Normal` |
| `work_center` | string | Work center assignment | - | `WC-FORM-01` |
| `bom_version` | string | BOM version | - | `BOM-V2.1` |
| `std_yield_pct` | float64 | Standard yield percentage | % | `98.0` |
| `std_cycle_time_hr` | float64 | Standard cycle time | hours | `16.0` |
| `status` | string | Order status | - | `REL`, `TECO`, `CLSD` |

**Record Count**: 107

**Source System**: SAP S/4HANA

---

### 3.2 MES_PASX_BATCHES

**Purpose**: Batch execution data from MES (PAS-X)

| Field Name | Data Type | Description | Unit | Example Values |
|------------|-----------|-------------|------|----------------|
| `batch_id` | string | Unique batch identifier | - | `B2025-00007` |
| `order_id` | string | Parent production order | - | `ORD-2025-001` |
| `material_id` | string | Material being produced | - | `SKU_123` |
| `batch_size` | int64 | Planned batch size | units | `5000` |
| `uom` | string | Unit of measure | - | `KG` |
| `route` | string | Manufacturing route | - | `FORM-COAT-PACK` |
| `actual_start` | string | Actual start timestamp | ISO 8601 | `2025-01-15T08:15:00` |
| `actual_end` | string | Actual end timestamp | ISO 8601 | `2025-01-16T02:27:00` |
| `cycle_time_hr` | float64 | Actual cycle time | hours | `18.2` |
| `yield_qty` | int64 | Actual yield quantity | units | `4850` |
| `yield_pct` | float64 | Yield percentage | % | `97.0` |
| `status` | string | Batch status | - | `Released`, `Quarantined`, `Rejected` |
| `deviations_count` | int64 | Number of deviations | count | `1` |
| `rework_flag` | boolean | Rework required | - | `false` |
| `primary_equipment_id` | string | Main equipment | - | `VIAL-1` |

**Record Count**: 376

**Source System**: Werum PAS-X MES

**Status Distribution**: 87% Released, 7.4% Quarantined, 5.6% Rejected

---

### 3.3 MES_PASX_BATCH_STEPS

**Purpose**: Detailed batch step execution data

| Field Name | Data Type | Description | Unit | Example Values |
|------------|-----------|-------------|------|----------------|
| `batch_id` | string | Parent batch identifier | - | `B2025-00007` |
| `step_id` | string | Unique step identifier | - | `B2025-00007-FORM-01` |
| `step_code` | string | Step code | - | `FORM`, `COAT`, `PACK` |
| `step_name` | string | Step description | - | `Formulation`, `Coating` |
| `sequence` | int64 | Step sequence number | - | `1`, `2`, `3` |
| `step_start` | string | Step start timestamp | ISO 8601 | `2025-01-15T08:15:00` |
| `step_end` | string | Step end timestamp | ISO 8601 | `2025-01-15T14:30:00` |
| `duration_min` | int64 | Step duration | minutes | `375` |
| `wait_before_min` | int64 | Wait time before step | minutes | `30` |
| `target_temp_C` | int64 | Target temperature | Celsius | `25`, `40` |
| `target_pH` | float64 | Target pH value | - | `6.8`, `7.2` |
| `equipment_id` | string | Equipment used for step | - | `MIX-01`, `COAT-01` |

**Record Count**: 2,474

**Source System**: Werum PAS-X MES

**Use Case**: Calculate wait times between steps (e.g., formulation to packaging)

---

### 3.4 LIMS_RESULTS

**Purpose**: Laboratory test results from LIMS

| Field Name | Data Type | Description | Unit | Example Values |
|------------|-----------|-------------|------|----------------|
| `sample_id` | string | Sample identifier | - | `SAMP-2025-00123` |
| `batch_id` | string | Associated batch | - | `B2025-00007` |
| `material_id` | string | Material tested | - | `SKU_123` |
| `test_name` | string | Test name | - | `Assay`, `Dissolution` |
| `analyte` | string | Analyte measured | - | `API Content`, `Impurity A` |
| `result_value` | float64 | Test result | varies | `99.5`, `0.12` |
| `unit` | string | Result unit | - | `%`, `mg/L` |
| `spec_low` | float64 | Specification lower limit | varies | `98.0` |
| `spec_high` | float64 | Specification upper limit | varies | `102.0` |
| `result_status` | string | Pass/Fail status | - | `Pass`, `Fail`, `OOS` |
| `sampled_ts` | string | Sample collection time | ISO 8601 | `2025-01-15T14:00:00` |
| `received_ts` | string | Lab receipt time | ISO 8601 | `2025-01-15T15:30:00` |
| `approved_ts` | string | Result approval time | ISO 8601 | `2025-01-16T10:00:00` |
| `analyst_id` | string | Analyst identifier | - | `ANALYST-001` |
| `tat_days` | float64 | Turnaround time | days | `0.8`, `1.5` |

**Record Count**: 1,880

**Source System**: LIMS

---

### 3.5 EVENTS_ALARMS

**Purpose**: Equipment events and alarms

| Field Name | Data Type | Description | Unit | Example Values |
|------------|-----------|-------------|------|----------------|
| `timestamp` | string | Event timestamp | ISO 8601 | `2025-01-15T10:23:45` |
| `equipment_id` | string | Equipment identifier | - | `VIAL-1`, `MIX-01` |
| `batch_id` | string | Associated batch (if any) | - | `B2025-00007` |
| `step_id` | string | Associated step (if any) | - | `B2025-00007-FORM-01` |
| `event_type` | string | Type of event | - | `ALARM`, `WARNING`, `INFO` |
| `code` | string | Event/alarm code | - | `ALM-101`, `WRN-205` |
| `severity` | string | Severity level | - | `Critical`, `High`, `Medium`, `Low` |
| `description` | string | Event description | - | `Temperature out of range` |
| `duration_sec` | int64 | Event duration | seconds | `120`, `3600` |
| `ack_ts` | string | Acknowledgment time | ISO 8601 | `2025-01-15T10:25:00` |
| `cleared_ts` | string | Clear time | ISO 8601 | `2025-01-15T10:35:00` |

**Record Count**: 345

**Source System**: SCADA/Historian

---

### 3.6 PROCUREMENT_POS

**Purpose**: Purchase orders for materials

| Field Name | Data Type | Description | Unit | Example Values |
|------------|-----------|-------------|------|----------------|
| `po_id` | string | Purchase order number | - | `PO-2025-00123` |
| `vendor_id` | string | Vendor identifier | - | `VEND-001` |
| `material_id` | string | Material ordered | - | `RM-001` |
| `qty_ordered` | int64 | Quantity ordered | units | `1000` |
| `uom` | string | Unit of measure | - | `KG` |
| `order_date` | string | PO creation date | ISO 8601 | `2025-01-01` |
| `promised_date` | string | Vendor promised date | ISO 8601 | `2025-01-15` |
| `delivery_date` | string | Actual delivery date | ISO 8601 | `2025-01-14` |
| `status` | string | PO status | - | `Received`, `Pending`, `Partial` |
| `price_per_uom` | float64 | Unit price | currency | `25.50` |
| `currency` | string | Currency code | - | `USD`, `EUR` |
| `month` | string | Order month | - | `2025-01` |
| `on_time` | int64 | On-time delivery indicator | 0/1 | `1`, `0` |

**Record Count**: 182

**Source System**: SAP MM

---

### 3.7 GOODS_RECEIPTS

**Purpose**: Material receipts into inventory

| Field Name | Data Type | Description | Unit | Example Values |
|------------|-----------|-------------|------|----------------|
| `gr_id` | string | Goods receipt number | - | `GR-2025-00456` |
| `po_id` | string | Related purchase order | - | `PO-2025-00123` |
| `material_id` | string | Material received | - | `RM-001` |
| `qty_received` | int64 | Quantity received | units | `1000` |
| `uom` | string | Unit of measure | - | `KG` |
| `receipt_date` | string | Receipt date | ISO 8601 | `2025-01-14` |
| `lot_id` | string | Lot/batch number | - | `LOT-2025-001` |
| `coa_status` | string | Certificate of Analysis status | - | `Approved`, `Pending` |
| `qc_release_ts` | string | QC release timestamp | ISO 8601 | `2025-01-15T14:00:00` |

**Record Count**: 244

**Source System**: SAP WM

---

### 3.8 INVENTORY_SNAPSHOTS

**Purpose**: Daily inventory position snapshots

| Field Name | Data Type | Description | Unit | Example Values |
|------------|-----------|-------------|------|----------------|
| `date` | string | Snapshot date | ISO 8601 | `2025-01-15` |
| `material_id` | string | Material identifier | - | `RM-001`, `SKU_123` |
| `on_hand_qty` | float64 | Quantity on hand | units | `5000.0` |
| `uom` | string | Unit of measure | - | `KG` |
| `lot_count` | int64 | Number of lots | count | `3` |
| `days_on_hand` | float64 | Days of inventory coverage | days | `15.5` |
| `iso_week` | int64 | ISO week number | - | `3` |

**Record Count**: 1,325

**Source System**: SAP WM

---

### 3.9 CONSUMPTION_MOVEMENTS

**Purpose**: Material consumption/issue transactions

| Field Name | Data Type | Description | Unit | Example Values |
|------------|-----------|-------------|------|----------------|
| `move_id` | string | Movement document number | - | `MOV-2025-00789` |
| `batch_id` | string | Consuming batch | - | `B2025-00007` |
| `material_id` | string | Material consumed | - | `RM-001` |
| `qty_issued` | float64 | Quantity issued | units | `500.0` |
| `uom` | string | Unit of measure | - | `KG` |
| `issue_date` | string | Issue date | ISO 8601 | `2025-01-15` |
| `storage_location` | string | Source storage location | - | `SLOC-01` |
| `lot_id` | string | Lot consumed | - | `LOT-2025-001` |

**Record Count**: 3,161

**Source System**: SAP WM

---

## 4. Master Data Products

### 4.1 MATERIALS_MASTER

**Purpose**: Material/SKU master data

| Field Name | Data Type | Description | Unit | Example Values |
|------------|-----------|-------------|------|----------------|
| `MATERIAL_ID` | string | Unique material identifier | - | `SKU_123`, `RM-001` |
| `DESCRIPTION` | string | Material description | - | `Aspirin 500mg Tablets` |
| `UOM` | string | Base unit of measure | - | `KG`, `EA` |
| `STD_BATCH_SIZE` | float64 | Standard batch size | units | `5000.0` |
| `VALUE_STREAM` | string | Value stream assignment | - | `Oral Solid Dose` |
| `ROUTE` | string | Default manufacturing route | - | `FORM-COAT-PACK` |
| `TYPE` | string | Material type | - | `FG`, `SEMI`, `RM`, `PM` |
| `LEAD_TIME_DAYS` | float64 | Manufacturing lead time | days | `5.0` |
| `CRITICAL` | string | Critical material flag | - | `Yes`, `No` |

**Record Count**: 30

**Source System**: SAP MM

---

### 4.2 EQUIPMENT_MASTER

**Purpose**: Manufacturing equipment master data

| Field Name | Data Type | Description | Unit | Example Values |
|------------|-----------|-------------|------|----------------|
| `EQUIPMENT_ID` | string | Unique equipment identifier | - | `VIAL-1`, `MIX-01` |
| `TYPE` | string | Equipment type | - | `Mixer`, `Coater`, `Packaging Line` |
| `AREA` | string | Manufacturing area | - | `Formulation`, `Packaging` |
| `LINE` | string | Production line | - | `Line-1`, `Line-2` |
| `CAPACITY_L` | float64 | Equipment capacity | liters | `500.0`, `1000.0` |

**Record Count**: 8

**Source System**: SAP PM

---

### 4.3 VENDORS_MASTER

**Purpose**: Supplier/vendor master data

| Field Name | Data Type | Description | Unit | Example Values |
|------------|-----------|-------------|------|----------------|
| `VENDOR_ID` | string | Unique vendor identifier | - | `VEND-001` |
| `NAME` | string | Vendor name | - | `Acme Chemicals Inc.` |
| `PREFERRED` | string | Preferred vendor flag | - | `Yes`, `No` |

**Record Count**: 15

**Source System**: SAP MM

---

## 5. KPI Definitions & Calculations

### 5.1 Core KPIs

| KPI Name | Formula | Target | RAG Thresholds |
|----------|---------|--------|----------------|
| **Batch Yield** | `(YIELD_QTY / BATCH_SIZE) × 100` | 98% | G: ≥98%, A: 95-98%, R: <95% |
| **RFT (Right First Time)** | `Batches with no deviations AND no rework / Total Batches × 100` | 92% | G: ≥92%, A: 80-92%, R: <80% |
| **OEE Packaging** | `Availability × Performance × Quality` | 80% | G: ≥80%, A: 70-80%, R: <70% |
| **Schedule Adherence** | `On-time batches / Total batches × 100` | 95% | G: ≥95%, A: 85-95%, R: <85% |
| **OTIF (On-Time In-Full)** | `Orders delivered on-time AND in-full / Total orders × 100` | 95% | G: ≥95%, A: 90-95%, R: <90% |
| **Deviations per 100 Batches** | `Total deviations / Total batches × 100` | <5 | G: <5, A: 5-10, R: >10 |

### 5.2 Derived Metrics

| Metric | Calculation | Source Tables |
|--------|-------------|---------------|
| **Average Cycle Time** | `AVG(cycle_time_hr)` | MES_PASX_BATCHES |
| **Wait Time (Step-to-Step)** | `Step_N_Start - Step_N-1_End` | MES_PASX_BATCH_STEPS |
| **Lab Turnaround** | `approved_ts - sampled_ts` | LIMS_RESULTS |
| **Supplier OTIF** | `POs on-time AND in-full / Total POs` | PROCUREMENT_POS, GOODS_RECEIPTS |
| **Alarms per 1000 Hours** | `Alarm count / Operating hours × 1000` | EVENTS_ALARMS |

---

## 6. Entity Relationships

```
                    ┌─────────────────┐
                    │  MATERIALS_MASTER│
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
         ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│   SAP_ORDERS    │ │INVENTORY_SNAPSHOT│ │ PROCUREMENT_POS │
└────────┬────────┘ └─────────────────┘ └────────┬────────┘
         │                                       │
         ▼                                       ▼
┌─────────────────┐                     ┌─────────────────┐
│ MES_PASX_BATCHES│                     │ GOODS_RECEIPTS  │
└────────┬────────┘                     └─────────────────┘
         │
    ┌────┴────┬────────────────┐
    │         │                │
    ▼         ▼                ▼
┌─────────┐ ┌───────────┐ ┌─────────────┐
│BATCH_   │ │LIMS_      │ │EVENTS_      │
│STEPS    │ │RESULTS    │ │ALARMS       │
└─────────┘ └───────────┘ └─────────────┘
         │
         ▼
┌─────────────────┐
│CONSUMPTION_     │
│MOVEMENTS        │
└─────────────────┘
```

### Key Relationships

| Parent Table | Child Table | Join Key | Relationship |
|--------------|-------------|----------|--------------|
| MATERIALS_MASTER | SAP_ORDERS | material_id | 1:N |
| MATERIALS_MASTER | MES_PASX_BATCHES | material_id | 1:N |
| MATERIALS_MASTER | PROCUREMENT_POS | material_id | 1:N |
| SAP_ORDERS | MES_PASX_BATCHES | order_id | 1:N |
| MES_PASX_BATCHES | MES_PASX_BATCH_STEPS | batch_id | 1:N |
| MES_PASX_BATCHES | LIMS_RESULTS | batch_id | 1:N |
| MES_PASX_BATCHES | EVENTS_ALARMS | batch_id | 1:N |
| MES_PASX_BATCHES | CONSUMPTION_MOVEMENTS | batch_id | 1:N |
| PROCUREMENT_POS | GOODS_RECEIPTS | po_id | 1:N |
| EQUIPMENT_MASTER | MES_PASX_BATCHES | equipment_id | 1:N |
| VENDORS_MASTER | PROCUREMENT_POS | vendor_id | 1:N |

---

## 7. Sample Queries for KPI Agent

### 7.1 Simple KPI Lookups

```sql
-- Monthly batch yield
SELECT MONTH, BATCH_YIELD_AVG_PCT, TARGET_RFT_PCT, RFT_RAG
FROM KPI_STORE_MONTHLY
WHERE SITE_ID = 'FCTN-PLANT-01'
ORDER BY MONTH DESC
LIMIT 3;

-- Weekly OEE trend
SELECT ISO_WEEK, OEE_PACKAGING_PCT
FROM KPI_STORE_WEEKLY
WHERE MONTH >= '2025-10-01'
ORDER BY ISO_WEEK;
```

### 7.2 Batch-Level Queries

```sql
-- Batch waiting time (formulation to packaging)
SELECT
    b.batch_id,
    s1.step_end AS formulation_end,
    s2.step_start AS packaging_start,
    TIMESTAMPDIFF(MINUTE, s1.step_end, s2.step_start) AS wait_time_min
FROM MES_PASX_BATCHES b
JOIN MES_PASX_BATCH_STEPS s1 ON b.batch_id = s1.batch_id AND s1.step_code = 'FORM'
JOIN MES_PASX_BATCH_STEPS s2 ON b.batch_id = s2.batch_id AND s2.step_code = 'PACK'
WHERE b.batch_id = 'B2025-00007';

-- Equipment performance breakdown
SELECT
    primary_equipment_id,
    COUNT(*) as batch_count,
    AVG(yield_pct) as avg_yield,
    SUM(CASE WHEN status = 'Released' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as rft_pct
FROM ANALYTICS_BATCH_STATUS
GROUP BY primary_equipment_id
ORDER BY rft_pct ASC;
```

---

## 8. Glossary

| Term | Definition |
|------|------------|
| **RFT** | Right First Time - batches released without deviations or rework |
| **OEE** | Overall Equipment Effectiveness - measure of manufacturing productivity |
| **OTIF** | On-Time In-Full - orders delivered as promised |
| **RAG** | Red/Amber/Green status indicator |
| **TAT** | Turnaround Time - time from sample to result |
| **BOM** | Bill of Materials - recipe/formula components |
| **MES** | Manufacturing Execution System (PAS-X) |
| **LIMS** | Laboratory Information Management System |
| **CoA** | Certificate of Analysis |
| **QC** | Quality Control |

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-12 | MIA Team | Initial data dictionary |

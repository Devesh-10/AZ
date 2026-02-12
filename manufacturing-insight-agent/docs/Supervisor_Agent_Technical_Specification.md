# Supervisor Agent - Technical Specification

**Document Version:** 1.0
**Date:** February 2026
**System:** Manufacturing Insight Agent (MIA)
**Author:** AstraZeneca Digital Engineering Team

---

## Executive Summary

The Supervisor Agent is the intelligent routing layer of the Manufacturing Insight Agent (MIA) system. It interprets natural language queries from users, matches requested metrics against the KPI catalogue, and routes queries to the appropriate downstream agent for processing.

**Key Capabilities:**
- Natural language understanding for manufacturing domain
- Real-time KPI entity matching against data catalogue
- Intelligent query classification and routing
- Sub-500ms routing decisions

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER INTERFACE                                  │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SUPERVISOR AGENT                                   │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │   EXTRACT   │───▶│    MATCH    │───▶│  CLASSIFY   │───▶│    ROUTE    │  │
│  │  Entities   │    │  Against    │    │   Intent    │    │   Query     │  │
│  │             │    │ KPI Catalog │    │             │    │             │  │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘  │
│                            │                                                 │
│                            ▼                                                 │
│                   ┌─────────────────┐                                       │
│                   │  KPI CATALOGUE  │                                       │
│                   │  (Embedded JSON)│                                       │
│                   └─────────────────┘                                       │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
                    ▼                           ▼
        ┌───────────────────┐       ┌───────────────────┐
        │     KPI AGENT     │       │   ANALYST AGENT   │
        │                   │       │                   │
        │  • Fast lookups   │       │  • Root cause     │
        │  • Pre-aggregated │       │  • Complex joins  │
        │  • Monthly/Weekly │       │  • Batch-level    │
        └───────────────────┘       └───────────────────┘
```

---

## 2. Supervisor Agent Prompt

The following prompt is embedded in the Supervisor Agent and executed for each user query:

```
You are the Supervisor Agent for AstraZeneca's Manufacturing Insight Agent.
Route user queries to the correct downstream agent.

## KPI Catalogue

{{KPI_CATALOGUE}}

## Field Aliases

| User Says                  | Maps To                    |
|----------------------------|----------------------------|
| yield, batch yield         | BATCH_YIELD_AVG_PCT        |
| RFT, right first time      | RFT_PCT                    |
| OEE, equipment effectiveness| OEE_PACKAGING_PCT         |
| cycle time                 | AVG_CYCLE_TIME_HR          |
| deviations                 | DEVIATIONS_PER_100_BATCHES |
| alarms                     | ALARMS_PER_1000_HOURS      |
| production, volume         | PRODUCTION_VOLUME          |
| batches                    | BATCH_COUNT                |
| schedule adherence         | SCHEDULE_ADHERENCE_PCT     |
| lab turnaround, TAT        | LAB_TURNAROUND_MEDIAN_DAYS |
| supplier OTIF              | SUPPLIER_OTIF_PCT          |
| stockouts                  | STOCKOUTS_COUNT            |

## Routing Rules

1. **Extract** from query: metric, time range, batch_id, filters
2. **Match** extracted metric against KPI_CATALOGUE.tables[*].fields[].field_name
3. **Route** based on:

| Match? | Query Type                        | Route          |
|--------|-----------------------------------|----------------|
| Yes    | Simple lookup (show, what is, get)| KPI_AGENT      |
| Yes    | Analysis (why, improve, root cause)| ANALYST_AGENT |
| No     | Batch-level, equipment, deviations| ANALYST_AGENT  |
| -      | Not manufacturing related         | REJECT         |

## Patterns

- **Time**: (last|past) N (month|week)s? → set granularity
- **Batch ID**: B\d{4}-\d{5} → route to ANALYST
- **Weekly-only fields**: STOCKOUTS_COUNT, ISO_WEEK
- **Monthly-only fields**: LAB_TURNAROUND_MEDIAN_DAYS, SUPPLIER_OTIF_PCT, *_RAG, TARGET_*

## Output

{
  "intent": "KPI_SIMPLE|KPI_COMPLEX|COMPLEX|REJECT",
  "entities": {
    "metric": "FIELD_NAME|null",
    "time": {"n": 3, "unit": "month"},
    "batch_id": "string|null"
  },
  "match": {
    "found": true,
    "table": "KPI_STORE_MONTHLY|KPI_STORE_WEEKLY",
    "field": "FIELD_NAME"
  },
  "route": "KPI_AGENT|ANALYST_AGENT",
  "reason": "brief explanation"
}
```

---

## 3. KPI Catalogue Schema

The `{{KPI_CATALOGUE}}` placeholder is replaced at runtime with the following JSON structure:

```json
{
  "category": "kpi_data_products",
  "tables": {
    "KPI_STORE_MONTHLY": {
      "record_count": 13,
      "fields": [
        {"field_name": "MONTH", "data_type": "datetime64[ns]", "description": "Calendar month (YYYY-MM)"},
        {"field_name": "SITE_ID", "data_type": "object", "description": "Manufacturing site identifier"},
        {"field_name": "PRODUCTION_VOLUME", "data_type": "int64", "description": "Total production volume"},
        {"field_name": "BATCH_COUNT", "data_type": "int64", "description": "Number of batches"},
        {"field_name": "BATCH_YIELD_AVG_PCT", "data_type": "float64", "description": "Average batch yield %"},
        {"field_name": "RFT_PCT", "data_type": "float64", "description": "Right First Time %"},
        {"field_name": "SCHEDULE_ADHERENCE_PCT", "data_type": "float64", "description": "Schedule adherence %"},
        {"field_name": "AVG_CYCLE_TIME_HR", "data_type": "float64", "description": "Average cycle time (hours)"},
        {"field_name": "DEVIATIONS_PER_100_BATCHES", "data_type": "float64", "description": "Deviation rate"},
        {"field_name": "ALARMS_PER_1000_HOURS", "data_type": "float64", "description": "Alarm frequency"},
        {"field_name": "LAB_TURNAROUND_MEDIAN_DAYS", "data_type": "float64", "description": "Lab TAT (days)"},
        {"field_name": "SUPPLIER_OTIF_PCT", "data_type": "float64", "description": "Supplier OTIF %"},
        {"field_name": "OEE_PACKAGING_PCT", "data_type": "float64", "description": "OEE Packaging %"},
        {"field_name": "TARGET_OTIF_PCT", "data_type": "int64", "description": "OTIF target"},
        {"field_name": "TARGET_RFT_PCT", "data_type": "int64", "description": "RFT target"},
        {"field_name": "TARGET_OEE_PACKAGING_PCT", "data_type": "int64", "description": "OEE target"},
        {"field_name": "OTIF_RAG", "data_type": "object", "description": "OTIF RAG status"},
        {"field_name": "RFT_RAG", "data_type": "object", "description": "RFT RAG status"},
        {"field_name": "OEE_RAG", "data_type": "object", "description": "OEE RAG status"}
      ]
    },
    "KPI_STORE_WEEKLY": {
      "record_count": 52,
      "fields": [
        {"field_name": "ISO_WEEK", "data_type": "int64", "description": "ISO week number (1-52)"},
        {"field_name": "SITE_ID", "data_type": "object", "description": "Manufacturing site identifier"},
        {"field_name": "PRODUCTION_VOLUME", "data_type": "int64", "description": "Weekly production volume"},
        {"field_name": "BATCH_COUNT", "data_type": "int64", "description": "Weekly batch count"},
        {"field_name": "BATCH_YIELD_AVG_PCT", "data_type": "float64", "description": "Weekly average yield %"},
        {"field_name": "RFT_PCT", "data_type": "float64", "description": "Weekly RFT %"},
        {"field_name": "SCHEDULE_ADHERENCE_PCT", "data_type": "float64", "description": "Weekly schedule adherence %"},
        {"field_name": "AVG_CYCLE_TIME_HR", "data_type": "float64", "description": "Weekly cycle time (hours)"},
        {"field_name": "DEVIATIONS_PER_100_BATCHES", "data_type": "float64", "description": "Weekly deviation rate"},
        {"field_name": "ALARMS_PER_1000_HOURS", "data_type": "float64", "description": "Weekly alarm rate"},
        {"field_name": "STOCKOUTS_COUNT", "data_type": "int64", "description": "Stockout events count"},
        {"field_name": "OEE_PACKAGING_PCT", "data_type": "float64", "description": "Weekly OEE %"},
        {"field_name": "MONTH", "data_type": "datetime64[ns]", "description": "Parent month"}
      ]
    }
  }
}
```

---

## 4. Processing Flow

### 4.1 Step-by-Step Process

```
┌──────────────────────────────────────────────────────────────────────────┐
│ STEP 1: ENTITY EXTRACTION                                                │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  User Query: "What is the batch yield for last 3 months?"                │
│                                                                          │
│  Extracted:                                                              │
│  ├── Metric: "batch yield"                                               │
│  ├── Time Range: 3 months                                                │
│  ├── Granularity: monthly                                                │
│  └── Batch ID: null                                                      │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ STEP 2: FIELD ALIAS RESOLUTION                                           │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  "batch yield" ──────────────────────────▶ BATCH_YIELD_AVG_PCT           │
│                                                                          │
│  Using Field Aliases Table:                                              │
│  ┌─────────────────────┬────────────────────────┐                        │
│  │ User Says           │ Maps To                │                        │
│  ├─────────────────────┼────────────────────────┤                        │
│  │ yield, batch yield  │ BATCH_YIELD_AVG_PCT    │ ◀── MATCH              │
│  └─────────────────────┴────────────────────────┘                        │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ STEP 3: KPI CATALOGUE MATCHING                                           │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Check: BATCH_YIELD_AVG_PCT ∈ KPI_CATALOGUE.tables[*].fields[]?          │
│                                                                          │
│  KPI_STORE_MONTHLY.fields:                                               │
│  ├── MONTH                                                               │
│  ├── SITE_ID                                                             │
│  ├── PRODUCTION_VOLUME                                                   │
│  ├── BATCH_COUNT                                                         │
│  ├── BATCH_YIELD_AVG_PCT  ◀────────────────────── ✅ FOUND               │
│  ├── RFT_PCT                                                             │
│  └── ...                                                                 │
│                                                                          │
│  Result: MATCH FOUND in KPI_STORE_MONTHLY                                │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ STEP 4: INTENT CLASSIFICATION                                            │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Query Keywords: "What is..."                                            │
│                                                                          │
│  Intent Patterns:                                                        │
│  ├── Simple: "show", "what is", "get", "display" ──▶ KPI_SIMPLE          │
│  ├── Analysis: "why", "how to improve", "root cause" ──▶ KPI_COMPLEX     │
│  └── Out of scope: non-manufacturing terms ──▶ REJECT                    │
│                                                                          │
│  Classification: KPI_SIMPLE (simple lookup)                              │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ STEP 5: ROUTING DECISION                                                 │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Decision Matrix:                                                        │
│  ┌─────────┬─────────────────┬────────────────┐                          │
│  │ Match?  │ Intent          │ Route          │                          │
│  ├─────────┼─────────────────┼────────────────┤                          │
│  │ ✅ Yes  │ KPI_SIMPLE      │ KPI_AGENT      │ ◀── SELECTED             │
│  │ ✅ Yes  │ KPI_COMPLEX     │ ANALYST_AGENT  │                          │
│  │ ❌ No   │ COMPLEX         │ ANALYST_AGENT  │                          │
│  │ -       │ REJECT          │ USER           │                          │
│  └─────────┴─────────────────┴────────────────┘                          │
│                                                                          │
│  Route: KPI_AGENT                                                        │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Output Generated

```json
{
  "intent": "KPI_SIMPLE",
  "entities": {
    "metric": "BATCH_YIELD_AVG_PCT",
    "time": {"n": 3, "unit": "month"},
    "batch_id": null
  },
  "match": {
    "found": true,
    "table": "KPI_STORE_MONTHLY",
    "field": "BATCH_YIELD_AVG_PCT"
  },
  "route": "KPI_AGENT",
  "reason": "Direct KPI lookup - metric exists in monthly table"
}
```

---

## 5. Routing Decision Matrix

### 5.1 Complete Decision Logic

| KPI Match | Query Intent | Keywords | Route | Rationale |
|:---------:|:-------------|:---------|:------|:----------|
| ✅ Yes | Simple Lookup | "show", "what is", "get", "display" | **KPI_AGENT** | Pre-aggregated data available |
| ✅ Yes | Trend Analysis | "trend", "over time", "compare months" | **KPI_AGENT** | Can be derived from KPI tables |
| ✅ Yes | Target Comparison | "vs target", "meeting target" | **KPI_AGENT** | Target fields available in KPI |
| ✅ Yes | Root Cause | "why", "reason", "root cause" | **ANALYST_AGENT** | Requires transactional drill-down |
| ✅ Yes | Improvement | "how to improve", "recommendations" | **ANALYST_AGENT** | Requires analysis of contributing factors |
| ❌ No | Batch-Level | Batch ID pattern (B2025-XXXXX) | **ANALYST_AGENT** | Requires MES transactional data |
| ❌ No | Equipment-Level | Equipment ID, specific machine | **ANALYST_AGENT** | Requires equipment logs |
| ❌ No | Step Timing | "waiting time", "step duration" | **ANALYST_AGENT** | Requires batch step data |
| - | Out of Scope | Non-manufacturing topics | **REJECT** | Not supported |

### 5.2 Field Availability by Table

| Field | Monthly | Weekly | Notes |
|:------|:-------:|:------:|:------|
| BATCH_YIELD_AVG_PCT | ✅ | ✅ | Available in both |
| RFT_PCT | ✅ | ✅ | Available in both |
| OEE_PACKAGING_PCT | ✅ | ✅ | Available in both |
| AVG_CYCLE_TIME_HR | ✅ | ✅ | Available in both |
| PRODUCTION_VOLUME | ✅ | ✅ | Available in both |
| BATCH_COUNT | ✅ | ✅ | Available in both |
| SCHEDULE_ADHERENCE_PCT | ✅ | ✅ | Available in both |
| DEVIATIONS_PER_100_BATCHES | ✅ | ✅ | Available in both |
| ALARMS_PER_1000_HOURS | ✅ | ✅ | Available in both |
| LAB_TURNAROUND_MEDIAN_DAYS | ✅ | ❌ | Monthly only |
| SUPPLIER_OTIF_PCT | ✅ | ❌ | Monthly only |
| TARGET_* fields | ✅ | ❌ | Monthly only |
| *_RAG fields | ✅ | ❌ | Monthly only |
| STOCKOUTS_COUNT | ❌ | ✅ | Weekly only |
| ISO_WEEK | ❌ | ✅ | Weekly only |

---

## 6. Test Scenarios & Expected Results

### 6.1 Scenario Summary

| # | Test Scenario | Query Example | Expected Route |
|:-:|:--------------|:--------------|:---------------|
| 1 | Simple KPI Lookup | "What is batch yield?" | KPI_AGENT |
| 2 | KPI with Time Filter | "Show RFT for last 3 months" | KPI_AGENT |
| 3 | Weekly-Only Metric | "How many stockouts last week?" | KPI_AGENT |
| 4 | Root Cause Analysis | "Why is RFT below target?" | ANALYST_AGENT |
| 5 | Improvement Query | "How can we improve OEE?" | ANALYST_AGENT |
| 6 | Batch-Level Query | "Status of batch B2025-00007?" | ANALYST_AGENT |
| 7 | Equipment Query | "Performance of VIAL-1?" | ANALYST_AGENT |
| 8 | Step Timing Query | "Waiting time between steps?" | ANALYST_AGENT |
| 9 | Out of Scope | "What's the weather today?" | REJECT |
| 10 | Target Comparison | "Is OEE meeting target?" | KPI_AGENT |

### 6.2 Detailed Test Cases

#### Test Case 1: Simple KPI Lookup (Monthly)

**Input:**
```
"What is the batch yield for last 3 months?"
```

**Processing:**
| Step | Action | Result |
|:-----|:-------|:-------|
| Extract | Parse metric | "batch yield" |
| Extract | Parse time | 3 months |
| Alias | Map to field | BATCH_YIELD_AVG_PCT |
| Match | Check KPI catalogue | ✅ Found in KPI_STORE_MONTHLY |
| Classify | Detect intent | "What is" → KPI_SIMPLE |
| Route | Apply rules | KPI_AGENT |

**Output:**
```json
{
  "intent": "KPI_SIMPLE",
  "entities": {
    "metric": "BATCH_YIELD_AVG_PCT",
    "time": {"n": 3, "unit": "month"},
    "batch_id": null
  },
  "match": {
    "found": true,
    "table": "KPI_STORE_MONTHLY",
    "field": "BATCH_YIELD_AVG_PCT"
  },
  "route": "KPI_AGENT",
  "reason": "Direct KPI lookup"
}
```

---

#### Test Case 2: Weekly-Only Metric

**Input:**
```
"Show me stockouts for past 4 weeks"
```

**Processing:**
| Step | Action | Result |
|:-----|:-------|:-------|
| Extract | Parse metric | "stockouts" |
| Extract | Parse time | 4 weeks |
| Alias | Map to field | STOCKOUTS_COUNT |
| Match | Check KPI catalogue | ✅ Found in KPI_STORE_WEEKLY only |
| Classify | Detect intent | "Show me" → KPI_SIMPLE |
| Route | Apply rules | KPI_AGENT |

**Output:**
```json
{
  "intent": "KPI_SIMPLE",
  "entities": {
    "metric": "STOCKOUTS_COUNT",
    "time": {"n": 4, "unit": "week"},
    "batch_id": null
  },
  "match": {
    "found": true,
    "table": "KPI_STORE_WEEKLY",
    "field": "STOCKOUTS_COUNT"
  },
  "route": "KPI_AGENT",
  "reason": "STOCKOUTS_COUNT available in weekly table"
}
```

---

#### Test Case 3: Root Cause Analysis

**Input:**
```
"Why is our RFT below target?"
```

**Processing:**
| Step | Action | Result |
|:-----|:-------|:-------|
| Extract | Parse metric | "RFT" |
| Extract | Parse comparison | "below target" |
| Alias | Map to field | RFT_PCT, TARGET_RFT_PCT |
| Match | Check KPI catalogue | ✅ Found in KPI_STORE_MONTHLY |
| Classify | Detect intent | "Why" → KPI_COMPLEX |
| Route | Apply rules | ANALYST_AGENT |

**Output:**
```json
{
  "intent": "KPI_COMPLEX",
  "entities": {
    "metric": "RFT_PCT",
    "time": null,
    "batch_id": null
  },
  "match": {
    "found": true,
    "table": "KPI_STORE_MONTHLY",
    "field": "RFT_PCT"
  },
  "route": "ANALYST_AGENT",
  "reason": "Root cause analysis requires transactional data"
}
```

---

#### Test Case 4: Batch-Level Query (No KPI Match)

**Input:**
```
"What is the waiting time between formulation and packaging for batch B2025-00007?"
```

**Processing:**
| Step | Action | Result |
|:-----|:-------|:-------|
| Extract | Parse metric | "waiting time" |
| Extract | Parse batch ID | B2025-00007 |
| Alias | Map to field | No match |
| Match | Check KPI catalogue | ❌ Not found |
| Classify | Detect intent | Batch-level → COMPLEX |
| Route | Apply rules | ANALYST_AGENT |

**Output:**
```json
{
  "intent": "COMPLEX",
  "entities": {
    "metric": null,
    "time": null,
    "batch_id": "B2025-00007"
  },
  "match": {
    "found": false,
    "table": null,
    "field": null
  },
  "route": "ANALYST_AGENT",
  "reason": "Batch-level step timing not in KPI tables"
}
```

---

#### Test Case 5: Out of Scope

**Input:**
```
"What is the stock price of AstraZeneca?"
```

**Processing:**
| Step | Action | Result |
|:-----|:-------|:-------|
| Extract | Parse metric | "stock price" |
| Alias | Map to field | No match |
| Match | Check KPI catalogue | ❌ Not found |
| Classify | Detect intent | Non-manufacturing → REJECT |
| Route | Apply rules | REJECT |

**Output:**
```json
{
  "intent": "REJECT",
  "entities": {
    "metric": null,
    "time": null,
    "batch_id": null
  },
  "match": {
    "found": false,
    "table": null,
    "field": null
  },
  "route": "USER",
  "reason": "Query not related to manufacturing operations"
}
```

---

## 7. Performance Specifications

| Metric | Target | Description |
|:-------|:-------|:------------|
| Routing Latency | < 500ms | Time from query receipt to routing decision |
| Accuracy | > 95% | Correct routing classification |
| Token Usage | ~600 tokens | Static prompt size (excluding KPI JSON) |
| KPI Catalogue Size | ~2KB | Injected JSON schema |

---

## 8. Integration Points

### 8.1 Upstream Integration
- **Input**: User natural language query + session context
- **Source**: Chat interface / API gateway

### 8.2 Downstream Integration

| Agent | Purpose | Data Source |
|:------|:--------|:------------|
| KPI Agent | Simple metric lookups | KPI_STORE_MONTHLY, KPI_STORE_WEEKLY |
| Analyst Agent | Complex analysis | Transactional tables (MES, LIMS, SAP) |

### 8.3 Data Catalogue Sync
- KPI schema refreshed weekly from Collibra
- Field aliases maintained in configuration

---

## 9. Appendix

### A. Supported KPI Metrics

| Metric | Description | Target | Unit |
|:-------|:------------|:-------|:-----|
| Batch Yield | Average batch yield percentage | 98% | % |
| RFT | Right First Time rate | 92% | % |
| OEE Packaging | Overall Equipment Effectiveness | 80% | % |
| Cycle Time | Average batch processing time | - | hours |
| Deviations | Quality deviation rate | <5 | per 100 batches |
| Alarms | Equipment alarm frequency | - | per 1000 hours |
| Lab TAT | Laboratory turnaround time | - | days |
| Supplier OTIF | Supplier delivery performance | 95% | % |
| Stockouts | Material stockout events | 0 | count |
| Schedule Adherence | On-time batch completion | 95% | % |

### B. Glossary

| Term | Definition |
|:-----|:-----------|
| KPI | Key Performance Indicator |
| RFT | Right First Time - batches released without rework |
| OEE | Overall Equipment Effectiveness |
| OTIF | On-Time In-Full delivery |
| RAG | Red/Amber/Green status indicator |
| TAT | Turnaround Time |
| MES | Manufacturing Execution System |
| LIMS | Laboratory Information Management System |

---

**Document Control**

| Version | Date | Author | Changes |
|:--------|:-----|:-------|:--------|
| 1.0 | Feb 2026 | MIA Team | Initial release |

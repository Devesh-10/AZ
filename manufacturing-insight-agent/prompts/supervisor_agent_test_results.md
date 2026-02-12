# Supervisor Agent - Test Results

## KPI Catalogue Used

**KPI_STORE_MONTHLY fields:**
`MONTH`, `SITE_ID`, `PRODUCTION_VOLUME`, `BATCH_COUNT`, `BATCH_YIELD_AVG_PCT`, `RFT_PCT`, `SCHEDULE_ADHERENCE_PCT`, `AVG_CYCLE_TIME_HR`, `DEVIATIONS_PER_100_BATCHES`, `ALARMS_PER_1000_HOURS`, `LAB_TURNAROUND_MEDIAN_DAYS`, `SUPPLIER_OTIF_PCT`, `OEE_PACKAGING_PCT`, `TARGET_OTIF_PCT`, `TARGET_RFT_PCT`, `TARGET_OEE_PACKAGING_PCT`, `OTIF_RAG`, `RFT_RAG`, `OEE_RAG`

**KPI_STORE_WEEKLY fields:**
`ISO_WEEK`, `SITE_ID`, `PRODUCTION_VOLUME`, `BATCH_COUNT`, `BATCH_YIELD_AVG_PCT`, `RFT_PCT`, `SCHEDULE_ADHERENCE_PCT`, `AVG_CYCLE_TIME_HR`, `DEVIATIONS_PER_100_BATCHES`, `ALARMS_PER_1000_HOURS`, `STOCKOUTS_COUNT`, `OEE_PACKAGING_PCT`, `MONTH`

---

## Test Cases

### TEST 1: Simple KPI Lookup (Monthly)
**Question:** "What is the batch yield for last 3 months?"

**Processing:**
- Extracted metric: "batch yield" → `BATCH_YIELD_AVG_PCT`
- Time range: 3 months → granularity: monthly
- Match check: `BATCH_YIELD_AVG_PCT` ∈ KPI_STORE_MONTHLY.fields? ✅ YES
- Query type: "What is" = simple lookup

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
  "reason": "BATCH_YIELD_AVG_PCT exists in KPI_STORE_MONTHLY. Direct lookup."
}
```

---

### TEST 2: Simple KPI Lookup (Weekly)
**Question:** "Show me stockouts for the past 4 weeks"

**Processing:**
- Extracted metric: "stockouts" → `STOCKOUTS_COUNT`
- Time range: 4 weeks → granularity: weekly
- Match check: `STOCKOUTS_COUNT` ∈ KPI_STORE_WEEKLY.fields? ✅ YES
- Match check: `STOCKOUTS_COUNT` ∈ KPI_STORE_MONTHLY.fields? ❌ NO (weekly only)
- Query type: "Show me" = simple lookup

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
  "reason": "STOCKOUTS_COUNT exists in KPI_STORE_WEEKLY only. Direct lookup."
}
```

---

### TEST 3: KPI with Analysis Required
**Question:** "Why is our RFT below target?"

**Processing:**
- Extracted metric: "RFT" → `RFT_PCT`
- Comparison: "target" → `TARGET_RFT_PCT`
- Match check: `RFT_PCT` ∈ KPI_STORE_MONTHLY.fields? ✅ YES
- Query type: "Why" = root cause analysis

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
  "reason": "RFT_PCT exists but 'why' requires root cause analysis from transactional data."
}
```

---

### TEST 4: KPI Improvement Query
**Question:** "How can we improve OEE packaging?"

**Processing:**
- Extracted metric: "OEE packaging" → `OEE_PACKAGING_PCT`
- Match check: `OEE_PACKAGING_PCT` ∈ KPI_STORE_MONTHLY.fields? ✅ YES
- Query type: "How can we improve" = analysis/recommendations

**Output:**
```json
{
  "intent": "KPI_COMPLEX",
  "entities": {
    "metric": "OEE_PACKAGING_PCT",
    "time": null,
    "batch_id": null
  },
  "match": {
    "found": true,
    "table": "KPI_STORE_MONTHLY",
    "field": "OEE_PACKAGING_PCT"
  },
  "route": "ANALYST_AGENT",
  "reason": "OEE_PACKAGING_PCT exists but improvement recommendations require deeper analysis."
}
```

---

### TEST 5: Batch-Level Query (No KPI Match)
**Question:** "What is the waiting time between formulation and packaging for batch B2025-00007?"

**Processing:**
- Extracted metric: "waiting time" → No alias match
- Extracted batch_id: `B2025-00007`
- Match check: "waiting_time" ∈ KPI tables? ❌ NO
- Batch-level query requires transactional data (MES_PASX_BATCH_STEPS)

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
  "reason": "Waiting time not in KPI catalogue. Batch-level step data required."
}
```

---

### TEST 6: Equipment-Specific Query (No KPI Match)
**Question:** "What is the performance of equipment VIAL-1?"

**Processing:**
- Extracted metric: "performance" → ambiguous, no direct match
- Extracted equipment_id: `VIAL-1`
- Match check: equipment-specific data ∈ KPI tables? ❌ NO (KPIs are site-level aggregates)

**Output:**
```json
{
  "intent": "COMPLEX",
  "entities": {
    "metric": null,
    "time": null,
    "batch_id": null,
    "equipment_id": "VIAL-1"
  },
  "match": {
    "found": false,
    "table": null,
    "field": null
  },
  "route": "ANALYST_AGENT",
  "reason": "Equipment-level performance not in KPI tables. Requires batch/equipment transactional data."
}
```

---

### TEST 7: Lab Turnaround (Monthly Only)
**Question:** "What is the lab turnaround time?"

**Processing:**
- Extracted metric: "lab turnaround" → `LAB_TURNAROUND_MEDIAN_DAYS`
- Match check: `LAB_TURNAROUND_MEDIAN_DAYS` ∈ KPI_STORE_MONTHLY.fields? ✅ YES
- Match check: `LAB_TURNAROUND_MEDIAN_DAYS` ∈ KPI_STORE_WEEKLY.fields? ❌ NO (monthly only)
- Query type: "What is" = simple lookup

**Output:**
```json
{
  "intent": "KPI_SIMPLE",
  "entities": {
    "metric": "LAB_TURNAROUND_MEDIAN_DAYS",
    "time": null,
    "batch_id": null
  },
  "match": {
    "found": true,
    "table": "KPI_STORE_MONTHLY",
    "field": "LAB_TURNAROUND_MEDIAN_DAYS"
  },
  "route": "KPI_AGENT",
  "reason": "LAB_TURNAROUND_MEDIAN_DAYS exists in KPI_STORE_MONTHLY only. Direct lookup."
}
```

---

### TEST 8: RAG Status Query
**Question:** "What is the RFT status this month?"

**Processing:**
- Extracted metric: "RFT status" → `RFT_RAG`
- Time range: "this month" → current month
- Match check: `RFT_RAG` ∈ KPI_STORE_MONTHLY.fields? ✅ YES
- Query type: "What is" = simple lookup

**Output:**
```json
{
  "intent": "KPI_SIMPLE",
  "entities": {
    "metric": "RFT_RAG",
    "time": {"n": 1, "unit": "month"},
    "batch_id": null
  },
  "match": {
    "found": true,
    "table": "KPI_STORE_MONTHLY",
    "field": "RFT_RAG"
  },
  "route": "KPI_AGENT",
  "reason": "RFT_RAG exists in KPI_STORE_MONTHLY. Direct lookup."
}
```

---

### TEST 9: Multiple KPIs Query
**Question:** "Show me yield and OEE for last month"

**Processing:**
- Extracted metrics: "yield" → `BATCH_YIELD_AVG_PCT`, "OEE" → `OEE_PACKAGING_PCT`
- Time range: 1 month → granularity: monthly
- Match check: Both fields ∈ KPI_STORE_MONTHLY.fields? ✅ YES
- Query type: "Show me" = simple lookup

**Output:**
```json
{
  "intent": "KPI_SIMPLE",
  "entities": {
    "metric": ["BATCH_YIELD_AVG_PCT", "OEE_PACKAGING_PCT"],
    "time": {"n": 1, "unit": "month"},
    "batch_id": null
  },
  "match": {
    "found": true,
    "table": "KPI_STORE_MONTHLY",
    "field": ["BATCH_YIELD_AVG_PCT", "OEE_PACKAGING_PCT"]
  },
  "route": "KPI_AGENT",
  "reason": "Both metrics exist in KPI_STORE_MONTHLY. Direct lookup."
}
```

---

### TEST 10: Out of Scope Query
**Question:** "What is the weather forecast for tomorrow?"

**Processing:**
- Extracted metric: None (no manufacturing terms)
- Match check: N/A
- Query type: Not manufacturing related

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
  "reason": "Query not related to manufacturing. Out of scope."
}
```

---

### TEST 11: Deviation Root Cause
**Question:** "What are the root causes of deviations last month?"

**Processing:**
- Extracted metric: "deviations" → `DEVIATIONS_PER_100_BATCHES`
- Time range: 1 month
- Match check: `DEVIATIONS_PER_100_BATCHES` ∈ KPI_STORE_MONTHLY.fields? ✅ YES
- Query type: "root causes" = analysis required

**Output:**
```json
{
  "intent": "KPI_COMPLEX",
  "entities": {
    "metric": "DEVIATIONS_PER_100_BATCHES",
    "time": {"n": 1, "unit": "month"},
    "batch_id": null
  },
  "match": {
    "found": true,
    "table": "KPI_STORE_MONTHLY",
    "field": "DEVIATIONS_PER_100_BATCHES"
  },
  "route": "ANALYST_AGENT",
  "reason": "Deviation count exists but root cause analysis requires transactional deviation records."
}
```

---

### TEST 12: Supplier Performance
**Question:** "How is supplier OTIF trending?"

**Processing:**
- Extracted metric: "supplier OTIF" → `SUPPLIER_OTIF_PCT`
- Match check: `SUPPLIER_OTIF_PCT` ∈ KPI_STORE_MONTHLY.fields? ✅ YES
- Query type: "trending" = trend analysis (simple)

**Output:**
```json
{
  "intent": "KPI_SIMPLE",
  "entities": {
    "metric": "SUPPLIER_OTIF_PCT",
    "time": null,
    "batch_id": null
  },
  "match": {
    "found": true,
    "table": "KPI_STORE_MONTHLY",
    "field": "SUPPLIER_OTIF_PCT"
  },
  "route": "KPI_AGENT",
  "reason": "SUPPLIER_OTIF_PCT exists. Trend can be derived from monthly data."
}
```

---

### TEST 13: Specific Batch Status (No KPI Match)
**Question:** "What is the status of batch B2025-00123?"

**Processing:**
- Extracted metric: "status" → No direct KPI match (batch-level)
- Extracted batch_id: `B2025-00123`
- Match check: Batch status ∈ KPI tables? ❌ NO (requires MES_PASX_BATCHES)

**Output:**
```json
{
  "intent": "COMPLEX",
  "entities": {
    "metric": null,
    "time": null,
    "batch_id": "B2025-00123"
  },
  "match": {
    "found": false,
    "table": null,
    "field": null
  },
  "route": "ANALYST_AGENT",
  "reason": "Batch-level status not in KPI tables. Requires transactional batch data."
}
```

---

### TEST 14: Alarm Analysis
**Question:** "Show alarms per 1000 hours for last 6 months"

**Processing:**
- Extracted metric: "alarms per 1000 hours" → `ALARMS_PER_1000_HOURS`
- Time range: 6 months → granularity: monthly
- Match check: `ALARMS_PER_1000_HOURS` ∈ KPI_STORE_MONTHLY.fields? ✅ YES
- Query type: "Show" = simple lookup

**Output:**
```json
{
  "intent": "KPI_SIMPLE",
  "entities": {
    "metric": "ALARMS_PER_1000_HOURS",
    "time": {"n": 6, "unit": "month"},
    "batch_id": null
  },
  "match": {
    "found": true,
    "table": "KPI_STORE_MONTHLY",
    "field": "ALARMS_PER_1000_HOURS"
  },
  "route": "KPI_AGENT",
  "reason": "ALARMS_PER_1000_HOURS exists in KPI_STORE_MONTHLY. Direct lookup."
}
```

---

### TEST 15: Compare vs Target
**Question:** "Is OEE meeting target?"

**Processing:**
- Extracted metrics: "OEE" → `OEE_PACKAGING_PCT`, "target" → `TARGET_OEE_PACKAGING_PCT`
- Match check: Both fields ∈ KPI_STORE_MONTHLY.fields? ✅ YES
- Query type: Comparison = simple lookup (both values available)

**Output:**
```json
{
  "intent": "KPI_SIMPLE",
  "entities": {
    "metric": ["OEE_PACKAGING_PCT", "TARGET_OEE_PACKAGING_PCT"],
    "time": null,
    "batch_id": null
  },
  "match": {
    "found": true,
    "table": "KPI_STORE_MONTHLY",
    "field": ["OEE_PACKAGING_PCT", "TARGET_OEE_PACKAGING_PCT"]
  },
  "route": "KPI_AGENT",
  "reason": "Both OEE actual and target exist in KPI_STORE_MONTHLY. Direct comparison."
}
```

---

## Summary

| Test | Question Type | KPI Match | Route | Reason |
|------|--------------|-----------|-------|--------|
| 1 | Simple lookup (monthly) | ✅ BATCH_YIELD_AVG_PCT | KPI_AGENT | Direct lookup |
| 2 | Simple lookup (weekly) | ✅ STOCKOUTS_COUNT | KPI_AGENT | Weekly-only field |
| 3 | Root cause analysis | ✅ RFT_PCT | ANALYST_AGENT | "Why" needs transactional |
| 4 | Improvement query | ✅ OEE_PACKAGING_PCT | ANALYST_AGENT | Recommendations needed |
| 5 | Batch-level query | ❌ | ANALYST_AGENT | Not in KPI tables |
| 6 | Equipment-specific | ❌ | ANALYST_AGENT | Not in KPI tables |
| 7 | Monthly-only field | ✅ LAB_TURNAROUND_MEDIAN_DAYS | KPI_AGENT | Direct lookup |
| 8 | RAG status | ✅ RFT_RAG | KPI_AGENT | Direct lookup |
| 9 | Multiple KPIs | ✅ Multiple | KPI_AGENT | Direct lookup |
| 10 | Out of scope | ❌ | REJECT | Not manufacturing |
| 11 | Deviation root cause | ✅ DEVIATIONS_PER_100_BATCHES | ANALYST_AGENT | Root cause needed |
| 12 | Trend query | ✅ SUPPLIER_OTIF_PCT | KPI_AGENT | Direct lookup |
| 13 | Batch status | ❌ | ANALYST_AGENT | Not in KPI tables |
| 14 | Simple lookup | ✅ ALARMS_PER_1000_HOURS | KPI_AGENT | Direct lookup |
| 15 | Target comparison | ✅ Multiple | KPI_AGENT | Both values available |

**Routing Distribution:**
- KPI_AGENT: 9 queries (60%)
- ANALYST_AGENT: 5 queries (33%)
- REJECT: 1 query (7%)

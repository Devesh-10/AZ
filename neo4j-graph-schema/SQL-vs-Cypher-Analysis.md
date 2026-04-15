# MIA Ground Truth Questions — SQL vs Cypher Analysis

## Executive Summary

Of the **19 ground truth questions**, only **3–4 genuinely benefit from a graph database**. The remaining **15–16 are flat filter-aggregate queries** that are simpler, faster, and more maintainable in SQL on Snowflake.

| Category | Count | Recommendation |
|----------|-------|----------------|
| SQL is clearly better | 12 | Keep in Snowflake |
| Either works equally | 3 | SQL preferred (simpler tooling) |
| Graph adds genuine value | 4 | Use Neo4j/Cypher |

---

## Question-by-Question Analysis

### Q2: How many batches are in packing today?

| Aspect | Detail |
|--------|--------|
| **SQL Pattern** | Filter ORDER_STATUS + JOIN BATCH_STATUS on process order, filter supervisors, status, date → `COUNT` |
| **Tables** | ORDER_STATUS, BATCH_STATUS (1 JOIN) |
| **Graph hops** | 1 hop: `(po)-[:EXECUTED_AT]->(plant)` + `(b)-[:PRODUCED_BY]->(po)` |
| **Cypher pain points** | Requires `replace(coalesce(...))` string gymnastics identical to SQL — no simplification |
| **Verdict** | **SQL** |
| **Why** | Single-table filter + count. The JOIN to BATCH_STATUS is a 1:1 lookup, not a traversal. Zero graph benefit. |

---

### Q3: How many batches in quality control?

| Aspect | Detail |
|--------|--------|
| **SQL Pattern** | Filter BATCH_STATUS on plant, exclusion, LIMS dates, usage decision → `COUNT` |
| **Tables** | BATCH_STATUS only (0 JOINs) |
| **Graph hops** | 1 hop: `(b)-[:MANUFACTURED_AT]->(plant)` + `(b)-[:HAS_LIMS_LOT]->(ll)` |
| **Cypher pain points** | LIMS fields split across Batch and LIMSLot nodes — requires extra MATCH that SQL doesn't need |
| **Verdict** | **SQL** |
| **Why** | Single-table query in SQL. The graph actually makes this harder by splitting LIMS data onto a separate node. |

---

### Q4: How many orders of CP (China Packing) scheduled this week?

| Aspect | Detail |
|--------|--------|
| **SQL Pattern** | Filter ORDER_STATUS on week, supervisor, cancelled, plant → `COUNT DISTINCT` |
| **Tables** | ORDER_STATUS only (0 JOINs) |
| **Graph hops** | 1 hop: `(po)-[:EXECUTED_AT]->(plant)` |
| **Cypher pain points** | None significant, but no benefit either |
| **Verdict** | **SQL** |
| **Why** | Pure single-table filter + count. Textbook SQL. |

---

### Q6: How many orders scheduled & finished this week? (Total, Packing, Formulation)

| Aspect | Detail |
|--------|--------|
| **SQL Pattern** | Filter ORDER_STATUS, categorise by supervisor → group by category, count scheduled vs confirmed |
| **Tables** | ORDER_STATUS only (0 JOINs) |
| **Graph hops** | 1 hop: `(po)-[:EXECUTED_AT]->(plant)` |
| **Cypher pain points** | No native `UNION` — need `UNWIND` + `collect` workaround for Total/Packing/Formulation rows |
| **Verdict** | **SQL** |
| **Why** | Single-table GROUP BY with CASE WHEN. Cypher's lack of UNION makes the "Total" row awkward. |

---

### Q7: How many orders missed scheduled finish date for Packing (week of Feb 4, 2026)?

| Aspect | Detail |
|--------|--------|
| **SQL Pattern** | Filter ORDER_STATUS on date range, supervisor, cancelled, compare scheduled vs actual finish → `COUNT` |
| **Tables** | ORDER_STATUS only (0 JOINs) |
| **Graph hops** | 1 hop: `(po)-[:EXECUTED_AT]->(plant)` |
| **Cypher pain points** | Date arithmetic (week start/end calculation) is verbose in Cypher |
| **Verdict** | **SQL** |
| **Why** | Single-table filter + count with date comparison. No relationships involved. |

---

### Q9: Formulation orders missing scheduled finish date last week?

| Aspect | Detail |
|--------|--------|
| **SQL Pattern** | Filter ORDER_STATUS on relative week, formulation supervisors, system status, compare finish dates → `COUNT` |
| **Tables** | ORDER_STATUS only (0 JOINs) |
| **Graph hops** | 1 hop: `(po)-[:EXECUTED_AT]->(plant)` |
| **Cypher pain points** | None, but identical logic to SQL |
| **Verdict** | **SQL** |
| **Why** | Single-table filter. Identical complexity in both languages. |

---

### Q10: Orders exceeding MLT target last week?

| Aspect | Detail |
|--------|--------|
| **SQL Pattern** | Holiday table + ORDER_STATUS + ORDER_BATCH_RELATIONSHIP + formulation order lookup, working-day calculation, compare vs MLT targets |
| **Tables** | ORDER_STATUS, ORDER_BATCH_RELATIONSHIP (12 JOINs), holiday VALUES table |
| **Graph hops** | 2–3 hops: `(po)←[:CONSUMED_BY]-(b)-[:PRODUCED_BY]->(formOrd)` |
| **Cypher pain points** | No business-day functions, no holiday support — must approximate weekends only |
| **Graph advantage** | The formulation→packing traversal via consumed batches is a natural graph pattern |
| **Verdict** | **Graph (partial)** |
| **Why** | The multi-hop batch genealogy (packing order → consumed batch → formulation order) is genuinely easier to express as a graph traversal. However, the working-day calculation with holidays is significantly worse in Cypher. **Hybrid ideal**: graph for the traversal, SQL for the date math. |

---

### Q11: List all batches of raw material expiring within 6 months

| Aspect | Detail |
|--------|--------|
| **SQL Pattern** | Filter BATCH_STATUS on best_before_date range, stock > 0, location types → list |
| **Tables** | BATCH_STATUS only (0 JOINs) |
| **Graph hops** | 1 hop: `(b)-[:MANUFACTURED_AT]->(plant)` |
| **Cypher pain points** | None, but no benefit |
| **Verdict** | **SQL** |
| **Why** | Pure single-table filter with date range. Zero relationship traversal. |

---

### Q12: List all finish packs waiting for QA release

| Aspect | Detail |
|--------|--------|
| **SQL Pattern** | JOIN ORDER_STATUS + BATCH_STATUS, filter packing supervisors, confirmed, has goods receipt, no usage decision |
| **Tables** | ORDER_STATUS, BATCH_STATUS (1 JOIN) |
| **Graph hops** | 1 hop: `(b)-[:PRODUCED_BY]->(po)` or join via batchCode |
| **Cypher pain points** | Must join Batch by batchCode since LPB is on Batch node |
| **Verdict** | **SQL** |
| **Why** | Simple 2-table JOIN + filter. The graph adds no structural insight. |

---

### Q14: Seloken inventory days on hand (finish pack, bulk, API)

| Aspect | Detail |
|--------|--------|
| **SQL Pattern** | BATCH_STATUS + ORDER_STATUS + ORDER_BATCH_RELATIONSHIP for consumption over 6 months, stock / avg daily consumption |
| **Tables** | BATCH_STATUS, ORDER_STATUS, ORDER_BATCH_RELATIONSHIP (7 JOINs) |
| **Graph hops** | 2+ hops: `(b)-[:CONSUMED_BY]->(po)` for consumption history |
| **Cypher pain points** | Aggregating 6-month consumption windows |
| **Graph advantage** | Consumption relationships (`CONSUMED_BY`) naturally model material flow — "which orders consumed this material?" is a direct graph query |
| **Verdict** | **Graph** |
| **Why** | Inventory DOH requires tracing material consumption chains. The `CONSUMED_BY` relationship directly models this. In SQL it requires joining ORDER_BATCH_RELATIONSHIP + ORDER_STATUS + BATCH_STATUS with date windows. The graph makes the consumption traversal cleaner. |

---

### Q18: Average quality release lead time this week

| Aspect | Detail |
|--------|--------|
| **SQL Pattern** | JOIN ORDER_STATUS + BATCH_STATUS, compute (usage_decision - LPB) in working hours, subtract weekends |
| **Tables** | ORDER_STATUS, BATCH_STATUS (1 JOIN) |
| **Graph hops** | 1 hop: join Batch by batchCode |
| **Cypher pain points** | Working-day calculation is verbose and approximate (no holidays) |
| **Verdict** | **SQL** |
| **Why** | 2-table JOIN + date math. Snowflake's `DATEDIFF`, `DAYOFWEEKISO`, and holiday VALUES tables handle this natively. Cypher has no equivalent. |

---

### Q19: Average formulation lead time by brand for China market last week

| Aspect | Detail |
|--------|--------|
| **SQL Pattern** | Material-to-brand mapping + ORDER_STATUS + BATCH_STATUS + holiday/working-day calculation |
| **Tables** | ORDER_STATUS, BATCH_STATUS (2 JOINs), holidays |
| **Graph hops** | 1 hop: join Batch by batchCode |
| **Cypher pain points** | Holiday-aware working-day math not possible; material code matching (leading zeros) awkward |
| **Verdict** | **SQL** |
| **Why** | The core logic is date arithmetic with holidays — Snowflake excels at this. The material-to-brand mapping is a simple lookup, not a graph traversal. |

---

### Q20: Batch MLT of last week by order

| Aspect | Detail |
|--------|--------|
| **SQL Pattern** | ORDER_STATUS + ORDER_BATCH_RELATIONSHIP + formulation order lookup, 4 time segments (formulation, warehouse, packing, QA), holiday-aware working days, ROW_NUMBER dedup |
| **Tables** | ORDER_STATUS, ORDER_BATCH_RELATIONSHIP (15 JOINs), holidays |
| **Graph hops** | 3 hops: `(po)←[:CONSUMED_BY]-(consumedBatch)-[:PRODUCED_BY]->(formOrd)` + ADJUSTS path |
| **Cypher pain points** | No ROW_NUMBER(), no holidays, approximate weekend calc, complex dedup via collect()[0] |
| **Graph advantage** | The batch genealogy traversal (packing → consumed batch → formulation) is a natural graph pattern |
| **Verdict** | **Graph (partial)** |
| **Why** | Same as Q10 — the multi-hop genealogy is graph-native, but the working-day calculation with holidays and the ROW_NUMBER deduplication are painful in Cypher. **Most complex query in the set.** Hybrid approach ideal. |

---

### Q21: Average formulation yield for Brilinta in 2026

| Aspect | Detail |
|--------|--------|
| **SQL Pattern** | Material-to-target mapping + filter ORDER_STATUS on material, year, supervisor, confirmed → avg(yield) |
| **Tables** | ORDER_STATUS only (1 self-join on yield targets) |
| **Graph hops** | 1 hop: `(po)-[:EXECUTED_AT]->(plant)` |
| **Cypher pain points** | None significant |
| **Verdict** | **SQL** |
| **Why** | Single-table filter + AVG with a static lookup table. No relationships involved. |

---

### Q22: Average lead time for Formulation Seroquel IR last month

| Aspect | Detail |
|--------|--------|
| **SQL Pattern** | ORDER_STATUS + BATCH_STATUS + holiday/working-day calculation, filter by product family and date range |
| **Tables** | ORDER_STATUS, BATCH_STATUS (2 JOINs), holidays |
| **Graph hops** | 1 hop: join Batch by batchCode |
| **Cypher pain points** | Holiday-aware working-day math |
| **Verdict** | **SQL** |
| **Why** | 2-table JOIN + date arithmetic with holidays. Same pattern as Q18/Q19. |

---

### Q23: Yield adherence of Formulation Brilinta (Feb 2026)

| Aspect | Detail |
|--------|--------|
| **SQL Pattern** | Yield target mapping + ORDER_STATUS + BATCH_STATUS, compare actual yield vs target → pass rate % |
| **Tables** | ORDER_STATUS, BATCH_STATUS (2 JOINs) |
| **Graph hops** | 1 hop: join Batch by batchCode |
| **Cypher pain points** | None significant |
| **Verdict** | **SQL** |
| **Why** | Filter + ratio calculation. No relationships or traversals. |

---

### Q25: Formulation process lead time for CNC9-280 in February

| Aspect | Detail |
|--------|--------|
| **SQL Pattern** | ORDER_STATUS + BATCH_STATUS + holiday/working-day calculation for specific material |
| **Tables** | ORDER_STATUS, BATCH_STATUS (2 JOINs), holidays |
| **Graph hops** | 1 hop: join Batch by batchCode |
| **Cypher pain points** | Holiday-aware working-day math |
| **Verdict** | **SQL** |
| **Why** | Same pattern as Q19/Q22. Date math with holidays. |

---

### Q27: How many hours did the last order delay in L13?

| Aspect | Detail |
|--------|--------|
| **SQL Pattern** | ORDER_STATUS + BATCH_STATUS, filter by work centre, confirmed, packing supervisors, ORDER BY LPB DESC LIMIT 1 |
| **Tables** | ORDER_STATUS, BATCH_STATUS (1 JOIN) |
| **Graph hops** | 2 hops: `(po)-[:HAS_OPERATION]->(op)-[:USES_WORK_CENTRE]->(wc)` + Batch join |
| **Cypher pain points** | Work centre is a separate node requiring 2-hop traversal; alternatively use `workCentreCodesText` |
| **Graph advantage** | The operation → work centre model is a natural graph structure |
| **Verdict** | **Either** |
| **Why** | The work centre traversal is slightly more natural in graph form, but the SQL version just uses a text field (`WORK_CENTRE_CODE`). Marginal graph advantage. |

---

### Q29: Overall lead time adherence of different brands last week

| Aspect | Detail |
|--------|--------|
| **SQL Pattern** | MLT target table + ORDER_STATUS + BATCH_STATUS + holiday/working-day calculation, group by brand → adherence % |
| **Tables** | ORDER_STATUS, BATCH_STATUS (6 JOINs), holidays |
| **Graph hops** | 1 hop: join Batch by batchCode |
| **Cypher pain points** | Holiday-aware working-day math, no native window functions for the adherence calc |
| **Verdict** | **SQL** |
| **Why** | Multi-brand aggregation with holiday-aware date math. Snowflake handles this natively. |

---

## Summary Matrix

| Q# | Question | Tables | SQL JOINs | Graph Hops | Holiday Math | Window Fn | **Verdict** |
|----|----------|--------|-----------|------------|-------------|-----------|-------------|
| Q2 | Batches in packing today | 2 | 1 | 1–2 | No | No | **SQL** |
| Q3 | Batches in QC | 1 | 0 | 1–2 | No | No | **SQL** |
| Q4 | CP orders this week | 1 | 0 | 1 | No | No | **SQL** |
| Q6 | Scheduled & finished orders | 1 | 0 | 1 | No | No | **SQL** |
| Q7 | Missed finish date (Packing) | 1 | 0 | 1 | No | No | **SQL** |
| Q9 | Missing finish date (Formulation) | 1 | 0 | 1 | No | No | **SQL** |
| Q10 | Orders exceeding MLT | 3 | 12 | 2–3 | Yes | Yes | **Graph** (partial) |
| Q11 | Raw material expiry | 1 | 0 | 1 | No | No | **SQL** |
| Q12 | Finish packs waiting QA | 2 | 1 | 1 | No | No | **SQL** |
| Q14 | Seloken inventory DOH | 3 | 7 | 2+ | No | No | **Graph** |
| Q18 | Avg QA release lead time | 2 | 1 | 1 | Yes | No | **SQL** |
| Q19 | Avg formulation lead time by brand | 2 | 2 | 1 | Yes | No | **SQL** |
| Q20 | Batch MLT by order | 3 | 15 | 3 | Yes | Yes | **Graph** (partial) |
| Q21 | Avg formulation yield (Brilinta) | 1 | 0 | 1 | No | No | **SQL** |
| Q22 | Avg lead time (Seroquel IR) | 2 | 2 | 1 | Yes | No | **SQL** |
| Q23 | Yield adherence (Brilinta) | 2 | 2 | 1 | No | No | **SQL** |
| Q25 | Lead time CNC9-280 | 2 | 2 | 1 | Yes | No | **SQL** |
| Q27 | Last order delay in L13 | 2 | 1 | 2 | No | No | **Either** |
| Q29 | Lead time adherence by brand | 2 | 6 | 1 | Yes | No | **SQL** |

---

## Recommendation

### Keep in SQL (Snowflake) — 12 questions
Q2, Q3, Q4, Q6, Q7, Q9, Q11, Q12, Q18, Q21, Q22, Q23

These are **flat filter-aggregate queries** on 1–2 tables. The graph adds zero value and introduces mapping complexity.

### Either works — 3 questions
Q19, Q25, Q27, Q29

These could work in either, but SQL is preferred because of holiday-aware date math (Q19, Q25, Q29) or marginal graph benefit (Q27).

### Graph adds genuine value — 4 questions
Q10, Q14, Q20 (+ future genealogy/traceability queries)

These involve **multi-hop batch genealogy** (packing → consumed batch → formulation order) which is a natural graph traversal pattern. However, even these benefit from a **hybrid approach**:

- **Use Neo4j** for: traversing batch relationships, material genealogy, consumption chains
- **Use Snowflake** for: working-day calculations with holidays, window functions, aggregations

### Where Neo4j really shines (not in current questions)

The current 19 questions don't include the queries where graph databases provide 10x+ value:

1. **Full batch traceability** — "Trace batch X from raw material through all intermediate steps to finished product" (variable-depth traversal)
2. **Recall impact analysis** — "If raw material batch Y is recalled, which finished packs are affected?" (reverse traversal)
3. **Common failure patterns** — "Find all orders that share raw materials with orders that failed QC" (pattern matching)
4. **Supply chain dependency** — "Which products are at risk if supplier Z has a disruption?" (multi-hop impact)
5. **Process deviation correlation** — "Do batches that went through work centre X after work centre Y have higher failure rates?" (path pattern analysis)

**These are the questions you should be building toward** — they justify the graph investment.

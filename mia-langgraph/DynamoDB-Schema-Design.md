# MIA DynamoDB Schema Design Document

**Project:** Manufacturing Insight Agent (MIA)
**Version:** 2.0
**Date:** March 2026
**Author:** AI Architecture Team

---

## 1. Why Do We Need DynamoDB?

MIA runs on **AWS Lambda** — a serverless function that spins up, processes a request, and shuts down. Lambda has **no memory between requests**. This means:

- If User A asks "What is the batch yield?" and then asks "Can you break that down by site?" — Lambda has **no idea** what "that" refers to, because the first request is already gone.
- If 10 users ask the exact same question — Lambda runs the full AI pipeline 10 times, calling Claude, generating SQL, and querying data each time. That's **10x the cost and latency** for the same answer.

**DynamoDB solves both problems:**

| Problem | Solution | DynamoDB Table |
|---------|----------|----------------|
| Lambda forgets conversations | Store chat history persistently | `mia_chat_sessions` |
| Same questions re-processed | Cache results for repeated queries | `mia_session_turns` |

---

## 2. How MIA Works (Simplified)

```
User asks a question
        │
        ▼
┌─────────────────┐
│   Supervisor     │ ── Decides: Is this a simple KPI lookup or complex analysis?
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌──────────┐
│KPI Agent│ │Analyst   │ ── Generates SQL, queries data, builds answer
└───┬────┘ └────┬─────┘
    └─────┬─────┘
          ▼
   ┌────────────┐
   │ Validator   │ ── Checks if the answer makes sense
   └──────┬─────┘
          ▼
   ┌────────────┐
   │Visualization│ ── Creates chart configuration
   └──────┬─────┘
          ▼
    Answer returned to user
```

Each step above is an **agent**. Each agent calls Claude (AI model) on AWS Bedrock. Each call **costs money** and **takes time** (1-3 seconds per agent). A full pipeline run takes 5-15 seconds and costs ~$0.01-0.05.

**This is why caching matters.** If someone already asked "What is the batch yield?" today, we can return the cached answer in **<100ms** for **$0.00**.

---

## 3. Table 1: `mia_session_turns` — The Audit Trail & Cache

### What It Stores

Every time a user asks a question, we record **one row** with:
- What they asked
- Which path the AI took (fast KPI lookup vs complex analysis vs cache hit)
- A summary of the answer
- Enough metadata to replay or audit the interaction

Think of it like a **flight recorder** for every AI interaction.

### Why This Table Exists

1. **Query Caching** — Before running the full AI pipeline, we check: "Has this exact question been asked before?" If yes, return the cached answer instantly.
2. **Audit Trail** — For compliance and debugging: "What did the AI tell User X at 3pm yesterday?"
3. **Analytics** — "Which KPIs are most frequently asked about?" "How often does the AI take the slow path?"

### Schema

```
Table Name: mia_session_turns

┌─────────────────────────────────────────────────────────────────┐
│ KEY DESIGN                                                       │
│                                                                  │
│ Partition Key (pk):  {tenant_id}#{session_id}                    │
│                      Example: "default#sess-abc123"              │
│                                                                  │
│ Sort Key (sk):       {timestamp_iso}#{request_id}                │
│                      Example: "2026-03-09T10:30:15Z#req-xyz789"  │
└─────────────────────────────────────────────────────────────────┘
```

**Why this key design?**

- **Partition Key** combines `tenant_id` (for multi-tenancy — different teams or orgs) with `session_id` (groups all turns in one conversation). This means: *"Give me everything that happened in this session"* is a single, fast DynamoDB Query.
- **Sort Key** uses timestamp + request_id. The timestamp ensures turns come back in chronological order. The request_id prevents collisions if two requests happen at the exact same millisecond.

### All Attributes Explained

| Attribute | Type | Example | Why It Exists |
|-----------|------|---------|---------------|
| `pk` | String | `"default#sess-abc123"` | **Partition Key.** Groups all turns in a session. `tenant_id` enables multi-org support. |
| `sk` | String | `"2026-03-09T10:30:15Z#req-xyz789"` | **Sort Key.** Orders turns chronologically. Request ID prevents duplicates. |
| `tenant_id` | String | `"default"` | Which organization/team. Stored separately for filtering and future GSIs. |
| `session_id` | String | `"sess-abc123"` | Which conversation this turn belongs to. |
| `request_id` | String | `"req-xyz789"` | Unique ID for this specific request. Used for tracing and deduplication. |
| `query_hash` | String | `"a1b2c3d4e5f6g7h8"` | SHA-256 hash of the normalized question. Used for **cache lookups** — "has this exact question been asked before?" |
| `user_id` | String | `"harish"` | Who asked the question. For audit trail. |
| `role` | String | `"admin"` | User's role. For access control auditing. |
| `user_query` | String | `"What is the batch yield for Site A?"` | The exact question asked (truncated to 500 chars for safety). |
| `path_taken` | String | `"SLOW_PATH"` | Which execution path the AI chose. See table below. |
| `route_type` | String | `"KPI"` | How the Supervisor routed the query: `KPI`, `COMPLEX`, or `CLARIFY`. |
| `matched_kpi` | String | `"batch_yield"` | Which KPI was matched (null for complex/clarify queries). |
| `narrative_summary` | String | `"The batch yield for Site A is 94.2%..."` | The AI's answer (truncated to 2000 chars). |
| `generated_sql` | String | `"SELECT avg(yield) FROM..."` | The SQL query generated (for debugging). |
| `visualization_config` | Map | `{"type": "bar", ...}` | Chart configuration returned to frontend. Stored as **native DynamoDB Map** (not JSON string) so it's readable in the console. |
| `agent_logs` | List | `[{"agent_name": "Supervisor", ...}]` | Execution trace — which agents ran, how long each took, success/failure. |
| `total_execution_ms` | Number | `1250` | Total time from request to response in milliseconds. |
| `cache_hit_count` | Number | `3` | How many times this cached result was reused. Helps measure cache effectiveness. |
| `created_at_utc` | String | `"2026-03-09T10:30:15Z"` | When this turn was created (ISO 8601). |
| `ttl` | Number | `1741607415` | **Time-To-Live.** Unix epoch timestamp. DynamoDB auto-deletes this row after this time. |

### Path Types Explained

| Path | What Happens | Typical Latency | Cost |
|------|-------------|-----------------|------|
| `CACHE_HIT` | Same question was asked before. Return cached answer. | <100ms | ~$0.00 |
| `FAST_PATH` | Simple KPI lookup. Supervisor → KPI Agent → Validator → Viz. | 3-5 sec | ~$0.01 |
| `SLOW_PATH` | Complex analysis. Supervisor → Analyst Agent → Validator → Viz. | 8-15 sec | ~$0.03-0.05 |

### TTL Strategy (Auto-Deletion)

| Route Type | TTL | Why |
|-----------|-----|-----|
| KPI queries | 6 hours | KPI data updates periodically. A 6-hour-old "batch yield" answer is likely stale. |
| Complex analysis | 2 hours | Complex answers depend on current data context. Goes stale faster. |
| Clarification | 5 minutes | "What do you mean?" responses are session-specific. No reuse value. |
| Audit records | 24 hours | Keep for daily compliance review, then auto-delete. |

### GSI: QueryCacheIndex

```
GSI Name:       QueryCacheIndex
Partition Key:  query_hash (String)
Sort Key:       created_at_utc (String)
Projection:     INCLUDE [narrative_summary, visualization_config,
                         generated_sql, agent_logs, route_type,
                         matched_kpi, is_valid]
```

**What this enables:** When a user asks a question, we hash it and query this GSI: *"Has this exact question been answered before?"* If yes, return the cached result without running any agents.

**Why a GSI and not the main table?** The main table is keyed by `tenant_id#session_id` — good for "show me this session's history." But for cache lookup, we need to search by *question content* across all sessions. The GSI re-indexes the same data by `query_hash`.

---

## 4. Table 2: `mia_chat_sessions` — The Conversation Memory

### What It Stores

The full conversation history for each user — every question they asked and every answer the AI gave, organized by session.

Think of it like **ChatGPT's sidebar** — a list of your past conversations, and clicking one shows the full message thread.

### Why This Table Exists

1. **Conversation Context** — When a user asks "Break that down by site," the AI needs to know what "that" refers to. This table provides the previous messages as context.
2. **Session Resumption** — User closes their browser, comes back tomorrow, and continues the conversation.
3. **User Experience** — Show a list of past sessions in the sidebar with titles like "Batch Yield Analysis" or "Site Comparison Q1."

### Schema

```
Table Name: mia_chat_sessions

┌──────────────────────────────────────────────────────────────────┐
│ KEY DESIGN                                                        │
│                                                                   │
│ Partition Key (pk):  {tenant_id}#{user_id}                        │
│                      Example: "default#harish"                    │
│                                                                   │
│ Sort Key (sk):       SESSION#{session_id}        (for metadata)   │
│                      MSG#{session_id}#{timestamp} (for messages)  │
└──────────────────────────────────────────────────────────────────┘
```

**Why this key design?**

- **Partition Key** is `tenant_id#user_id`. This means *"Show me all of Harish's sessions"* is a single DynamoDB Query — no GSI needed. This is the most common access pattern (loading the sidebar).
- **Sort Key** uses prefixes to store **two types of items** in the same partition:
  - `SESSION#...` items hold session metadata (title, message count, status)
  - `MSG#...` items hold individual messages

This is called **vertical partitioning** — instead of cramming all messages into one JSON blob, each message is its own DynamoDB item.

### Why Individual Messages Instead of a JSON Blob?

DynamoDB has a **400KB item size limit**. Here's the math:

| Scenario | Message Size | Count | Total Size | Status |
|----------|-------------|-------|-----------|--------|
| Short KPI session | ~2 KB | 10 | 20 KB | Safe |
| Medium analysis session | ~5 KB | 20 | 100 KB | Safe |
| Long power-user session | ~8 KB | 40 | 320 KB | Risky |
| Heavy session with SQL + charts | ~10 KB | 50 | 500 KB | **FAILS** |

With individual items, each message is 2-10 KB — well under the 400KB limit. A session can have **thousands** of messages safely.

**Other benefits:**
- **Faster writes:** Appending a new message = one PutItem call. No need to read the entire blob, deserialize, append, re-serialize, and write back.
- **Partial reads:** "Get the last 20 messages" uses `Limit=20, ScanIndexForward=False` — DynamoDB only reads 20 items, not the entire history.
- **No race conditions:** Two concurrent requests can both write messages without overwriting each other.

### Item Type 1: Session Metadata

One item per session. Stores the session's "header" information.

```json
{
  "pk":            "default#harish",
  "sk":            "SESSION#sess-abc123",
  "session_id":    "sess-abc123",
  "tenant_id":     "default",
  "user_id":       "harish",
  "title":         "Batch Yield Analysis",
  "created_at":    "2026-03-09T10:30:00Z",
  "last_active":   "2026-03-09T11:45:00Z",
  "message_count": 12,
  "status":        "active",
  "ttl":           1744300000
}
```

| Attribute | Why It Exists |
|-----------|---------------|
| `title` | Auto-generated from the first question (first 45 chars). Shown in the sidebar. |
| `last_active` | Updated on every new message. Used for sorting sessions by recency. |
| `message_count` | Quick count without scanning all messages. Shown in the sidebar. |
| `status` | `active` or `archived`. Users can archive old sessions. |

### Item Type 2: Individual Message

One item per message (user question or AI answer).

```json
{
  "pk":            "default#harish",
  "sk":            "MSG#sess-abc123#2026-03-09T10:30:15Z#001",
  "session_id":    "sess-abc123",
  "role":          "human",
  "content":       "What is the batch yield for Site A?",
  "timestamp":     "2026-03-09T10:30:15Z",
  "message_index": 1,
  "metadata": {
    "route_type":   "KPI",
    "matched_kpi":  "batch_yield",
    "execution_ms": 1250
  },
  "ttl":           1744300000
}
```

```json
{
  "pk":            "default#harish",
  "sk":            "MSG#sess-abc123#2026-03-09T10:30:20Z#002",
  "session_id":    "sess-abc123",
  "role":          "ai",
  "content":       "The batch yield for Site A is 94.2%...",
  "timestamp":     "2026-03-09T10:30:20Z",
  "message_index": 2,
  "visualization_config": {
    "type": "bar",
    "x_axis": "month",
    "y_axis": "yield_pct"
  },
  "ttl":           1744300000
}
```

| Attribute | Why It Exists |
|-----------|---------------|
| `role` | `"human"` (user) or `"ai"` (assistant). Needed to reconstruct the conversation. |
| `content` | The actual message text. |
| `message_index` | Sequential number (1, 2, 3...). Ensures correct ordering even if timestamps collide. |
| `metadata` | AI execution details — only present on AI responses. Native DynamoDB Map. |
| `visualization_config` | Chart config — only present on AI responses that include charts. |

### Common Access Patterns

| What You Want | How to Query |
|--------------|-------------|
| List all of Harish's sessions | `Query pk="default#harish", sk begins_with "SESSION#"` |
| Get last 20 messages in a session | `Query pk="default#harish", sk begins_with "MSG#sess-abc123", Limit=20, ScanIndexForward=False` |
| Get session metadata only | `GetItem pk="default#harish", sk="SESSION#sess-abc123"` |
| Delete a session | `Query` all items with `sk begins_with "SESSION#sess-abc123" or "MSG#sess-abc123"`, then `BatchWriteItem` delete |

### TTL Strategy

- **Active sessions:** TTL = `last_active` + 30 days. Resets every time the user sends a message.
- **Archived sessions:** TTL = archive date + 90 days.
- **All messages inherit the session's TTL** — when a session expires, all its messages expire too.

---

## 5. How the Two Tables Work Together

Here's what happens when a user sends a message:

```
User: "What is the batch yield for Site A?"
                    │
                    ▼
        ┌─────────────────────┐
        │ 1. Hash the question │
        │    → "a1b2c3d4..."   │
        └──────────┬──────────┘
                   │
                   ▼
        ┌─────────────────────────────────┐
        │ 2. Check mia_session_turns GSI   │
        │    QueryCacheIndex:              │
        │    query_hash = "a1b2c3d4..."    │
        └──────────┬──────────────────────┘
                   │
            ┌──────┴──────┐
            │             │
         CACHE HIT     CACHE MISS
            │             │
            ▼             ▼
     Return cached    Run full AI pipeline
     answer           (Supervisor → KPI/Analyst
     (< 100ms)        → Validator → Viz)
            │             │
            │             ▼
            │    ┌─────────────────────────┐
            │    │ 3. Save trace to         │
            │    │    mia_session_turns      │
            │    │    (for future cache hits │
            │    │     and audit trail)      │
            │    └─────────────────────────┘
            │             │
            └──────┬──────┘
                   │
                   ▼
        ┌─────────────────────────────────┐
        │ 4. Save message to               │
        │    mia_chat_sessions              │
        │    (user question + AI answer     │
        │     as two separate items)        │
        └──────────┬──────────────────────┘
                   │
                   ▼
        ┌─────────────────────────────────┐
        │ 5. Update session META           │
        │    (last_active, message_count,   │
        │     reset TTL)                    │
        └─────────────────────────────────┘
```

---

## 6. Cost Estimate

DynamoDB on-demand pricing (us-east-1):

| Operation | Price |
|-----------|-------|
| Write (1 KB) | $1.25 per million |
| Read (4 KB) | $0.25 per million |
| Storage | $0.25 per GB/month |

**Per user question (cache miss):**
- 1 trace write (~2 KB) = $0.0000025
- 2 message writes (~4 KB each) = $0.000005
- 1 META update = $0.00000125
- **Total: ~$0.000009** (effectively free)

**Per user question (cache hit):**
- 1 GSI read = $0.00000025
- 2 message writes = $0.000005
- **Total: ~$0.000005** (even more free)

**Savings from caching:** Each cache hit avoids ~$0.01-0.05 in Bedrock (Claude) API costs. If 30% of questions are repeated, caching saves **$3-15 per 1000 questions** in AI costs alone.

---

## 7. Infrastructure (CDK)

Both tables are defined in the CDK stack at `mia-langgraph/infra/lib/mia-stack.ts` and deployed via:

```bash
cd mia-langgraph
bash scripts/build-lambda.sh    # Rebuild Lambda with new code
cd infra && npx cdk deploy       # Deploy infrastructure
```

### Session Table

```typescript
const sessionTable = new dynamodb.Table(this, "MiaChatSessions", {
  tableName: "mia_chat_sessions",
  partitionKey: { name: "pk", type: dynamodb.AttributeType.STRING },
  sortKey:      { name: "sk", type: dynamodb.AttributeType.STRING },
  billingMode:  dynamodb.BillingMode.PAY_PER_REQUEST,
  removalPolicy: cdk.RemovalPolicy.DESTROY,
  timeToLiveAttribute: "ttl",
});
```

### Trace Table

```typescript
const traceTable = new dynamodb.Table(this, "MiaSessionTurns", {
  tableName: "mia_session_turns",
  partitionKey: { name: "pk", type: dynamodb.AttributeType.STRING },
  sortKey:      { name: "sk", type: dynamodb.AttributeType.STRING },
  billingMode:  dynamodb.BillingMode.PAY_PER_REQUEST,
  removalPolicy: cdk.RemovalPolicy.DESTROY,
  timeToLiveAttribute: "ttl",
});

// GSI for cache lookups by question hash
traceTable.addGlobalSecondaryIndex({
  indexName: "QueryCacheIndex",
  partitionKey: { name: "query_hash", type: dynamodb.AttributeType.STRING },
  sortKey:      { name: "created_at_utc", type: dynamodb.AttributeType.STRING },
  projectionType: dynamodb.ProjectionType.INCLUDE,
  nonKeyAttributes: [
    "narrative_summary", "visualization_config", "generated_sql",
    "agent_logs", "route_type", "matched_kpi", "is_valid",
  ],
});
```

---

## 8. Summary

| | `mia_session_turns` | `mia_chat_sessions` |
|---|---|---|
| **Purpose** | Audit trail + query cache | Conversation memory |
| **Think of it as** | Flight recorder | Chat history sidebar |
| **PK** | `tenant#session` | `tenant#user` |
| **SK** | `timestamp#request` | `SESSION#id` or `MSG#id#time` |
| **TTL** | 2-24 hours (route-based) | 30 days (resets on activity) |
| **GSI** | QueryCacheIndex (by query_hash) | None needed |
| **Item count per session** | 1 per question asked | 1 META + 1 per message |
| **Key benefit** | Saves AI costs via caching | Enables follow-up conversations |

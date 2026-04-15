# Sustainability Insight Agent (SIA) - Architecture

## System Overview

The Sustainability Insight Agent (SIA) is a multi-agent AI system built on LangGraph that enables natural language queries against sustainability data. It uses AWS Bedrock Claude models for intent classification and response generation, with deterministic SQL execution via DuckDB.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                         USER                                            │
└─────────────────────────────────────────┬───────────────────────────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND (React + TypeScript)                              │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐  │
│  │  ChatInterface   │  │ AgentFlowPanel   │  │VisualizationPanel│  │    SqlPanel    │  │
│  │  - Message List  │  │ - Agent Timeline │  │ - Bar/Line/Pie   │  │ - SQL Display  │  │
│  │  - Input Box     │  │ - Status Icons   │  │ - Recharts       │  │ - Copy Button  │  │
│  │  - Quick Actions │  │ - Reasoning      │  │ - Toggle Views   │  │                │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘  └────────────────┘  │
└─────────────────────────────────────────┬───────────────────────────────────────────────┘
                                          │ HTTPS (POST /api/query)
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                  AWS CLOUD (us-east-1)                                  │
│                                                                                         │
│  ┌──────────────────────────────────────────────────────────────────────────────────┐  │
│  │                            CloudFront Distribution                                │  │
│  │   - Edge caching for static assets    - CORS enabled                             │  │
│  │   - API passthrough (no cache)        - SPA error handling (404 → index.html)    │  │
│  └──────────────────────────────────┬───────────────────────────────────────────────┘  │
│                     ┌───────────────┴───────────────┐                                  │
│                     ▼                               ▼                                  │
│  ┌──────────────────────────────┐    ┌──────────────────────────────┐                  │
│  │      S3 (Static Assets)      │    │      API Gateway (REST)      │                  │
│  │   - React build (index.html) │    │   - Stage: prod              │                  │
│  │   - JS/CSS bundles           │    │   - Throttle: 100 req/s      │                  │
│  │   - Origin Access Identity   │    │   - Lambda Proxy Integration │                  │
│  └──────────────────────────────┘    └──────────────┬───────────────┘                  │
│                                                      │                                  │
│                                                      ▼                                  │
│  ┌───────────────────────────────────────────────────────────────────────────────────┐ │
│  │                           Lambda Function (Python 3.11)                            │ │
│  │   Memory: 2048 MB  |  Timeout: 120s  |  Handler: lambda_handler.handler           │ │
│  │                                                                                    │ │
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐  │ │
│  │  │                    FastAPI Application (via Mangum)                          │  │ │
│  │  │   Endpoints:                                                                 │  │ │
│  │  │   - POST /api/query          → Process user query                           │  │ │
│  │  │   - GET  /api/sessions/{id}/telemetry → Agent execution logs                │  │ │
│  │  │   - GET  /api/kpis           → List available KPIs                          │  │ │
│  │  │   - GET  /health             → Health check                                 │  │ │
│  │  └─────────────────────────────────────────────────────────────────────────────┘  │ │
│  │                                        │                                           │ │
│  │                                        ▼                                           │ │
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐  │ │
│  │  │                         LangGraph Workflow Engine                            │  │ │
│  │  │                                                                              │  │ │
│  │  │   ┌─────────────┐                                                            │  │ │
│  │  │   │ SUPERVISOR  │ ─── Semantic Routing (Embeddings + Keywords)               │  │ │
│  │  │   └──────┬──────┘                                                            │  │ │
│  │  │          │                                                                   │  │ │
│  │  │    ┌─────┴─────┬─────────────┐                                               │  │ │
│  │  │    ▼           ▼             ▼                                               │  │ │
│  │  │ ┌──────┐  ┌─────────┐  ┌──────────┐                                          │  │ │
│  │  │ │ KPI  │  │ ANALYST │  │ CLARIFY  │                                          │  │ │
│  │  │ │AGENT │  │  AGENT  │  │          │                                          │  │ │
│  │  │ └──┬───┘  └────┬────┘  └────┬─────┘                                          │  │ │
│  │  │    │           │            │                                                │  │ │
│  │  │    ▼           ▼            │                                                │  │ │
│  │  │ ┌──────────────────┐        │                                                │  │ │
│  │  │ │    VALIDATOR     │        │                                                │  │ │
│  │  │ └────────┬─────────┘        │                                                │  │ │
│  │  │          │                  │                                                │  │ │
│  │  │    ┌─────┴─────┐            │                                                │  │ │
│  │  │    ▼           ▼            │                                                │  │ │
│  │  │ ┌──────┐  ┌────────┐        │                                                │  │ │
│  │  │ │ VIZ  │  │  END   │◄───────┘                                                │  │ │
│  │  │ │AGENT │  └────────┘                                                         │  │ │
│  │  │ └──┬───┘                                                                     │  │ │
│  │  │    ▼                                                                         │  │ │
│  │  │ ┌────────┐                                                                   │  │ │
│  │  │ │  END   │                                                                   │  │ │
│  │  │ └────────┘                                                                   │  │ │
│  │  └─────────────────────────────────────────────────────────────────────────────┘  │ │
│  │                                        │                                           │ │
│  │                    ┌───────────────────┼───────────────────┐                       │ │
│  │                    ▼                   ▼                   ▼                       │ │
│  │  ┌─────────────────────┐  ┌─────────────────┐  ┌─────────────────────┐            │ │
│  │  │     AWS Bedrock     │  │     DuckDB      │  │     CSV Data        │            │ │
│  │  │  - Claude Sonnet    │  │  (In-Memory)    │  │   /data/KPI/        │            │ │
│  │  │  - Titan Embeddings │  │  SQL Execution  │  │   /data/Transact/   │            │ │
│  │  └─────────────────────┘  └─────────────────┘  │   /data/Master/     │            │ │
│  │                                                 └─────────────────────┘            │ │
│  └───────────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Agent Workflow Detail

```
                                    ┌─────────────────┐
                                    │   User Query    │
                                    └────────┬────────┘
                                             │
                                             ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                    SUPERVISOR AGENT                                    │
│  ┌──────────────────────────────────────────────────────────────────────────────────┐ │
│  │ 1. Check transactional data patterns (diesel, powertrain, fleet asset, etc.)     │ │
│  │ 2. Semantic embedding match against KPI catalogue                                 │ │
│  │ 3. Keyword boosting (energy, emissions, water, waste, EV)                        │ │
│  │ 4. LLM verification for medium confidence matches                                 │ │
│  └──────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                        │
│  Route Decision:                                                                       │
│  • Confidence > 0.6 → KPI Agent                                                       │
│  • Transactional patterns → Analyst Agent                                             │
│  • Low confidence → LLM routing or Clarify                                            │
└────────────────────────────┬─────────────────────────────┬─────────────────────────────┘
                             │                             │
              ┌──────────────┴──────────────┐              │
              ▼                             ▼              ▼
┌──────────────────────────┐  ┌──────────────────────────┐  ┌────────────────────┐
│       KPI AGENT          │  │     ANALYST AGENT        │  │      CLARIFY       │
│                          │  │                          │  │                    │
│ 1. Intent Classification │  │ 1. Semantic Table Search │  │ Return prompt for  │
│    (Structured Output)   │  │    (Embeddings + Boost)  │  │ more information   │
│                          │  │                          │  │                    │
│ 2. SQL Template Render   │  │ 2. Load Selected Tables  │  └─────────┬──────────┘
│    (Deterministic)       │  │    (Top 3 matches)       │            │
│                          │  │                          │            │
│ 3. DuckDB Execution      │  │ 3. Build Data Context    │            │
│    (In-Memory SQL)       │  │    (Aggregations/Stats)  │            │
│                          │  │                          │            │
│ 4. LLM Response Format   │  │ 4. LLM Analysis          │            │
│    (Tables + Insights)   │  │    (Professional Report) │            │
│                          │  │                          │            │
│ 5. Visualization Config  │  │ 5. No Visualization      │            │
│    (Bar/Line Charts)     │  │                          │            │
└────────────┬─────────────┘  └────────────┬─────────────┘            │
             │                             │                          │
             └──────────────┬──────────────┘                          │
                            ▼                                         │
              ┌──────────────────────────┐                            │
              │     VALIDATOR AGENT      │                            │
              │                          │                            │
              │ • Response length check  │                            │
              │ • Error pattern detect   │                            │
              │ • Data presence verify   │                            │
              └────────────┬─────────────┘                            │
                           │                                          │
              ┌────────────┴────────────┐                             │
              │ Has visualization_config?│                             │
              └────────────┬────────────┘                             │
                    ┌──────┴──────┐                                   │
                    │ Yes         │ No                                │
                    ▼             ▼                                   │
        ┌────────────────┐  ┌─────────┐                               │
        │ VISUALIZATION  │  │   END   │◄──────────────────────────────┘
        │     AGENT      │  └─────────┘
        │                │
        │ • Verify chart │
        │ • Format series│
        └───────┬────────┘
                ▼
          ┌─────────┐
          │   END   │
          └─────────┘
```

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                    DATA LAYER                                        │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│   /data/KPI/                           /data/Transactional/                         │
│   ┌─────────────────────────────┐      ┌─────────────────────────────┐              │
│   │ energy_monthly_summary      │      │ fleet_asset_inventory       │              │
│   │ energy_quarterly_summary    │      │ fleet_fuel_consumption      │              │
│   │ ghg_emissions_monthly       │      │ fleet_mileage               │              │
│   │ ghg_emissions_quarterly     │      │ energy_consumption          │              │
│   │ water_monthly_summary       │      │ water_usage                 │              │
│   │ waste_monthly_summary       │      │ greenhouse_gas_emissions    │              │
│   │ ev_transition_quarterly     │      │ waste_record                │              │
│   └─────────────────────────────┘      └─────────────────────────────┘              │
│              │                                    │                                  │
│              │ KPI Agent queries                  │ Analyst Agent queries           │
│              ▼                                    ▼                                  │
│   ┌─────────────────────┐              ┌─────────────────────┐                      │
│   │      DuckDB         │              │       Pandas        │                      │
│   │  (SQL Execution)    │              │   (Data Loading)    │                      │
│   └─────────────────────┘              └─────────────────────┘                      │
│                                                                                      │
│   /data/Master/                                                                      │
│   ┌─────────────────────────────┐                                                   │
│   │ she_site.csv (Sites)        │                                                   │
│   │ she_indicator.csv (Metrics) │                                                   │
│   │ she_geography.csv (Regions) │                                                   │
│   └─────────────────────────────┘                                                   │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## KPI Agent - Structured Output Pattern

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                        STRUCTURED OUTPUT APPROACH                                    │
│                                                                                      │
│   "LLM classifies WHAT, Code renders HOW"                                           │
│                                                                                      │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│   User Query: "What are the greenhouse gas emissions by scope type?"                │
│                                                                                      │
│   Step 1: INTENT CLASSIFICATION (LLM)                                               │
│   ┌─────────────────────────────────────────────────────────────────────────────┐   │
│   │  LLM Output (JSON):                                                          │   │
│   │  {                                                                           │   │
│   │    "intent": "GHG_BY_SCOPE",                                                 │   │
│   │    "time_type": "current_year",                                              │   │
│   │    "geography": null                                                         │   │
│   │  }                                                                           │   │
│   └─────────────────────────────────────────────────────────────────────────────┘   │
│                                       │                                              │
│                                       ▼                                              │
│   Step 2: SQL TEMPLATE LOOKUP (Deterministic)                                       │
│   ┌─────────────────────────────────────────────────────────────────────────────┐   │
│   │  SQL_TEMPLATES["GHG_BY_SCOPE"]:                                              │   │
│   │                                                                              │   │
│   │  SELECT 'Scope 1' as SCOPE_TYPE,                                             │   │
│   │         SUM(SCOPE1_SITE_ENERGY_TCO2_QUANTITY +                               │   │
│   │             SCOPE1_F_GASES_TCO2_QUANTITY +                                   │   │
│   │             SCOPE1_SITE_NON_ENERGY_TCO2_QUANTITY +                           │   │
│   │             SCOPE1_SOLVENTS_TCO2_QUANTITY) as EMISSIONS_TCO2                 │   │
│   │  FROM GREENHOUSE_GAS_EMISSIONS_MONTHLY_SUMMARY                               │   │
│   │  WHERE REPORTING_YEAR_NUMBER = 2025                                          │   │
│   │  UNION ALL ...                                                               │   │
│   └─────────────────────────────────────────────────────────────────────────────┘   │
│                                       │                                              │
│                                       ▼                                              │
│   Step 3: EXECUTE SQL (DuckDB)                                                      │
│   ┌─────────────────────────────────────────────────────────────────────────────┐   │
│   │  Result:                                                                     │   │
│   │  ┌────────────────────┬────────────────┐                                    │   │
│   │  │ SCOPE_TYPE         │ EMISSIONS_TCO2 │                                    │   │
│   │  ├────────────────────┼────────────────┤                                    │   │
│   │  │ Scope 1            │ 3,529.61       │                                    │   │
│   │  │ Scope 2            │ 1,845.45       │                                    │   │
│   │  │ Total (Scope 1+2)  │ 5,375.06       │                                    │   │
│   │  └────────────────────┴────────────────┘                                    │   │
│   └─────────────────────────────────────────────────────────────────────────────┘   │
│                                       │                                              │
│                                       ▼                                              │
│   Step 4: FORMAT RESPONSE (LLM)                                                     │
│   ┌─────────────────────────────────────────────────────────────────────────────┐   │
│   │  Professional markdown response with:                                        │   │
│   │  - Summary statement with total                                              │   │
│   │  - Data table using EXACT values from SQL                                    │   │
│   │  - Key observations and insights                                             │   │
│   └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## AWS Services

| Service | Purpose | Configuration |
|---------|---------|---------------|
| **Lambda** | Backend compute | Python 3.11, 2GB RAM, 120s timeout |
| **API Gateway** | REST API | Proxy integration, 100 req/s throttle |
| **S3** | Frontend hosting | Private bucket with OAI |
| **CloudFront** | CDN & routing | Edge caching, API passthrough |
| **Bedrock** | LLM inference | Claude Sonnet, Titan Embeddings |

---

## LLM Models

| Agent | Model | Purpose |
|-------|-------|---------|
| Supervisor | Claude 3.5 Sonnet | Query routing & verification |
| KPI Agent | Claude 3.5 Sonnet | Intent classification & response |
| Analyst Agent | Claude Sonnet 4 | Complex analysis & reports |
| Validator | Claude 3.5 Haiku | Quick validation checks |
| Embeddings | Titan v2 | Semantic similarity matching |

---

## Key Design Patterns

### 1. Semantic Routing
- Embeddings match queries to KPIs/tables
- Keyword boosting for domain terms
- LLM fallback for ambiguous queries

### 2. Structured Output
- LLM classifies intent (WHAT)
- Code renders SQL (HOW)
- Eliminates SQL hallucination

### 3. Deterministic Execution
- Pre-defined SQL templates
- DuckDB in-memory queries
- Consistent, reproducible results

### 4. Multi-Agent Telemetry
- Each agent logs execution details
- Timeline visualization in UI
- Full audit trail

### 5. Conditional Visualization
- Charts only for KPI queries with data
- Skip visualization for text-only responses
- Dynamic chart type selection

---

## Directory Structure

```
sustainability-langgraph/
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   │   ├── supervisor.py      # Query routing
│   │   │   ├── kpi_agent.py       # KPI queries + SQL
│   │   │   ├── analyst_agent.py   # Complex analysis
│   │   │   ├── validator_agent.py # Response validation
│   │   │   └── visualization_agent.py
│   │   ├── core/
│   │   │   └── config.py          # Settings
│   │   ├── models/
│   │   │   └── state.py           # SIAState definition
│   │   ├── tools/
│   │   │   ├── data_catalogue.py  # KPI definitions
│   │   │   └── data_table_catalogue.py
│   │   └── graph.py               # LangGraph workflow
│   ├── data/
│   │   ├── KPI/                   # Summary CSV files
│   │   ├── Transactional/         # Detail CSV files
│   │   └── Master/                # Reference data
│   ├── main.py                    # FastAPI app
│   ├── lambda_handler.py          # Lambda adapter
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatInterface.tsx
│   │   │   ├── AgentFlowPanel.tsx
│   │   │   ├── VisualizationPanel.tsx
│   │   │   └── SqlPanel.tsx
│   │   ├── api/
│   │   │   └── chatApi.ts
│   │   └── types/
│   │       └── index.ts
│   └── package.json
├── infra/
│   └── lib/
│       └── sia-stack.ts           # CDK infrastructure
└── scripts/
    └── build-lambda.sh            # Build script
```

---

## Response Flow Example

```
User: "What was our total energy consumption last year?"

1. Supervisor → Routes to KPI Agent (energy keywords + high confidence)

2. KPI Agent:
   - Intent: ENERGY_TOTAL_LAST_YEAR
   - SQL: SELECT SUM(ENERGY_TOTAL_MWH_QUANTITY) FROM energy_monthly_summary WHERE REPORTING_YEAR_NUMBER = 2024
   - Result: 244,650.66 MWh
   - Response: Formatted markdown with table and insights

3. Validator → Passes (response has data, no errors)

4. Visualization → Generates bar chart with monthly breakdown

5. Return:
   {
     "answer": "**Total Energy Consumption** is **244,650.66 MWh**...",
     "visualization_config": { chartType: "bar", series: [...] },
     "generated_sql": "SELECT ...",
     "agent_logs": [supervisor, kpi_agent, validator, visualization]
   }
```

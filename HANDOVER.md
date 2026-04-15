# Handover Document — Devesh Sharma (Accenture)

**Prepared:** 2026-04-14
**Outgoing:** Devesh Sharma
**Workspace root:** `/Users/devesh.b.sharma/Astra Zeneca/`

This document captures the state of the three active client engagements at the point of my departure so work can continue without context loss. For each engagement I list: **client & stakeholders**, **scope**, **current status**, **artefacts (where to find them)**, and **open items / next steps**.

---

## 1. AstraZeneca — AI MDM (Agentic MDM POC)

### Client & context
- **Client:** AstraZeneca
- **Engagement type:** Proof of Concept — Agentic Master Data Management
- **Goal:** Conversational interface for MDM (HCP / HCO records) with **enforced governance**: search-before-create, duplicate detection, controlled merges. Demonstrates that an LLM agent can safely act on top of a Reltio-shaped MDM backend.

### Scope / architecture
Built as a swappable-backend demo so it can move from mock to a real Reltio tenant without code changes.

```
React chat (5180)  →  LangGraph backend (3010)  →  Mock Reltio (8765)
                         ↑                              ↑
                      Bedrock                       in-memory store
                      Claude Sonnet 4.5             + JSON persist
```

- Stack: **Claude (AWS Bedrock) + LangGraph + FastAPI + React**
- Mock Reltio service mirrors Reltio's REST API shape. Switching to real Reltio only requires setting `RELTIO_BASE_URL` and `RELTIO_AUTH_TOKEN` in `backend/.env` — no code change.

### Where the code lives
- [AI MDM/README.md](AI%20MDM/README.md) — run instructions, demo prompts, switching to real Reltio
- [AI MDM/backend/](AI%20MDM/backend/) — LangGraph + FastAPI agent
- [AI MDM/frontend/](AI%20MDM/frontend/) — React chat UI
- [AI MDM/mock-reltio/](AI%20MDM/mock-reltio/) — Reltio-shaped mock service

### Demo scenarios (working)
- `Add Dr. Sara Chen, oncologist in Boston MA` — finds 3 duplicates, asks for confirmation
- `Find all oncologists in Boston` — discovery query
- `Add Dr. Alex Kowalski, neurosurgeon in Pittsburgh PA, NPI 9988776655` — no duplicates, creates
- `Add a new hospital called Mass General Hospital in Boston MA` — HCO fuzzy match

### Status
- POC is **runnable end-to-end** against mock Reltio.
- Supporting deck: [R&D IT/AI-MDM-DataOps-DataGovernance.pptx](R%26D%20IT/AI-MDM-DataOps-DataGovernance.pptx).

### Open items / next steps
- Provisioning of real Reltio **trial tenant** — once available, flip env vars and validate the same four demo scenarios against live data.
- Production hardening not yet done (auth, audit log persistence, rate limits on merge).
- No CI/CD pipeline yet — POC is run locally in three terminals.

---

## 2. AstraZeneca — R&D IT (Agentic AI on 3DP & BIKG)

### Client & context
- **Client:** AstraZeneca R&D IT
- **Target platforms:** **3DP** (Drug Development Data Platform) and **BIKG** (Biological Intelligence Knowledge Graph)
- **Engagement type:** Agentic AI MVP — 9-month plan (Mar 2026 → Nov 2026)

### Scope — 4 agents integrated with the AZ Agent Mesh

| Agent | Phase | Primary function | Platforms |
|---|---|---|---|
| Test Intelligence Agent | 1 (Months 1–3) | Automated test case generation | 3DP, BIKG |
| Dependency Coordinator | 2 | Cross-platform dependency tracking | 3DP, BIKG |
| Knowledge Library Companion | 3 | RAG-powered documentation Q&A | 3DP, BIKG |
| Auto-Lineage Agent | Enhancement | Automated data lineage tracking | 3DP, BIKG |

### Architecture (summary)
Three layers: **Agent Mesh Control Plane** (registry, policy, observability, secrets) → **Agent Runtimes on ECS Fargate** → **MCP Servers** for 3DP, BIKG, Jira/ADO, Confluence, Data Catalog, GitHub. Full spec in [R&D IT/agent-mesh-architecture-spec.md](R%26D%20IT/agent-mesh-architecture-spec.md).

### Team plan (from 9-month plan)
- Core team: 8–10 FTEs — Tech Lead, 2× Sr ML Engineer, 2× Backend, 1× Frontend, 1× Data Eng, 1× QA, 1× PO.
- Part-time SMEs: 3DP (20%), BIKG (20%), AI Ops (10%), Data Foundation (10%).

### Where the artefacts live
- [R&D IT/Agentic-AI-9-Month-Plan.md](R%26D%20IT/Agentic-AI-9-Month-Plan.md) — phased timeline, deliverables per phase
- [R&D IT/agent-mesh-architecture-spec.md](R%26D%20IT/agent-mesh-architecture-spec.md) — technical architecture spec (v1.0, Feb 2026, Draft)
- [R&D IT/RnD-IT-Agentic-AI-Presentation.pptx](R%26D%20IT/RnD-IT-Agentic-AI-Presentation.pptx) — exec deck
- [R&D IT/Test-Intelligence-Agent-Architecture.pptx](R%26D%20IT/Test-Intelligence-Agent-Architecture.pptx), [Test-Intelligence-Agent-Walkthrough.pptx](R%26D%20IT/Test-Intelligence-Agent-Walkthrough.pptx), [Test-Intelligence-Agent-Dashboard.pptx](R%26D%20IT/Test-Intelligence-Agent-Dashboard.pptx)
- [R&D IT/Agentic-AI-Testing-Dashboard.pptx](R%26D%20IT/Agentic-AI-Testing-Dashboard.pptx), [AI-for-AI-Test-Agent-Delivery.pptx](R%26D%20IT/AI-for-AI-Test-Agent-Delivery.pptx)
- HTML views: [agent-mesh-architecture.html](R%26D%20IT/agent-mesh-architecture.html), [rnd-it-agentic-ai-presentation.html](R%26D%20IT/rnd-it-agentic-ai-presentation.html), [rnd-it-infrastructure-architecture.html](R%26D%20IT/rnd-it-infrastructure-architecture.html)
- PPT generators: `R&D IT/create_*.py` — rerun to regenerate decks if content changes

### Status
- Architecture spec: **v1.0 Draft** (Feb 2026).
- 9-month plan: **agreed at planning level**; Phase 1 (Test Intelligence Agent MVP) scoped to Months 1–3.
- Decks for exec review and dashboards are prepared.
- **No agent code committed in this workspace for R&D IT** — delivery code lives in separate client repos (and/or is pending kickoff). The `R&D IT/` folder here is planning & artefacts.

### Open items / next steps
- Confirm Phase 1 kickoff and infra onboarding (AI Ops, Data Foundation).
- Finalise MCP server inventory and ownership (who builds 3DP-MCP, BIKG-MCP).
- Move architecture spec from Draft → Approved.
- Stakeholder / SME introductions — **ensure the incoming lead is introduced to the 3DP and BIKG platform owners and the AI Ops platform owner.** (Please fill in names below.)

---

## 3. Novo Nordisk — *(details to confirm)*

> **Note:** There is **no Novo Nordisk folder under this workspace** (`/Users/devesh.b.sharma/Astra Zeneca/`). Any Novo Nordisk work was either done in a separate repo, on a client-provided laptop, or in shared drives (SharePoint / Teams / Confluence) that are not mirrored locally. I have not fabricated status for this engagement — please fill in the sections below from the correct source before sharing this handover.

### To complete
- **Client contact / stakeholders:**
- **Engagement type (POC / pilot / production):**
- **Scope — what was being built:**
- **Current status:**
- **Where the code / docs live (repo URLs, SharePoint, Confluence):**
- **Open items / next steps:**
- **Any credentials / access the successor needs:**

---

## Cross-cutting: other workspace folders worth knowing about

These are adjacent AZ assets in the same workspace — not the three engagements above, but relevant context for whoever picks up:

- [mia-langgraph/](mia-langgraph/) — Manufacturing Insight Agent (LangGraph). Has AWS CDK infra ([mia-langgraph/infra/](mia-langgraph/infra/)) and is the reference stack the AI MDM backend reuses for Bedrock auth.
- [manufacturing-insight-agent/](manufacturing-insight-agent/) — earlier TypeScript-based MIA implementation.
- [sustainability-langgraph/](sustainability-langgraph/) — Sustainability Insight Agent (LangGraph).
- [mia-infrastructure/](mia-infrastructure/), [sa-infrastructure/](sa-infrastructure/) — Terraform AWS infra for MIA and Sustainability agents (recently renamed — see commit `13b97e9`).
- [test-intelligence-agent/](test-intelligence-agent/) — code spike referenced by the R&D IT Test Intelligence Agent design.

## Known data / ontology context (carries across engagements)
- Ontology gaps exist on KPI coverage. Two separate SQL question sets are in play: **Wushi's 30 SQL questions** vs **Avanti's separate set** — they are not interchangeable and should not be merged without stakeholder sign-off.
- Data products sit in Snowflake.

## Access / credentials the successor will need
- AWS account access for Bedrock (same profile used by mia-langgraph)
- AstraZeneca VPN / SSO
- Access to AZ Agent Mesh (once provisioned) for R&D IT work
- Reltio trial tenant (AI MDM — pending)
- Client-side Jira / Confluence / SharePoint for each engagement
- *Novo Nordisk — to be listed*

---

## Suggested handover meetings

1. **AI MDM** — 30 min walkthrough of the three-terminal demo + Reltio swap procedure.
2. **R&D IT** — 60 min review of 9-month plan + architecture spec with the incoming lead and the 3DP/BIKG SMEs.
3. **Novo Nordisk** — to be scheduled once section 3 is completed.

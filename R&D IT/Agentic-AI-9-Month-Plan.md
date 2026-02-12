# Agentic AI MVP - 9 Month Plan
## R&D IT Platforms: 3DP & BIKG

---

## Executive Summary

| Item | Details |
|------|---------|
| **Duration** | 9 Months (Mar 2026 - Nov 2026) |
| **Target Platforms** | 3DP (Drug Development Data Platform), BIKG (Biological Intelligence Knowledge Graph) |
| **Agents** | Test Intelligence, Dependency Coordinator, Knowledge Library Companion |
| **Team Size** | 8-10 FTEs |

---

## 3 Agents Overview

| Agent | Rank | Score | 3DP Value | BIKG Value |
|-------|------|-------|-----------|------------|
| **Test Intelligence Agent** | #1 | 4.30 | Regulatory validation testing | KG query testing |
| **Dependency Coordinator** | #2 | 4.05 | Submission timeline tracking | Data pipeline dependencies |
| **Knowledge Library Companion** | #5 | 4.00 | Regulatory guidance search | Biological knowledge Q&A |

---

## Team Structure

### Core Team (8-10 FTEs)

| Role | Count | Responsibilities |
|------|-------|------------------|
| **Tech Lead / Architect** | 1 | Overall architecture, AI Ops integration, technical decisions |
| **Senior ML Engineer** | 2 | LLM integration, prompt engineering, model fine-tuning |
| **Backend Engineer** | 2 | APIs, data pipelines, platform integrations |
| **Frontend Engineer** | 1 | Agent UIs, dashboards, user experience |
| **Data Engineer** | 1 | Data Foundation, embeddings, vector DB |
| **QA Engineer** | 1 | Testing, validation, quality assurance |
| **Product Owner** | 1 | Requirements, stakeholder management, prioritization |

### Platform SMEs (Part-time / Advisory)

| Platform | Role | Involvement |
|----------|------|-------------|
| **3DP** | Domain Expert | 20% - Regulatory requirements, submission workflows |
| **BIKG** | Domain Expert | 20% - Knowledge graph structure, biological ontologies |
| **AI Ops** | Platform Owner | 10% - Model gateway, infrastructure |
| **Data Foundation** | Platform Owner | 10% - Data access, storage |

---

## 9-Month Timeline

### Phase 1: Test Intelligence Agent (Months 1-3)

#### Month 1: Foundation
| Week | Milestone | Deliverables |
|------|-----------|--------------|
| 1-2 | Discovery & Design | Requirements doc, architecture design, API contracts |
| 3-4 | Infrastructure Setup | AI Ops integration, dev environment, CI/CD pipeline |

#### Month 2: Core Development
| Week | Milestone | Deliverables |
|------|-----------|--------------|
| 1-2 | LLM Integration | Test case generation from code/requirements |
| 3-4 | Embedding Service | Similar test failure detection |

#### Month 3: Platform Integration
| Week | Milestone | Deliverables |
|------|-----------|--------------|
| 1-2 | 3DP Integration | Regulatory validation test automation |
| 3-4 | BIKG Integration | Knowledge graph query testing |

**Phase 1 Deliverables:**
- [ ] Test Intelligence Agent MVP deployed
- [ ] 3DP: Automated test generation for 2 submission types
- [ ] BIKG: Query validation testing for core entity types
- [ ] 25% reduction in manual test effort (pilot)

---

### Phase 2: Dependency Coordinator (Months 4-6)

#### Month 4: Foundation
| Week | Milestone | Deliverables |
|------|-----------|--------------|
| 1-2 | Discovery & Design | Dependency model, data sources mapping |
| 3-4 | Data Ingestion | Jira, ADO, roadmap integrations |

#### Month 5: Core Development
| Week | Milestone | Deliverables |
|------|-----------|--------------|
| 1-2 | LLM Parsing | Extract dependencies from text/tickets |
| 3-4 | Graph Model | Dependency visualization, conflict detection |

#### Month 6: Platform Integration
| Week | Milestone | Deliverables |
|------|-----------|--------------|
| 1-2 | 3DP Integration | Submission timeline dependency tracking |
| 3-4 | BIKG Integration | Data pipeline dependency mapping |

**Phase 2 Deliverables:**
- [ ] Dependency Coordinator MVP deployed
- [ ] 3DP: Regulatory submission dependencies visualized
- [ ] BIKG: Cross-domain data pipeline dependencies mapped
- [ ] 1+ dependency conflict flagged early (pilot)

---

### Phase 3: Knowledge Library Companion (Months 7-9)

#### Month 7: Foundation
| Week | Milestone | Deliverables |
|------|-----------|--------------|
| 1-2 | Discovery & Design | Content inventory, RAG architecture |
| 3-4 | Document Ingestion | Confluence, SharePoint, platform docs indexed |

#### Month 8: Core Development
| Week | Milestone | Deliverables |
|------|-----------|--------------|
| 1-2 | RAG Pipeline | Semantic search, document retrieval |
| 3-4 | LLM Q&A | Natural language answers from docs |

#### Month 9: Platform Integration
| Week | Milestone | Deliverables |
|------|-----------|--------------|
| 1-2 | 3DP Integration | Regulatory guidance search, SOP lookup |
| 3-4 | BIKG Integration | Biological ontology Q&A, pathway docs |

**Phase 3 Deliverables:**
- [ ] Knowledge Library Companion MVP deployed
- [ ] 3DP: Regulatory docs searchable via natural language
- [ ] BIKG: Biological knowledge Q&A functional
- [ ] 50% faster time-to-answer for common questions

---

## Agent-Model-Platform Matrix

### Test Intelligence Agent

| Model Type | Purpose | 3DP Use Case | BIKG Use Case |
|-----------|---------|--------------|---------------|
| LLM (Claude) | Generate test cases | Regulatory validation tests | KG query tests |
| Code Model | Synthetic data generation | Patient data for testing | Biological entity data |
| Embedding Model | Similar failure detection | Past submission failures | Failed BIKG queries |

### Dependency Coordinator

| Model Type | Purpose | 3DP Use Case | BIKG Use Case |
|-----------|---------|--------------|---------------|
| LLM | Parse roadmaps/tickets | FDA/EMA submission timelines | Data pipeline schedules |
| Graph Model | Conflict prediction | Submission delay prediction | KG update conflicts |
| Embedding Model | Similar pattern matching | Past regulatory delays | Past dependency issues |

### Knowledge Library Companion

| Model Type | Purpose | 3DP Use Case | BIKG Use Case |
|-----------|---------|--------------|---------------|
| LLM | Answer questions | "How to prepare Module 3?" | "How to query gene-disease?" |
| Embedding Model | Semantic search | Regulatory guidelines, SOPs | Ontologies, data dictionaries |
| Summarization | Condense documents | FDA guidance summaries | Pathway doc summaries |

---

## Infrastructure Requirements

### AI Ops Components

| Component | Purpose | Priority |
|-----------|---------|----------|
| Model Gateway | API access to Claude/Bedrock | Critical |
| Embedding Service | Vector embeddings | Critical |
| Vector Database | Store/query embeddings | Critical |
| Prompt Management | Version control for prompts | High |
| Guardrails | PII filtering, rate limiting | High |
| Observability | Cost/latency tracking | Medium |

### Data Foundation Components

| Component | Purpose | Priority |
|-----------|---------|----------|
| Document Store | Platform docs, SOPs | Critical |
| Metadata Catalog | Data lineage, schemas | High |
| Search Index | Full-text + semantic search | Critical |

---

## Success Metrics

### Phase 1: Test Intelligence Agent
| Metric | Target | Measurement |
|--------|--------|-------------|
| Manual test effort reduction | 25% | Hours saved vs baseline |
| Test coverage increase | 15% | New edge cases discovered |
| Synthetic data quality | 90% valid | Data validation pass rate |

### Phase 2: Dependency Coordinator
| Metric | Target | Measurement |
|--------|--------|-------------|
| Dependencies mapped | 100+ | Across 3DP & BIKG |
| Conflicts flagged early | 3+ | Before becoming blockers |
| Timeline accuracy | 85% | Predicted vs actual |

### Phase 3: Knowledge Library Companion
| Metric | Target | Measurement |
|--------|--------|-------------|
| Time-to-answer reduction | 50% | Survey + usage data |
| Query success rate | 80% | Relevant answers returned |
| Documents indexed | 1000+ | 3DP + BIKG docs |

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| AI Ops not ready | Medium | High | Early engagement, fallback to direct Bedrock |
| Data access delays | Medium | Medium | Parallel data engineering track |
| Model quality issues | Low | Medium | Prompt iteration, human-in-the-loop |
| Adoption resistance | Medium | Medium | Early stakeholder involvement, demos |
| Scope creep | High | Medium | Strict MVP definition, PM governance |

---

## Budget Estimate

| Category | Monthly | 9-Month Total |
|----------|---------|---------------|
| Team (8 FTEs avg) | $120K | $1.08M |
| AI/ML Compute (Bedrock) | $15K | $135K |
| Infrastructure | $5K | $45K |
| **Total** | **$140K** | **$1.26M** |

*Note: Estimates based on standard AZ rates. Adjust based on actual resource allocation.*

---

## Governance

### Steering Committee
- Monthly reviews with Platform Owners (3DP, BIKG)
- Quarterly executive updates

### Sprint Cadence
- 2-week sprints
- Demo at end of each sprint
- Retrospective monthly

### Decision Log
- Architecture decisions documented in ADRs
- Trade-offs reviewed with Tech Lead + Platform SMEs

---

## Next Steps

1. **Week 1-2:** Finalize team allocation, confirm platform SME availability
2. **Week 3-4:** Kick-off Phase 1 (Test Intelligence Agent) discovery
3. **Month 1:** Complete architecture design, begin development

---

*Document Version: 1.0*
*Created: February 2026*
*Owner: R&D IT Agentic AI Team*

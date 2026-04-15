# R&D IT Agentic AI - Agent Mesh Architecture Specification

## Document Information
| Field | Value |
|-------|-------|
| **Version** | 1.0 |
| **Date** | February 2026 |
| **Status** | Draft |
| **Owner** | R&D IT Agentic AI Team |
| **Platforms** | 3DP, BIKG |

---

## 1. Executive Summary

This specification defines the architecture for integrating 4 Agentic AI solutions with the AstraZeneca Agent Mesh framework. The agents will leverage shared infrastructure, MCP (Model Context Protocol) servers, and centralized governance to deliver intelligent automation for the 3DP (Drug Development Data Platform) and BIKG (Biological Intelligence Knowledge Graph) platforms.

### 1.1 Agents Overview

| Agent | Phase | Primary Function | Target Platforms |
|-------|-------|------------------|------------------|
| Test Intelligence Agent | 1 | Automated test case generation | 3DP, BIKG |
| Dependency Coordinator | 2 | Cross-platform dependency tracking | 3DP, BIKG |
| Knowledge Library Companion | 3 | RAG-powered documentation Q&A | 3DP, BIKG |
| Auto-Lineage Agent | Enhancement | Automated data lineage tracking | 3DP, BIKG |

---

## 2. Agent Mesh Integration Architecture

### 2.1 Architecture Layers

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        AGENT MESH CONTROL PLANE                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Agent     │  │   Policy    │  │ Observability│  │   Secret    │        │
│  │  Registry   │  │   Engine    │  │     Hub     │  │  Manager    │        │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        AGENT RUNTIMES (ECS Fargate)                         │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐       │
│  │    Test      │ │  Dependency  │ │  Knowledge   │ │ Auto-Lineage │       │
│  │ Intelligence │ │ Coordinator  │ │   Library    │ │    Agent     │       │
│  │    Agent     │ │              │ │  Companion   │ │              │       │
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘       │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        MCP SERVERS (Tools Layer)                            │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐        │
│  │  3DP   │ │  BIKG  │ │  Jira/ │ │Confluence│ │  Data  │ │ GitHub │        │
│  │  MCP   │ │  MCP   │ │  ADO   │ │   MCP   │ │Catalog │ │  MCP   │        │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘ └────────┘        │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        AWS FOUNDATION SERVICES                              │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐        │
│  │Bedrock │ │Elasti- │ │Open-   │ │Key-    │ │  SQS   │ │   S3   │        │
│  │(Claude)│ │ Cache  │ │Search  │ │spaces  │ │        │ │        │        │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘ └────────┘        │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        TARGET PLATFORMS                                     │
│  ┌────────────────────────────┐  ┌────────────────────────────┐            │
│  │           3DP              │  │           BIKG             │            │
│  │  Drug Development Data     │  │  Biological Intelligence   │            │
│  │       Platform             │  │     Knowledge Graph        │            │
│  └────────────────────────────┘  └────────────────────────────┘            │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Agent Mesh Control Plane Components

| Component | Purpose | Integration Point |
|-----------|---------|-------------------|
| **Agent Registry** | Discovers and registers all R&D IT agents | `/registry/agents` API |
| **Policy Engine** | Enforces access control, rate limiting, GxP compliance | Policy evaluation on each tool call |
| **Observability Hub** | Metrics, distributed tracing, cost tracking | OpenTelemetry collectors |
| **Secret Manager** | Centralized credentials, API keys | AWS Secrets Manager integration |

---

## 3. Agent Specifications

### 3.1 Test Intelligence Agent

#### Overview
| Attribute | Value |
|-----------|-------|
| **Agent ID** | `rnd-it-test-intelligence` |
| **Phase** | 1 (Months 1-3) |
| **Primary LLM** | Claude 3.5 Sonnet / Claude 4 |
| **Runtime** | ECS Fargate (2 vCPU, 4GB RAM) |

#### Capabilities

| Capability | Description | 3DP Use Case | BIKG Use Case |
|------------|-------------|--------------|---------------|
| Test Generation | Generate test cases from code/requirements | Module 2/3 submission tests | KG query validation tests |
| Edge Case Discovery | Identify missing test scenarios | CDISC format edge cases | Ontology boundary cases |
| Coverage Analysis | Measure and improve test coverage | Regulatory compliance gaps | Query coverage gaps |
| Similar Failure Detection | Find related past failures | Past submission failures | Historical query failures |
| Compliance Validation | Ensure regulatory compliance | FDA 21 CFR Part 11 | Data integrity rules |

#### MCP Tools

| Tool Name | Purpose | API Endpoint |
|-----------|---------|--------------|
| `3dp-data-access` | Query 3DP data schemas and APIs | `mcp://3dp/data` |
| `code-scanner` | Analyze source code repositories | `mcp://github/repos` |
| `test-executor` | Run generated test cases | `mcp://testing/execute` |
| `confluence-reader` | Fetch requirements documentation | `mcp://confluence/pages` |
| `jira-writer` | Create defect tickets | `mcp://jira/issues` |

#### Data Flow

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│    Code     │    │   LLM       │    │   Test      │    │  Validation │
│  Analysis   │ -> │  Processing │ -> │ Generation  │ -> │  & Output   │
│             │    │  (Claude)   │    │             │    │             │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
      ▲                                                        │
      │              ┌─────────────┐                           │
      └──────────────│  Feedback   │<──────────────────────────┘
                     │    Loop     │
                     └─────────────┘
```

#### Output Artifacts

| Artifact | Format | Storage |
|----------|--------|---------|
| Test Cases | GxP-compliant JSON/YAML | S3 bucket |
| Coverage Reports | HTML/PDF | S3 + Confluence |
| Validation Evidence | PDF with audit trail | S3 (versioned) |
| Defect Predictions | JSON | Jira integration |

---

### 3.2 Dependency Coordinator

#### Overview
| Attribute | Value |
|-----------|-------|
| **Agent ID** | `rnd-it-dependency-coordinator` |
| **Phase** | 2 (Months 4-6) |
| **Primary LLM** | Claude 3.5 Sonnet |
| **Runtime** | ECS Fargate (2 vCPU, 4GB RAM) |

#### Capabilities

| Capability | Description | 3DP Use Case | BIKG Use Case |
|------------|-------------|--------------|---------------|
| Dependency Extraction | Parse dependencies from text/tickets | FDA timeline dependencies | Pipeline dependencies |
| Graph Visualization | Interactive dependency graphs | Submission module graph | Data flow graph |
| Conflict Detection | Identify scheduling conflicts | Cross-submission conflicts | Pipeline conflicts |
| Critical Path Analysis | Find bottlenecks and risks | Regulatory approval paths | Data freshness paths |
| Impact Assessment | What-if scenario analysis | Delay impact on submissions | Schema change impact |

#### MCP Tools

| Tool Name | Purpose | API Endpoint |
|-----------|---------|--------------|
| `jira-reader` | Read tickets and epics | `mcp://jira/search` |
| `ado-connector` | Azure DevOps integration | `mcp://ado/workitems` |
| `confluence-reader` | Roadmap documents | `mcp://confluence/pages` |
| `slack-notifier` | Send alerts and updates | `mcp://slack/messages` |
| `calendar-api` | Team capacity data | `mcp://calendar/events` |

#### Graph Model

```
Nodes:
  - Work Item (Jira ticket, ADO item)
  - Milestone (Release, Submission)
  - Resource (Team, Person)
  - Platform (3DP, BIKG)

Edges:
  - DEPENDS_ON (blocking dependency)
  - RELATED_TO (soft dependency)
  - ASSIGNED_TO (resource allocation)
  - PART_OF (hierarchy)
```

#### Storage

| Data Type | Storage | Purpose |
|-----------|---------|---------|
| Dependency Graph | Amazon Neptune | Graph queries, traversals |
| Real-time State | ElastiCache | Fast lookups |
| Historical Data | Keyspaces | Audit trail |
| Alerts | SNS/SQS | Notifications |

---

### 3.3 Knowledge Library Companion

#### Overview
| Attribute | Value |
|-----------|-------|
| **Agent ID** | `rnd-it-knowledge-library` |
| **Phase** | 3 (Months 7-9) |
| **Primary LLM** | Claude 3.5 Sonnet |
| **Embedding Model** | Titan Embeddings |
| **Runtime** | ECS Fargate (2 vCPU, 8GB RAM) |

#### Capabilities

| Capability | Description | 3DP Use Case | BIKG Use Case |
|------------|-------------|--------------|---------------|
| Semantic Search | Natural language document search | "Find Module 3 requirements" | "Find gene-disease docs" |
| Q&A Generation | Answer questions from docs | "How to prepare CTD?" | "What is UMLS?" |
| Multi-doc Synthesis | Combine info from multiple sources | Cross-reference SOPs | Cross-ontology answers |
| Citation Linking | Provide source references | Link to FDA guidance | Link to ontology docs |
| Document Summary | Condense long documents | Summarize guidance docs | Summarize pathway docs |

#### RAG Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     DOCUMENT INGESTION                          │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐      │
│  │Confluence│    │SharePoint│   │   PDF   │    │  APIs   │      │
│  └────┬────┘    └────┬────┘    └────┬────┘    └────┬────┘      │
│       └──────────────┴──────────────┴──────────────┘            │
│                              │                                   │
│                    ┌─────────▼─────────┐                        │
│                    │   Document Parser  │                        │
│                    │   (Textract/Custom)│                        │
│                    └─────────┬─────────┘                        │
│                              │                                   │
│                    ┌─────────▼─────────┐                        │
│                    │     Chunking      │                        │
│                    │  (512 tokens max) │                        │
│                    └─────────┬─────────┘                        │
│                              │                                   │
│                    ┌─────────▼─────────┐                        │
│                    │   Titan Embeddings │                        │
│                    └─────────┬─────────┘                        │
│                              │                                   │
│                    ┌─────────▼─────────┐                        │
│                    │   OpenSearch      │                        │
│                    │  (Vector Store)   │                        │
│                    └───────────────────┘                        │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                       QUERY FLOW                                │
│                              │                                   │
│                    ┌─────────▼─────────┐                        │
│                    │   User Question   │                        │
│                    └─────────┬─────────┘                        │
│                              │                                   │
│                    ┌─────────▼─────────┐                        │
│                    │ Query Embedding   │                        │
│                    └─────────┬─────────┘                        │
│                              │                                   │
│                    ┌─────────▼─────────┐                        │
│                    │  Semantic Search  │                        │
│                    │   (Top-K = 5)     │                        │
│                    └─────────┬─────────┘                        │
│                              │                                   │
│                    ┌─────────▼─────────┐                        │
│                    │  Claude (LLM)     │                        │
│                    │  Answer + Cite    │                        │
│                    └─────────┬─────────┘                        │
│                              │                                   │
│                    ┌─────────▼─────────┐                        │
│                    │   Response +      │                        │
│                    │   Source Links    │                        │
│                    └───────────────────┘                        │
└─────────────────────────────────────────────────────────────────┘
```

#### Document Sources

| Source | Content Type | Update Frequency |
|--------|--------------|------------------|
| Confluence | Platform docs, SOPs | On change |
| SharePoint | Regulatory guidance | Weekly |
| 3DP Docs | API documentation | On release |
| BIKG Ontologies | Ontology definitions | Monthly |
| FDA/EMA | Regulatory guidelines | Quarterly |

---

### 3.4 Auto-Lineage Agent

#### Overview
| Attribute | Value |
|-----------|-------|
| **Agent ID** | `rnd-it-auto-lineage` |
| **Phase** | Enhancement |
| **Primary LLM** | Claude 3.5 Sonnet |
| **Runtime** | ECS Fargate (4 vCPU, 8GB RAM) |

#### Capabilities

| Capability | Description | 3DP Use Case | BIKG Use Case |
|------------|-------------|--------------|---------------|
| Schema Discovery | Auto-detect database schemas | Clinical data schemas | KG entity schemas |
| Lineage Extraction | Parse SQL/ETL for lineage | Submission data flow | KG ingestion flow |
| Change Detection | Monitor schema changes | Alert on clinical schema changes | Alert on ontology changes |
| Impact Analysis | Assess downstream effects | "What breaks if X changes?" | "What queries fail?" |
| Documentation | Auto-generate lineage docs | Regulatory audit docs | Data dictionary updates |

#### Lineage Graph Model

```
┌─────────────────────────────────────────────────────────────────┐
│                     LINEAGE GRAPH                               │
│                                                                 │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐      │
│  │ Source  │───>│   ETL   │───>│  Target │───>│  Report │      │
│  │ Table   │    │ Process │    │  Table  │    │   View  │      │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘      │
│       │              │              │              │             │
│       ▼              ▼              ▼              ▼             │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐      │
│  │ Column  │    │Transform│    │ Column  │    │ Column  │      │
│  │  A, B   │    │  Rules  │    │  X, Y   │    │  P, Q   │      │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘      │
│                                                                 │
│  Edge Types: DERIVES_FROM, TRANSFORMS_TO, AGGREGATES, JOINS    │
└─────────────────────────────────────────────────────────────────┘
```

#### MCP Tools

| Tool Name | Purpose | API Endpoint |
|-----------|---------|--------------|
| `data-catalog` | Metadata repository | `mcp://glue/catalog` |
| `schema-registry` | Schema definitions | `mcp://schema/registry` |
| `dbt-metadata` | dbt model lineage | `mcp://dbt/metadata` |
| `db-introspector` | Database schema queries | `mcp://db/introspect` |
| `notifier` | Alert on changes | `mcp://slack/messages` |

---

## 4. Shared Infrastructure

### 4.1 AWS Services

| Service | Purpose | Configuration |
|---------|---------|---------------|
| **Amazon Bedrock** | LLM API (Claude) | On-demand, model: `anthropic.claude-3-5-sonnet` |
| **Titan Embeddings** | Vector embeddings | Model: `amazon.titan-embed-text-v1` |
| **OpenSearch Serverless** | Vector store | Index: `rnd-it-vectors`, dimension: 1536 |
| **Amazon Neptune** | Graph database | Instance: `db.r5.large`, serverless |
| **ElastiCache** | Session cache | Redis 7.x, 2 nodes |
| **Amazon Keyspaces** | Conversation history | Cassandra-compatible |
| **Amazon SQS** | Async task queue | Standard queue, DLQ enabled |
| **Amazon S3** | Document/artifact store | Versioning enabled, lifecycle rules |
| **AWS Secrets Manager** | Credentials | Auto-rotation enabled |

### 4.2 Compute Configuration

| Agent | vCPU | Memory | Min Tasks | Max Tasks | Auto-scaling |
|-------|------|--------|-----------|-----------|--------------|
| Test Intelligence | 2 | 4 GB | 1 | 5 | CPU > 70% |
| Dependency Coordinator | 2 | 4 GB | 1 | 3 | CPU > 70% |
| Knowledge Library | 2 | 8 GB | 1 | 5 | Request count |
| Auto-Lineage | 4 | 8 GB | 1 | 3 | Event-driven |

### 4.3 Networking

```
┌─────────────────────────────────────────────────────────────────┐
│                         VPC (10.0.0.0/16)                       │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                Private Subnets (Agents)                 │    │
│  │  10.0.1.0/24  │  10.0.2.0/24  │  10.0.3.0/24           │    │
│  │     AZ-a      │     AZ-b      │     AZ-c               │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                   │
│                    ┌─────────▼─────────┐                        │
│                    │  NAT Gateway      │                        │
│                    │  (Outbound only)  │                        │
│                    └───────────────────┘                        │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              Private Subnets (Data)                     │    │
│  │  10.0.10.0/24 │  10.0.11.0/24 │  10.0.12.0/24          │    │
│  │  OpenSearch   │   Neptune     │   ElastiCache          │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                 VPC Endpoints                           │    │
│  │  Bedrock │ S3 │ Secrets Manager │ SQS │ CloudWatch     │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. Security & Compliance

### 5.1 Authentication & Authorization

| Layer | Mechanism | Details |
|-------|-----------|---------|
| User Auth | SSO (Okta/ADFS) | SAML 2.0, MFA required |
| Service Auth | IAM Roles | ECS task roles, least privilege |
| API Auth | API Gateway + JWT | Token validation, expiry |
| Agent Auth | mTLS | Certificate-based between agents |

### 5.2 Data Classification

| Classification | Examples | Handling |
|----------------|----------|----------|
| PHI | Patient data, clinical records | Never processed by agents |
| PII | User identifiers, emails | Masked/tokenized |
| Confidential | Business data, roadmaps | Encrypted at rest/transit |
| Internal | Documentation, SOPs | Standard protection |

### 5.3 Compliance Requirements

| Requirement | Implementation |
|-------------|----------------|
| FDA 21 CFR Part 11 | Audit trails, electronic signatures |
| GxP | Validated workflows, change control |
| SOC 2 Type II | AWS compliance, custom controls |
| GDPR | Data minimization, retention policies |

### 5.4 Audit Logging

```json
{
  "event_id": "uuid",
  "timestamp": "ISO8601",
  "agent_id": "rnd-it-test-intelligence",
  "user_id": "user@astrazeneca.com",
  "action": "test_generation",
  "resource": "3dp/module-3/validation",
  "input_hash": "sha256",
  "output_hash": "sha256",
  "duration_ms": 2340,
  "cost_usd": 0.012,
  "status": "success"
}
```

---

## 6. Observability

### 6.1 Metrics

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| `agent.request.count` | Total requests per agent | N/A |
| `agent.request.latency_p99` | 99th percentile latency | > 10s |
| `agent.error.rate` | Error rate percentage | > 5% |
| `llm.token.count` | Tokens consumed (input+output) | N/A |
| `llm.cost.usd` | LLM API cost | > $100/day |
| `cache.hit.rate` | Cache hit percentage | < 50% |

### 6.2 Tracing

All agent requests are traced using OpenTelemetry:

```
Trace ID: abc123
├── Span: agent.request
│   ├── Span: mcp.tool.call (3dp-data-access)
│   ├── Span: llm.completion (bedrock.claude)
│   ├── Span: vector.search (opensearch)
│   └── Span: response.format
```

### 6.3 Dashboards

| Dashboard | Purpose | Audience |
|-----------|---------|----------|
| Agent Overview | Health, traffic, errors | Operations |
| Cost Tracking | LLM costs, compute costs | Finance/PM |
| User Activity | Usage patterns, top queries | Product |
| Compliance | Audit logs, policy violations | Security |

---

## 7. Deployment

### 7.1 CI/CD Pipeline

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│  Code   │───>│  Build  │───>│  Test   │───>│ Security│───>│ Deploy  │
│  Push   │    │ (Docker)│    │ (pytest)│    │  Scan   │    │  (ECS)  │
└─────────┘    └─────────┘    └─────────┘    └─────────┘    └─────────┘
     │              │              │              │              │
     ▼              ▼              ▼              ▼              ▼
  GitHub       ECR Image       Coverage       Snyk/SonarQ    Blue/Green
  Actions                        >80%          No Critical   Deployment
```

### 7.2 Infrastructure as Code

| Component | IaC Tool | Repository |
|-----------|----------|------------|
| AWS Resources | CDK (TypeScript) | `rnd-it-agents-infra` |
| Agent Configs | Terraform | `rnd-it-agents-config` |
| Kubernetes | Helm Charts | `rnd-it-agents-helm` |

### 7.3 Environment Strategy

| Environment | Purpose | Data |
|-------------|---------|------|
| Dev | Development, testing | Synthetic |
| QA | Integration testing | Anonymized |
| Staging | Pre-production validation | Anonymized |
| Production | Live system | Production (no PHI) |

---

## 8. Cost Estimates

### 8.1 Monthly Cost Breakdown

| Component | Estimated Cost | Notes |
|-----------|----------------|-------|
| Amazon Bedrock (Claude) | $4,500 | Based on 5M tokens/month |
| Titan Embeddings | $800 | Based on 10M tokens/month |
| ECS Fargate | $1,200 | 4 agents, avg 2 tasks each |
| OpenSearch Serverless | $600 | 2 OCU |
| Amazon Neptune | $400 | Serverless, burst |
| ElastiCache | $300 | 2-node Redis |
| S3 + other | $200 | Storage, transfer |
| **Total** | **$8,000** | |

### 8.2 Cost Optimization

| Strategy | Potential Savings |
|----------|-------------------|
| Response caching | 20-30% LLM costs |
| Prompt optimization | 10-15% token usage |
| Auto-scaling | 15-20% compute |
| Reserved capacity | 30% Neptune/ElastiCache |

---

## 9. Appendix

### 9.1 Glossary

| Term | Definition |
|------|------------|
| **MCP** | Model Context Protocol - standard for agent-tool communication |
| **RAG** | Retrieval-Augmented Generation |
| **3DP** | Drug Development Data Platform |
| **BIKG** | Biological Intelligence Knowledge Graph |
| **GxP** | Good Practice regulations (GMP, GLP, GCP) |
| **CTD** | Common Technical Document (regulatory submission format) |

### 9.2 References

- AstraZeneca Agent Mesh Solution Blueprint
- AWS Well-Architected Framework
- FDA 21 CFR Part 11 Guidance
- MCP Specification v1.0

### 9.3 Change Log

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | Feb 2026 | R&D IT Team | Initial draft |

---

*Document Status: Draft - Pending Architecture Review*

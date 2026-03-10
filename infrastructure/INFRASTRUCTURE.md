# MIA Infrastructure — Terraform Documentation

## Overview

This Terraform project provisions the complete AWS infrastructure for the **Manufacturing Insight Agent (MIA)** — an AI-powered conversational platform built with LangGraph, FastAPI, and React. The infrastructure supports real-time agent interactions, semantic search via RAG, and multi-environment deployment.

---

## Architecture Diagram

```
                            ┌─────────────────────────────────────────────────────────────┐
                            │                        AWS Cloud                            │
                            │                                                             │
    Users ──── HTTPS ──────▶│  ┌─────────────────────────────────────┐                    │
                            │  │          Public Subnets              │                    │
                            │  │  ┌─────────────────────────────┐    │                    │
                            │  │  │   Application Load Balancer  │    │                    │
                            │  │  │                               │    │                    │
                            │  │  │  / ──────▶ Frontend TG        │    │                    │
                            │  │  │  /api/* ──▶ Backend TG        │    │                    │
                            │  │  │  /agents/*▶ Agents TG         │    │                    │
                            │  │  └─────────────────────────────┘    │                    │
                            │  └──────────────────┬──────────────────┘                    │
                            │                     │                                       │
                            │  ┌──────────────────▼──────────────────┐                    │
                            │  │          Private Subnets             │                    │
                            │  │                                      │                    │
                            │  │  ┌──────────┐ ┌──────────┐ ┌──────────┐                 │
                            │  │  │ Frontend │ │ Backend  │ │  Agents  │  ECS Fargate     │
                            │  │  │ React/   │ │ FastAPI  │ │ LangGraph│                  │
                            │  │  │ Nginx    │ │ + WS     │ │ Service  │                  │
                            │  │  │ 0.5vCPU  │ │ 1 vCPU   │ │ 2 vCPU   │                 │
                            │  │  │ 1 GB     │ │ 2 GB     │ │ 4 GB     │                 │
                            │  │  └──────────┘ └────┬─────┘ └────┬─────┘                 │
                            │  │                     │            │                       │
                            │  │         ┌───────────┴────────────┘                       │
                            │  │         │                                                │
                            │  │    ┌────▼─────┐  ┌──────────┐  ┌────────────┐           │
                            │  │    │ DynamoDB  │  │    S3    │  │ OpenSearch │           │
                            │  │    │ Sessions  │  │   KB     │  │  Vector   │           │
                            │  │    │ + Turns   │  │  Docs    │  │  Search   │           │
                            │  │    └──────────┘  └──────────┘  └────────────┘           │
                            │  │                                                          │
                            │  │    ┌──────────────┐  ┌─────────────────┐                │
                            │  │    │   Bedrock     │  │ Secrets Manager │                │
                            │  │    │ Claude + Cohere│ │ API Keys, Creds│                │
                            │  │    └──────────────┘  └─────────────────┘                │
                            │  └──────────────────────────────────────────┘                │
                            │                                                             │
                            │  ┌──────────────────┐  ┌──────────────────┐                │
                            │  │  API Gateway WS   │  │   CloudWatch     │                │
                            │  │  Real-time Stream  │  │  Logs + Alarms   │                │
                            │  └──────────────────┘  └──────────────────┘                │
                            └─────────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
infrastructure/
├── modules/                    # 13 reusable Terraform modules
│   ├── vpc/                    # Network foundation
│   ├── security-groups/        # Firewall rules
│   ├── iam/                    # Roles and policies
│   ├── ecr/                    # Container image registries
│   ├── s3/                     # Object storage
│   ├── dynamodb/               # NoSQL database tables
│   ├── secrets-manager/        # Secret storage
│   ├── opensearch/             # Search engine
│   ├── cloudwatch/             # Monitoring and logging
│   ├── alb/                    # Load balancer
│   ├── ecs-cluster/            # Container orchestration cluster
│   ├── ecs-service/            # Container service definitions
│   └── api-gateway/            # WebSocket API
├── environments/               # Per-environment configurations
│   ├── dev/                    # Development environment
│   ├── preprod/                # Pre-production environment
│   └── prod/                   # Production environment
└── global/
    └── state-bucket/           # Bootstrap: Terraform state storage
```

---

## Module-by-Module Detailed Explanation

---

### 1. VPC (Virtual Private Cloud) — `modules/vpc/`

**Purpose:** Creates the isolated network foundation for the entire infrastructure. All AWS resources live inside this VPC, providing network-level security and traffic control.

**What it creates:**

| Resource | Description |
|----------|-------------|
| **VPC** | The top-level virtual network with a configurable CIDR block (e.g., `10.0.0.0/16` = 65,536 IP addresses). DNS hostnames and DNS resolution are enabled so services can discover each other. |
| **Internet Gateway (IGW)** | Attaches to the VPC and allows resources in public subnets to communicate with the internet. Without this, nothing inside the VPC can reach the outside world. |
| **Public Subnets** | One per availability zone. These host the ALB (load balancer) which needs to be internet-facing. Each subnet gets a `/24` CIDR (256 IPs) carved from the VPC CIDR using the `cidrsubnet` function. Resources here receive public IPs automatically. |
| **Private Subnets** | One per availability zone. These host all ECS Fargate containers (frontend, backend, agents) and OpenSearch. Resources here have NO public IP and can only reach the internet through a NAT Gateway. This is a critical security boundary — application containers are never directly exposed. |
| **NAT Gateway(s)** | Allows private subnet resources to make outbound internet calls (e.g., calling Bedrock API, pulling Docker images) without being directly accessible from the internet. In dev, a single NAT Gateway is used to save cost (~$32/month each). In prod, one per AZ for high availability — if one AZ fails, containers in other AZs still have outbound connectivity. Each NAT Gateway requires an Elastic IP. |
| **Route Tables** | Public route table: routes `0.0.0.0/0` to the Internet Gateway. Private route tables (one per AZ): route `0.0.0.0/0` to the corresponding NAT Gateway. These tables define how traffic flows within and out of the VPC. |
| **VPC Flow Logs** | Captures all network traffic metadata (source IP, destination IP, port, protocol, accept/reject) and sends it to CloudWatch Logs. Essential for security auditing — you can investigate suspicious traffic, diagnose connectivity issues, and meet compliance requirements. Aggregated every 60 seconds. |
| **VPC Endpoints (Gateway)** | Creates free endpoints for S3 and DynamoDB. Instead of traffic to these services going out through the NAT Gateway (which costs money per GB), it stays on Amazon's private network. This saves significant cost and reduces latency. Gateway endpoints are added to route tables so all private subnets benefit automatically. |

**Why this matters:**
The VPC is the security perimeter. By separating public subnets (ALB only) from private subnets (all application and data services), we ensure that no container or database is directly accessible from the internet. All inbound traffic must pass through the ALB, which enforces routing rules and health checks.

**Environment differences:**

| Setting | Dev | Pre-Prod | Prod |
|---------|-----|----------|------|
| CIDR | `10.0.0.0/16` | `10.1.0.0/16` | `10.2.0.0/16` |
| AZs | 2 | 3 | 3 |
| NAT Gateways | 1 (shared) | 1 (shared) | 3 (one per AZ) |

---

### 2. Security Groups — `modules/security-groups/`

**Purpose:** Acts as virtual firewalls controlling inbound and outbound traffic for each tier of the application. Security groups operate at the network interface level — every packet is evaluated against these rules.

**What it creates:**

| Security Group | Inbound Rules | Outbound Rules |
|----------------|---------------|----------------|
| **ALB SG** | Port 80 (HTTP) and 443 (HTTPS) from `0.0.0.0/0` — the only resource accepting internet traffic | Allows traffic only to the ECS Services SG (ports 0-65535 TCP) |
| **ECS Services SG** | Allows traffic only from the ALB SG (not from the internet). Also allows internal service-to-service traffic (e.g., backend calling agents) via self-referencing rule | Allows all outbound (`0.0.0.0/0`) — needed for NAT Gateway access to Bedrock, external APIs, ECR image pulls |
| **OpenSearch SG** | Allows HTTPS (port 443) only from the ECS Services SG — only application containers can query OpenSearch | Allows all outbound |

**Key security principles applied:**
- **Default deny**: Security groups deny all traffic by default. Only explicitly allowed traffic passes.
- **Reference by security group ID, not CIDR**: Instead of saying "allow from 10.0.0.0/16", rules reference other security groups. This means if IP ranges change, rules remain valid.
- **`create_before_destroy` lifecycle**: When Terraform needs to update a security group, it creates the new one before destroying the old one, preventing momentary connectivity loss.
- **No `0.0.0.0/0` ingress on application tier**: Only the ALB accepts internet traffic. Application containers are completely shielded.

---

### 3. IAM (Identity and Access Management) — `modules/iam/`

**Purpose:** Defines WHO (which service) can do WHAT (which API actions) on WHICH resources. IAM is the authorization backbone — without the correct roles and policies, ECS tasks cannot access DynamoDB, S3, Bedrock, or any other AWS service.

**What it creates:**

#### ECS Task Execution Role
This role is used by the **ECS agent itself** (not your application code). It needs permissions to:
- Pull Docker images from ECR
- Write container logs to CloudWatch
- Fetch secrets from Secrets Manager at container startup (for injecting env vars)

This role gets the AWS-managed `AmazonECSTaskExecutionRolePolicy` plus a custom policy scoped to secrets under the project prefix.

#### ECS Task Role
This role is assumed by **your running application containers**. It has separate, scoped policies for each AWS service:

| Policy | Actions Allowed | Resource Scope |
|--------|----------------|----------------|
| **DynamoDB** | PutItem, GetItem, UpdateItem, DeleteItem, Query, Scan, BatchGet, BatchWrite | Only tables prefixed with `{project}-{env}-*` and their indexes |
| **S3** | GetObject, PutObject, ListBucket, DeleteObject | Only buckets prefixed with `{project}-{env}-*` |
| **Bedrock** | InvokeModel, InvokeModelWithResponseStream, ListFoundationModels, GetFoundationModel | Only Anthropic Claude and Cohere embedding models |
| **OpenSearch** | ESHttpGet, ESHttpPost, ESHttpPut, ESHttpDelete | Only domains prefixed with `{project}-{env}-*` |
| **Secrets Manager** | GetSecretValue, DescribeSecret | Only secrets under `{project}-{env}/*` path |
| **CloudWatch Logs** | CreateLogStream, PutLogEvents | Only log groups under `/ecs/{project}-{env}/*` |

**Why least privilege matters:**
If an agent container is compromised, the attacker can only access resources scoped to that environment's prefix. They cannot access prod data from a dev container, cannot delete DynamoDB tables (no `DeleteTable` permission), and cannot access secrets from other projects.

---

### 4. ECR (Elastic Container Registry) — `modules/ecr/`

**Purpose:** Private Docker image registry that stores the container images for all three application services. ECS Fargate pulls images from here at deployment time.

**What it creates:**

| Resource | Details |
|----------|---------|
| **3 ECR Repositories** | `{prefix}-frontend`, `{prefix}-backend`, `{prefix}-agents` |
| **Image Scanning** | Scan-on-push enabled — every pushed image is automatically scanned for known CVEs (vulnerabilities) using Amazon's vulnerability database. Results appear in the ECR console. |
| **Image Tag Immutability** | Set to `IMMUTABLE` — once a tag (e.g., `v1.2.3`) is pushed, it cannot be overwritten. This prevents accidental or malicious replacement of production images. Use unique tags per deployment. |
| **Lifecycle Policy** | Automatically expires images when count exceeds the retention limit (default: 10). Prevents unbounded storage growth. Old images are garbage-collected. |
| **Encryption** | AES-256 encryption at rest for all stored images. |

**CI/CD integration:**
Your CI/CD pipeline will:
1. Build the Docker image
2. Tag it with the git SHA or version
3. Authenticate: `aws ecr get-login-password | docker login`
4. Push: `docker push {repo-url}:{tag}`
5. Update the ECS service to use the new image tag

---

### 5. S3 (Simple Storage Service) — `modules/s3/`

**Purpose:** Stores the Knowledge Base content for the RAG (Retrieval-Augmented Generation) pipeline. This includes raw documents, prompt templates, embedding artifacts, and unstructured content that the agents index and search.

**What it creates:**

| Resource | Details |
|----------|---------|
| **S3 Bucket** | Named `{prefix}-knowledge-base`. This is the canonical store for all KB data. |
| **Versioning** | Enabled — every overwrite creates a new version. You can recover accidentally deleted or overwritten documents. Critical for a knowledge base where content changes are frequent. |
| **KMS Encryption** | Server-side encryption using AWS KMS (Key Management Service). All objects are encrypted at rest automatically. Bucket key is enabled to reduce KMS API call costs. |
| **Public Access Block** | All four public access block settings are enabled — `block_public_acls`, `block_public_policy`, `ignore_public_acls`, `restrict_public_buckets`. It is impossible to accidentally make this bucket public. |
| **TLS Enforcement** | A bucket policy explicitly denies any S3 API call made over plain HTTP (non-TLS). All access must use HTTPS. |
| **Lifecycle Rules** | After 90 days, objects transition to S3 Standard-IA (Infrequent Access) storage class, which is ~45% cheaper. Non-current versions (from versioning) expire after 30 days. |
| **`prevent_destroy`** | Terraform will refuse to delete this bucket, even with `terraform destroy`. Must be explicitly removed from the lifecycle block first. Protects against accidental data loss. |

---

### 6. DynamoDB — `modules/dynamodb/`

**Purpose:** Provides two NoSQL database tables that store conversation state. DynamoDB is chosen for its single-digit millisecond latency, serverless scaling, and native TTL (Time-To-Live) support.

**What it creates:**

#### Table 1: `{prefix}-mia-session-turns`
Stores individual conversation turns (user messages and agent responses).

| Attribute | Type | Role |
|-----------|------|------|
| `session_id` | String | Partition key — groups all turns belonging to one conversation |
| `turn_id` | String | Sort key — orders turns chronologically within a session |
| `ttl` | Number | TTL attribute — DynamoDB automatically deletes expired items |

#### Table 2: `{prefix}-mia-chat-sessions`
Stores session metadata — which user owns which session, session creation time, status.

| Attribute | Type | Role |
|-----------|------|------|
| `user_id` | String | Partition key — groups all sessions for a user |
| `session_id` | String | Sort key — identifies individual sessions |
| `ttl` | Number | TTL attribute |

**Common settings for both tables:**
- **Billing Mode: PAY_PER_REQUEST** — No capacity planning needed. You pay per read/write request. Ideal for unpredictable workloads. Scales automatically from 0 to millions of requests.
- **TTL Enabled** — Items with an expired `ttl` attribute are automatically deleted within 48 hours at no cost. Keeps the tables clean without manual purging.
- **Point-in-Time Recovery (PITR)** — Enabled in preprod/prod. Allows you to restore the table to any second within the last 35 days. Essential for disaster recovery. Disabled in dev to save cost.
- **Server-Side Encryption** — Enabled using AWS-owned keys (free).
- **`prevent_destroy`** — Terraform will refuse to delete these tables.

---

### 7. Secrets Manager — `modules/secrets-manager/`

**Purpose:** Securely stores sensitive credentials that application containers need at runtime. Secrets are encrypted at rest with AWS KMS and can be rotated without redeploying the application.

**What it creates:**

| Secret | Purpose |
|--------|---------|
| `{prefix}/azure-ad-client-secret` | Azure Active Directory client secret for user authentication |
| `{prefix}/langsmith-api-key` | LangSmith API key for LLM observability and tracing |
| `{prefix}/snowflake-connection-string` | Snowflake data warehouse connection credentials |

**How secrets reach the containers:**
1. **At startup (ECS execution role):** Secrets can be injected as environment variables directly into the container by referencing the secret ARN in the task definition. ECS pulls the value from Secrets Manager before the container starts.
2. **At runtime (ECS task role):** Application code can call the Secrets Manager API directly using `GetSecretValue`.

**Placeholder values:** Secrets are created with `{"placeholder": "UPDATE_ME"}` as the initial value. The `ignore_changes` lifecycle rule ensures Terraform doesn't overwrite the value once you've set the real secret manually or via CI/CD.

**Recovery window:** Secrets have a 7-day recovery window. If deleted, they enter a "pending deletion" state for 7 days before permanent removal, allowing recovery from accidental deletion.

---

### 8. OpenSearch — `modules/opensearch/`

**Purpose:** Amazon OpenSearch Service provides the vector search and full-text search capabilities for the RAG (Retrieval-Augmented Generation) pipeline. The agents use OpenSearch to find relevant documents by converting queries into embeddings and performing similarity search.

**What it creates:**

| Resource | Details |
|----------|---------|
| **OpenSearch Domain** | A managed Elasticsearch-compatible search cluster. Engine version: OpenSearch 2.11. |
| **Cluster Configuration** | Configurable instance type and count. Zone awareness is automatically enabled when `instance_count > 1`, distributing data across AZs for fault tolerance. |
| **EBS Storage** | GP3 volumes attached to each node (default: 100 GB per node, 125 MiB/s throughput, 3000 IOPS). GP3 provides consistent performance regardless of volume size. |
| **Encryption at Rest** | All data stored on disk is encrypted using AWS KMS. |
| **Node-to-Node Encryption** | All traffic between OpenSearch nodes within the cluster is encrypted using TLS. |
| **HTTPS Enforcement** | The domain endpoint only accepts HTTPS connections with TLS 1.2 minimum. No plaintext HTTP. |
| **VPC Placement** | The domain is placed in private subnets with the OpenSearch security group. It is NOT publicly accessible — only ECS containers can reach it. |
| **Access Policy** | Allows all actions from within the VPC. Fine-grained access control is handled by the security group (only ECS SG can reach port 443). |
| **Slow Query Logs** | Index slow logs and search slow logs are published to CloudWatch for performance debugging. A log resource policy grants OpenSearch permission to write to the log group. |
| **`prevent_destroy`** | Terraform will refuse to delete the OpenSearch domain. Rebuilding an OpenSearch cluster with re-indexed data can take hours. |

**Environment differences:**

| Setting | Dev | Pre-Prod | Prod |
|---------|-----|----------|------|
| Instance Type | `t3.small.search` | `t3.medium.search` | `r6g.large.search` |
| Instance Count | 1 (no zone awareness) | 2 (zone-aware) | 2 (zone-aware) |
| EBS Volume | 50 GB | 100 GB | 100 GB |

---

### 9. CloudWatch — `modules/cloudwatch/`

**Purpose:** Centralized monitoring and logging for all application services. CloudWatch collects container logs, tracks resource utilization metrics, and triggers alarms when thresholds are breached.

**What it creates:**

#### Log Groups
One CloudWatch Log Group per ECS service:
- `/ecs/{prefix}/frontend` — Nginx access/error logs
- `/ecs/{prefix}/backend` — FastAPI application logs, request traces
- `/ecs/{prefix}/agents` — LangGraph agent execution logs, LLM call traces

Plus an ALB log group: `/aws/alb/{prefix}`

Log retention is environment-specific: 7 days (dev), 30 days (preprod), 90 days (prod).

#### CPU Alarms
One alarm per ECS service. Triggers when **average CPU utilization exceeds 80%** for 3 consecutive 5-minute periods (15 minutes sustained). This indicates the service needs more tasks (horizontal scaling) or larger tasks (vertical scaling).

#### Memory Alarms
One alarm per ECS service. Triggers when **average memory utilization exceeds 85%** for 3 consecutive 5-minute periods. Memory exhaustion causes OOM kills and container restarts.

**How container logs work:**
Each ECS task definition configures the `awslogs` log driver. The container's stdout/stderr is automatically captured and streamed to the corresponding CloudWatch Log Group. The stream prefix includes the service name, making it easy to filter logs per container instance.

---

### 10. ALB (Application Load Balancer) — `modules/alb/`

**Purpose:** The single entry point for all user traffic. The ALB receives HTTP requests and routes them to the correct ECS service based on the URL path. It also performs health checks to ensure traffic only goes to healthy containers.

**What it creates:**

| Resource | Details |
|----------|---------|
| **Application Load Balancer** | Internet-facing, placed in public subnets. Protected by the ALB security group (ports 80/443 only). |
| **Frontend Target Group** | Routes to frontend containers on port 80. Health check: `GET /` expecting HTTP 200. |
| **Backend Target Group** | Routes to backend containers on port 8000. Health check: `GET /health` expecting HTTP 200. |
| **Agents Target Group** | Routes to agent containers on port 8001. Health check: `GET /health` expecting HTTP 200. Deregistration delay set to 120 seconds (longer than default 300s) to allow in-flight agent requests to complete during deployments. |
| **HTTP Listener** | Listens on port 80. Default action forwards to the frontend target group. When you add an ACM certificate later, add an HTTPS listener on port 443 and redirect HTTP to HTTPS. |
| **Path-Based Routing Rules** | Priority 100: `/api/*` → Backend TG. Priority 200: `/agents/*` → Agents TG. Everything else (`/*`) → Frontend TG (default action). |

**How path-based routing works:**
```
User Request                    → Routed To
─────────────────────────────────────────────
GET /                           → Frontend (React SPA)
GET /dashboard                  → Frontend (React SPA)
POST /api/chat                  → Backend (FastAPI)
GET /api/sessions               → Backend (FastAPI)
POST /agents/invoke             → Agents (LangGraph)
GET /agents/health              → Agents (LangGraph)
```

**Target type: `ip`** — Required for Fargate. Unlike EC2 targets (instance IDs), Fargate tasks register by their private IP address in the VPC.

**Deletion protection:** Enabled in prod to prevent accidental deletion via Terraform or AWS console.

---

### 11. ECS Cluster — `modules/ecs-cluster/`

**Purpose:** The logical grouping of all ECS services and tasks. The cluster itself doesn't run anything — it's a namespace that organizes your Fargate services.

**What it creates:**

| Resource | Details |
|----------|---------|
| **ECS Cluster** | Named `{prefix}-cluster`. Container Insights can be enabled/disabled per environment. |
| **Capacity Providers** | Registers both `FARGATE` (on-demand, guaranteed) and `FARGATE_SPOT` (up to 70% cheaper, can be interrupted). Default strategy uses `FARGATE` with a base of 1 — ensuring at least one task is always on-demand. |
| **ECS Exec Log Group** | CloudWatch log group for ECS Exec sessions (`/ecs/{prefix}/exec`). ECS Exec lets developers SSH into running containers for debugging — enabled in dev only. |

**Container Insights** (enabled in preprod/prod):
Collects and aggregates container-level metrics: CPU, memory, network, disk I/O per task and per service. Provides dashboards in CloudWatch showing resource utilization trends, which is essential for capacity planning.

---

### 12. ECS Service — `modules/ecs-service/` (Reusable)

**Purpose:** This is the core compute module, used three times — once for each service (frontend, backend, agents). It defines HOW containers run: what image, how much CPU/memory, how many instances, networking, health checks, auto-scaling, and deployment strategy.

**What it creates per service:**

#### Task Definition
The blueprint for running a container:

| Setting | Details |
|---------|---------|
| Network Mode | `awsvpc` — each task gets its own ENI (Elastic Network Interface) with a private IP in the VPC. Required for Fargate. |
| CPU / Memory | Configurable per service. Fargate has fixed valid combinations (e.g., 512 CPU / 1024 MB, 1024 CPU / 2048 MB, 2048 CPU / 4096 MB). |
| Container Image | Pulled from the ECR repository URL. |
| Port Mappings | One port per container, mapped to the target group. |
| Environment Variables | Injected as plain text: table names, bucket names, OpenSearch endpoint, Bedrock model IDs, etc. |
| Secrets | Injected from Secrets Manager ARNs at startup by the ECS agent. The secret value is decrypted and set as an env var. The container never sees the ARN — it sees the actual secret value. |
| Log Configuration | `awslogs` driver pointing to the service's CloudWatch log group. |
| Health Check | Container-level health check command (e.g., `curl -f http://localhost:8000/health`). If the health check fails, ECS replaces the task. |

#### ECS Service
The long-running service definition:

| Setting | Details |
|---------|---------|
| Launch Type | `FARGATE` — fully serverless, no EC2 instances to manage. |
| Desired Count | Number of tasks to keep running (configurable per environment). |
| Network Config | Tasks placed in private subnets with the ECS security group. No public IP assigned. |
| Load Balancer | Registered with the corresponding ALB target group. The ALB health check determines if a task is healthy for receiving traffic. |
| Deployment Config | `maximum_percent: 200%` and `minimum_healthy_percent: 100%` — during deployments, ECS launches new tasks (up to 2x desired count) before draining old ones. Zero-downtime rolling deployments. |
| Circuit Breaker | Enabled with rollback. If new tasks fail to stabilize (health checks fail repeatedly), ECS automatically rolls back to the previous task definition. Prevents bad deployments from taking down the service. |
| ECS Exec | Enabled in dev for debugging. Allows `aws ecs execute-command` to open a shell inside a running container. |
| `ignore_changes: [desired_count]` | Terraform ignores changes to desired_count after initial creation. This prevents Terraform from fighting with auto-scaling — if auto-scaling increased tasks to 6, Terraform won't reset it back to 4 on the next apply. |

#### Auto Scaling (enabled in preprod/prod)

| Setting | Details |
|---------|---------|
| Target Tracking: CPU | If average CPU across all tasks exceeds 70%, add more tasks. If it drops below, scale in. Scale-out cooldown: 60 seconds (react quickly to load). Scale-in cooldown: 300 seconds (avoid flapping). |
| Target Tracking: Memory | Same pattern for memory at 80% threshold. |
| Min / Max Capacity | Min = desired_count, Max = desired_count × 3. |

**Service sizing per environment:**

| Service | Dev | Pre-Prod | Prod |
|---------|-----|----------|------|
| **Frontend** | 1 × (0.5 vCPU, 1 GB) | 2 × (0.5 vCPU, 1 GB) | 2 × (0.5 vCPU, 1 GB) |
| **Backend** | 1 × (1 vCPU, 2 GB) | 2 × (1 vCPU, 2 GB) | 4 × (1 vCPU, 2 GB) |
| **Agents** | 1 × (2 vCPU, 4 GB) | 2 × (2 vCPU, 4 GB) | 4 × (2 vCPU, 4 GB) |

---

### 13. API Gateway (WebSocket) — `modules/api-gateway/`

**Purpose:** Manages persistent WebSocket connections between the frontend and backend for real-time streaming of agent responses. When a user asks a question, the agent's response is streamed token-by-token via Server-Sent Events (SSE) through this WebSocket connection.

**What it creates:**

| Resource | Details |
|----------|---------|
| **WebSocket API** | Protocol type `WEBSOCKET` with route selection expression `$request.body.action`. This lets API Gateway route different message types to different integrations. |
| **HTTP Proxy Integration** | Routes WebSocket messages to the backend ECS service via the ALB at `/ws` endpoint. |
| **Routes** | `$connect` (new connection), `$disconnect` (closed connection), `$default` (catch-all), `sendMessage` (user sends a message). All route to the backend integration. |
| **Stage** | Auto-deployed stage (named by environment). Includes throttling settings (burst: 500, rate: 1000 req/sec) to protect the backend from overwhelming traffic. |
| **Access Logging** | Every WebSocket event is logged to CloudWatch with request ID, source IP, event type, route key, status, and connection ID. Essential for debugging connection issues. |

**Connection flow:**
1. Frontend opens WebSocket: `wss://{api-id}.execute-api.{region}.amazonaws.com/{stage}`
2. API Gateway establishes the connection (`$connect` route)
3. Frontend sends a message (routed via `sendMessage`)
4. Backend processes the request, invokes LangGraph agents
5. Agent responses stream back through the WebSocket connection
6. Frontend renders tokens in real-time

---

### 14. Global State Bucket — `global/state-bucket/`

**Purpose:** Bootstrap resource that creates the S3 bucket used to store Terraform state files for all environments. This must be deployed FIRST before any other environment.

**Why it's separate:**
This is a chicken-and-egg problem — you need an S3 bucket to store state, but the bucket itself is managed by Terraform. The solution: this module uses **local state** (stored on your machine). Once the bucket exists, all other environments use it as their remote backend.

**What it creates:**
- S3 bucket with versioning (recover previous state files)
- KMS encryption at rest
- Public access blocked
- TLS-only access enforced via bucket policy
- `prevent_destroy` lifecycle rule

---

## Environment Comparison

| Dimension | Dev | Pre-Prod | Prod |
|-----------|-----|----------|------|
| **VPC CIDR** | `10.0.0.0/16` | `10.1.0.0/16` | `10.2.0.0/16` |
| **Availability Zones** | 2 | 3 | 3 |
| **NAT Gateways** | 1 (shared) | 1 (shared) | 3 (one per AZ) |
| **Total ECS Tasks** | 3 | 6 | 10 |
| **Total vCPUs** | 3.5 | 7 | 11 |
| **Total Memory** | 7 GB | 14 GB | 22 GB |
| **OpenSearch** | 1 × t3.small, 50 GB | 2 × t3.medium, 100 GB | 2 × r6g.large, 100 GB |
| **DynamoDB PITR** | Disabled | Enabled | Enabled |
| **Auto Scaling** | Disabled | Enabled | Enabled |
| **Container Insights** | Disabled | Enabled | Enabled |
| **ALB Deletion Protection** | Disabled | Disabled | Enabled |
| **Log Retention** | 7 days | 30 days | 90 days |
| **ECS Exec (debug shell)** | Enabled | Disabled | Disabled |
| **ECR Force Delete** | Enabled | Disabled | Disabled |

---

## Deployment Order

```
Step 1 (One-time bootstrap):
  cd infrastructure/global/state-bucket
  terraform init
  terraform apply

Step 2 (Per environment):
  cd infrastructure/environments/dev    # or preprod, prod
  terraform init
  terraform plan -out=tfplan
  terraform apply tfplan
```

---

## Security Summary

| Layer | Protection |
|-------|-----------|
| **Network** | VPC isolation, private subnets, no public IPs on containers |
| **Firewall** | Security groups with default-deny, SG-to-SG references |
| **Encryption at Rest** | KMS on S3, DynamoDB, OpenSearch, ECR, Secrets Manager |
| **Encryption in Transit** | TLS enforced on S3, OpenSearch (TLS 1.2 min), ALB |
| **Access Control** | IAM least-privilege, scoped to environment prefix |
| **Secrets** | Secrets Manager with 7-day recovery window |
| **Image Security** | ECR scan-on-push, immutable tags |
| **Deployment Safety** | Circuit breaker + rollback, `prevent_destroy` on stateful resources |
| **Audit** | VPC flow logs, CloudWatch logs, API Gateway access logs |
| **Cost Protection** | VPC endpoints (free S3/DynamoDB access), NAT optimization per env |

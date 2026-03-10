# MIA Infrastructure — Deployment Guide

A step-by-step guide to deploy the Manufacturing Insight Agent (MIA) infrastructure on AWS using Terraform.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [AWS Account Setup](#2-aws-account-setup)
3. [Local Environment Setup](#3-local-environment-setup)
4. [Step 1 — Bootstrap the State Bucket](#4-step-1--bootstrap-the-state-bucket)
5. [Step 2 — Build & Push Docker Images](#5-step-2--build--push-docker-images)
6. [Step 3 — Configure Secrets](#6-step-3--configure-secrets)
7. [Step 4 — Deploy Dev Environment](#7-step-4--deploy-dev-environment)
8. [Step 5 — Deploy Pre-Prod Environment](#8-step-5--deploy-pre-prod-environment)
9. [Step 6 — Deploy Prod Environment](#9-step-6--deploy-prod-environment)
10. [Post-Deployment Verification](#10-post-deployment-verification)
11. [Day-2 Operations](#11-day-2-operations)
12. [Rollback Procedures](#12-rollback-procedures)
13. [Tear Down](#13-tear-down)
14. [Troubleshooting](#14-troubleshooting)

---

## 1. Prerequisites

### Tools Required

| Tool | Minimum Version | Installation |
|------|----------------|-------------|
| **Terraform** | 1.10.0+ | `brew install terraform` or [terraform.io/downloads](https://developer.hashicorp.com/terraform/downloads) |
| **AWS CLI** | 2.x | `brew install awscli` or [aws.amazon.com/cli](https://aws.amazon.com/cli/) |
| **Docker** | 24.x+ | [docker.com/get-docker](https://docs.docker.com/get-docker/) |
| **Git** | 2.x | `brew install git` |
| **jq** (optional) | 1.6+ | `brew install jq` — useful for parsing Terraform outputs |

### Verify installations

```bash
terraform version    # Should show v1.10.0 or higher
aws --version        # Should show aws-cli/2.x
docker --version     # Should show Docker version 24.x+
```

---

## 2. AWS Account Setup

### 2.1 — Create an IAM User or Role for Terraform

Terraform needs an AWS identity with sufficient permissions. You have two options:

**Option A: IAM User (for local development)**

```bash
# Create a dedicated Terraform user (do this once via AWS Console or CLI)
aws iam create-user --user-name terraform-deployer

# Attach the required managed policies
aws iam attach-user-policy --user-name terraform-deployer \
  --policy-arn arn:aws:iam::aws:policy/AmazonVPCFullAccess

aws iam attach-user-policy --user-name terraform-deployer \
  --policy-arn arn:aws:iam::aws:policy/AmazonECS_FullAccess

aws iam attach-user-policy --user-name terraform-deployer \
  --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess

aws iam attach-user-policy --user-name terraform-deployer \
  --policy-arn arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess

aws iam attach-user-policy --user-name terraform-deployer \
  --policy-arn arn:aws:iam::aws:policy/AmazonOpenSearchServiceFullAccess

aws iam attach-user-policy --user-name terraform-deployer \
  --policy-arn arn:aws:iam::aws:policy/AmazonAPIGatewayAdministrator

aws iam attach-user-policy --user-name terraform-deployer \
  --policy-arn arn:aws:iam::aws:policy/IAMFullAccess

aws iam attach-user-policy --user-name terraform-deployer \
  --policy-arn arn:aws:iam::aws:policy/CloudWatchFullAccess

aws iam attach-user-policy --user-name terraform-deployer \
  --policy-arn arn:aws:iam::aws:policy/SecretsManagerReadWrite

aws iam attach-user-policy --user-name terraform-deployer \
  --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryFullAccess

aws iam attach-user-policy --user-name terraform-deployer \
  --policy-arn arn:aws:iam::aws:policy/ElasticLoadBalancingFullAccess

# Create access keys
aws iam create-access-key --user-name terraform-deployer
# Save the AccessKeyId and SecretAccessKey securely
```

**Option B: IAM Role with Assume Role (recommended for CI/CD)**

If your organization uses role-based access, update the `providers.tf` in each environment to include:

```hcl
provider "aws" {
  region = var.aws_region
  assume_role {
    role_arn     = "arn:aws:iam::ACCOUNT_ID:role/TerraformDeployRole"
    session_name = "terraform-mia"
  }
}
```

### 2.2 — Configure AWS CLI

```bash
# Configure your AWS credentials
aws configure

# You will be prompted for:
# AWS Access Key ID:      <your-access-key>
# AWS Secret Access Key:  <your-secret-key>
# Default region name:    us-east-1
# Default output format:  json

# Verify the identity
aws sts get-caller-identity
```

Expected output:
```json
{
    "UserId": "AIDXXXXXXXXXXXXXXXX",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/terraform-deployer"
}
```

### 2.3 — Enable Bedrock Model Access

Bedrock models require explicit activation in your AWS account:

1. Go to **AWS Console → Amazon Bedrock → Model access**
2. Click **Manage model access**
3. Enable the following models:
   - `Anthropic - Claude Sonnet 4.5` (us.anthropic.claude-sonnet-4-5-20251001-v1:0)
   - `Anthropic - Claude Opus 4.6` (us.anthropic.claude-opus-4-6-...-v1:0)
   - `Cohere - Embed English v3` (cohere.embed-english-v3)
4. Click **Save changes** — approval is usually instant for on-demand models

> **Note:** If your account requires Anthropic's approval for model access, submit the request early as it may take up to 48 hours.

---

## 3. Local Environment Setup

### 3.1 — Clone the repository

```bash
cd /path/to/your/workspace
git clone <repository-url>
cd infrastructure
```

### 3.2 — Understand the directory layout

```
infrastructure/
├── global/state-bucket/    ← Deploy FIRST (one-time)
├── environments/
│   ├── dev/                ← Deploy SECOND
│   ├── preprod/            ← Deploy THIRD
│   └── prod/               ← Deploy LAST
└── modules/                ← Reusable modules (not deployed directly)
```

### 3.3 — Customize configuration

Before deploying, review and update these values:

**In each `terraform.tfvars`:**
- `aws_region` — Change if not using `us-east-1`
- `owner` — Set to your team name or email
- `availability_zones` — Must match your chosen region

**In each `backend.tf`:**
- `bucket` — Must match the state bucket name (default: `mia-terraform-state`)
- `region` — Must match where the state bucket lives

**In `global/state-bucket/main.tf`:**
- `state_bucket_name` — S3 bucket names are globally unique. Change if `mia-terraform-state` is taken.

---

## 4. Step 1 — Bootstrap the State Bucket

This creates the S3 bucket that stores Terraform state for all environments. **Run this once, ever.**

```bash
cd infrastructure/global/state-bucket
```

### 4.1 — Initialize Terraform

```bash
terraform init
```

Expected output:
```
Initializing the backend...
Initializing provider plugins...
- Finding hashicorp/aws versions matching "~> 5.0"...
- Installing hashicorp/aws v5.x.x...

Terraform has been successfully initialized!
```

### 4.2 — Preview the changes

```bash
terraform plan
```

Expected output:
```
Plan: 5 to add, 0 to change, 0 to destroy.

Changes to Outputs:
  + state_bucket_arn  = (known after apply)
  + state_bucket_name = "mia-terraform-state"
```

You should see 5 resources:
1. `aws_s3_bucket.terraform_state`
2. `aws_s3_bucket_versioning.terraform_state`
3. `aws_s3_bucket_server_side_encryption_configuration.terraform_state`
4. `aws_s3_bucket_public_access_block.terraform_state`
5. `aws_s3_bucket_policy.enforce_tls`

### 4.3 — Apply

```bash
terraform apply
```

Type `yes` when prompted.

Expected output:
```
Apply complete! Resources: 5 added, 0 changed, 0 destroyed.

Outputs:
  state_bucket_arn  = "arn:aws:s3:::mia-terraform-state"
  state_bucket_name = "mia-terraform-state"
```

### 4.4 — Verify

```bash
aws s3 ls | grep mia-terraform-state
```

Expected:
```
2026-03-10 12:00:00 mia-terraform-state
```

> **Important:** The state for this bootstrap module is stored locally in `terraform.tfstate` inside `global/state-bucket/`. **Do not delete this file.** Commit it to your repository or store it safely.

---

## 5. Step 2 — Build & Push Docker Images

Before deploying ECS services, you need container images in ECR. The ECR repositories are created by Terraform, but you need to push at least a placeholder image first.

### 5.1 — Deploy ECR repositories first (quick partial apply)

```bash
cd infrastructure/environments/dev

terraform init

# Deploy only the ECR module first
terraform apply -target=module.ecr
```

Type `yes` when prompted. This creates the 3 ECR repositories.

### 5.2 — Authenticate Docker with ECR

```bash
# Get the AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION="us-east-1"

# Authenticate Docker
aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin \
  $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
```

Expected:
```
Login Succeeded
```

### 5.3 — Build and push images

For each service, build and push the Docker image:

```bash
# --- Frontend ---
cd /path/to/mia-langgraph/frontend
docker build -t mia-dev-frontend:latest .
docker tag mia-dev-frontend:latest \
  $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/mia-dev-frontend:latest
docker push \
  $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/mia-dev-frontend:latest

# --- Backend ---
cd /path/to/mia-langgraph/backend
docker build -t mia-dev-backend:latest .
docker tag mia-dev-backend:latest \
  $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/mia-dev-backend:latest
docker push \
  $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/mia-dev-backend:latest

# --- Agents ---
# (If agents share the same backend codebase, use the same Dockerfile)
cd /path/to/mia-langgraph/backend
docker build -t mia-dev-agents:latest -f Dockerfile.agents .
docker tag mia-dev-agents:latest \
  $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/mia-dev-agents:latest
docker push \
  $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/mia-dev-agents:latest
```

### 5.4 — Verify images in ECR

```bash
aws ecr list-images --repository-name mia-dev-frontend --region $AWS_REGION
aws ecr list-images --repository-name mia-dev-backend --region $AWS_REGION
aws ecr list-images --repository-name mia-dev-agents --region $AWS_REGION
```

Each should show at least one image with the `latest` tag.

---

## 6. Step 3 — Configure Secrets

Secrets Manager secrets are created by Terraform with placeholder values. You must update them with real values before the ECS services can function.

### 6.1 — Update each secret

```bash
# Azure AD Client Secret
aws secretsmanager update-secret \
  --secret-id "mia-dev/azure-ad-client-secret" \
  --secret-string '{"client_id":"YOUR_CLIENT_ID","client_secret":"YOUR_SECRET","tenant_id":"YOUR_TENANT_ID"}' \
  --region $AWS_REGION

# LangSmith API Key
aws secretsmanager update-secret \
  --secret-id "mia-dev/langsmith-api-key" \
  --secret-string '{"api_key":"ls-YOUR_LANGSMITH_API_KEY"}' \
  --region $AWS_REGION

# Snowflake Connection String
aws secretsmanager update-secret \
  --secret-id "mia-dev/snowflake-connection-string" \
  --secret-string '{"account":"YOUR_ACCOUNT","user":"YOUR_USER","password":"YOUR_PASSWORD","database":"YOUR_DB","schema":"YOUR_SCHEMA","warehouse":"YOUR_WH"}' \
  --region $AWS_REGION
```

### 6.2 — Verify secrets

```bash
# List all MIA secrets
aws secretsmanager list-secrets \
  --filter Key=name,Values=mia-dev \
  --query 'SecretList[].Name' \
  --output table \
  --region $AWS_REGION
```

Expected:
```
-----------------------------------------
|             ListSecrets               |
+---------------------------------------+
|  mia-dev/azure-ad-client-secret       |
|  mia-dev/langsmith-api-key            |
|  mia-dev/snowflake-connection-string  |
+---------------------------------------+
```

> **Security Note:** Never commit secret values to Git. The Terraform code creates secrets with `ignore_changes = [secret_string]`, so real values set via CLI/Console are preserved across `terraform apply` runs.

---

## 7. Step 4 — Deploy Dev Environment

Now deploy the full dev infrastructure.

### 7.1 — Initialize

```bash
cd infrastructure/environments/dev

terraform init
```

Expected output:
```
Initializing the backend...
  Successfully configured the backend "s3"!

Initializing modules...
- alb in ../../modules/alb
- api_gateway in ../../modules/api-gateway
- agents in ../../modules/ecs-service
- backend in ../../modules/ecs-service
- cloudwatch in ../../modules/cloudwatch
- dynamodb in ../../modules/dynamodb
- ecr in ../../modules/ecr
- ecs_cluster in ../../modules/ecs-cluster
- frontend in ../../modules/ecs-service
- iam in ../../modules/iam
- opensearch in ../../modules/opensearch
- s3 in ../../modules/s3
- secrets_manager in ../../modules/secrets-manager
- security_groups in ../../modules/security-groups
- vpc in ../../modules/vpc

Terraform has been successfully initialized!
```

### 7.2 — Plan

```bash
terraform plan -out=tfplan
```

Review the plan carefully. You should see approximately **70-80 resources** to be created:

```
Plan: ~75 to add, 0 to change, 0 to destroy.
```

**Key resources to verify in the plan output:**

| Category | Resources | Count |
|----------|-----------|-------|
| VPC & Networking | VPC, subnets, NAT, IGW, route tables, endpoints, flow logs | ~20 |
| Security Groups | ALB SG, ECS SG, OpenSearch SG, rules | ~10 |
| IAM | Execution role, task role, 7 policies | ~9 |
| ECR | 3 repositories, 3 lifecycle policies | ~6 |
| S3 | Bucket, versioning, encryption, public block, policy, lifecycle | ~6 |
| DynamoDB | 2 tables | ~2 |
| Secrets Manager | 3 secrets, 3 versions | ~6 |
| OpenSearch | Domain, log group, log policy | ~3 |
| CloudWatch | 4 log groups, 6 alarms | ~10 |
| ALB | ALB, 3 target groups, listener, 2 rules | ~7 |
| ECS | Cluster, capacity providers, 3 task defs, 3 services | ~8 |
| API Gateway | API, integration, 4 routes, stage, log group | ~7 |

### 7.3 — Apply

```bash
terraform apply tfplan
```

This will take approximately **15-25 minutes**. The longest resources to create are:
- **OpenSearch domain**: 10-15 minutes (AWS provisions managed Elasticsearch nodes)
- **NAT Gateway**: 1-2 minutes
- **ECS services**: 2-5 minutes (waits for tasks to reach RUNNING state)

Expected final output:
```
Apply complete! Resources: 75 added, 0 changed, 0 destroyed.

Outputs:

alb_dns_name       = "mia-dev-alb-XXXXXXXXX.us-east-1.elb.amazonaws.com"
dynamodb_tables    = {
  "chat_sessions" = "mia-dev-mia-chat-sessions"
  "session_turns" = "mia-dev-mia-session-turns"
}
ecr_repository_urls = {
  "agents"   = "123456789012.dkr.ecr.us-east-1.amazonaws.com/mia-dev-agents"
  "backend"  = "123456789012.dkr.ecr.us-east-1.amazonaws.com/mia-dev-backend"
  "frontend" = "123456789012.dkr.ecr.us-east-1.amazonaws.com/mia-dev-frontend"
}
ecs_cluster_name    = "mia-dev-cluster"
opensearch_endpoint = "search-mia-dev-search-XXXXXXXXX.us-east-1.es.amazonaws.com"
s3_bucket_name      = "mia-dev-knowledge-base"
vpc_id              = "vpc-0abcdef1234567890"
websocket_endpoint  = "wss://XXXXXXXXXX.execute-api.us-east-1.amazonaws.com/dev"
```

### 7.4 — Save the outputs

```bash
terraform output -json > dev-outputs.json
```

---

## 8. Step 5 — Deploy Pre-Prod Environment

### 8.1 — Initialize and plan

```bash
cd infrastructure/environments/preprod

terraform init
terraform plan -out=tfplan
```

Review the plan. Pre-prod creates the same resources but with:
- 3 AZs instead of 2
- 2 tasks per service instead of 1
- Larger OpenSearch nodes (t3.medium)
- Auto-scaling enabled
- Container Insights enabled

### 8.2 — Apply

```bash
terraform apply tfplan
```

Takes approximately **15-25 minutes**.

### 8.3 — Update secrets for preprod

```bash
# Repeat Step 6 with "mia-preprod" prefix
aws secretsmanager update-secret \
  --secret-id "mia-preprod/azure-ad-client-secret" \
  --secret-string '{"client_id":"...","client_secret":"...","tenant_id":"..."}' \
  --region $AWS_REGION

aws secretsmanager update-secret \
  --secret-id "mia-preprod/langsmith-api-key" \
  --secret-string '{"api_key":"ls-..."}' \
  --region $AWS_REGION

aws secretsmanager update-secret \
  --secret-id "mia-preprod/snowflake-connection-string" \
  --secret-string '{"account":"...","user":"...","password":"...","database":"...","schema":"...","warehouse":"..."}' \
  --region $AWS_REGION
```

### 8.4 — Push images to preprod ECR

```bash
# Authenticate
aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin \
  $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Tag and push (reuse dev images or build preprod-specific ones)
for service in frontend backend agents; do
  docker tag mia-dev-$service:latest \
    $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/mia-preprod-$service:latest
  docker push \
    $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/mia-preprod-$service:latest
done
```

---

## 9. Step 6 — Deploy Prod Environment

> **Warning:** Production deployment should go through a formal change management process. Ensure preprod has been validated first.

### 9.1 — Pre-deployment checklist

- [ ] Pre-prod environment tested and stable
- [ ] All secrets configured for prod
- [ ] Docker images built, tested, and tagged with a release version (not `latest`)
- [ ] Team notified of upcoming deployment
- [ ] Rollback plan reviewed

### 9.2 — Initialize and plan

```bash
cd infrastructure/environments/prod

terraform init
terraform plan -out=tfplan
```

**Carefully review the plan.** Prod has critical differences:
- `single_nat_gateway = false` — Creates 3 NAT Gateways (one per AZ)
- `enable_deletion_protection = true` — ALB cannot be accidentally deleted
- `opensearch_instance_type = "r6g.large.search"` — Memory-optimized instances
- 10 total ECS tasks (2 frontend + 4 backend + 4 agents)
- Auto-scaling enabled (can grow to 3× desired count)

### 9.3 — Apply

```bash
terraform apply tfplan
```

Takes approximately **20-30 minutes** (OpenSearch with r6g.large nodes takes longer).

### 9.4 — Configure prod secrets and push images

```bash
# Update secrets (same pattern as above with "mia-prod" prefix)
# Push versioned images (use specific tags like v1.0.0, not latest)
for service in frontend backend agents; do
  docker tag mia-$service:v1.0.0 \
    $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/mia-prod-$service:v1.0.0
  docker push \
    $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/mia-prod-$service:v1.0.0
done
```

---

## 10. Post-Deployment Verification

### 10.1 — Check ECS services are healthy

```bash
ENV="dev"  # Change to preprod or prod

# List all services in the cluster
aws ecs list-services \
  --cluster mia-${ENV}-cluster \
  --query 'serviceArns' \
  --output table \
  --region $AWS_REGION

# Check each service status
for service in frontend backend agents; do
  echo "=== mia-${ENV}-${service} ==="
  aws ecs describe-services \
    --cluster mia-${ENV}-cluster \
    --services mia-${ENV}-${service} \
    --query 'services[0].{Status:status,Running:runningCount,Desired:desiredCount,Deployments:deployments[0].rolloutState}' \
    --output table \
    --region $AWS_REGION
done
```

Expected output per service:
```
-------------------------------------------
|           DescribeServices              |
+-------------+---------------------------+
|  Desired    |  2                        |
|  Deployments|  COMPLETED                |
|  Running    |  2                        |
|  Status     |  ACTIVE                   |
+-------------+---------------------------+
```

**Key checks:**
- `Running` should equal `Desired`
- `Status` should be `ACTIVE`
- `rolloutState` should be `COMPLETED`

### 10.2 — Check ALB target group health

```bash
# Get target group ARNs
TG_ARNS=$(aws elbv2 describe-target-groups \
  --names mia-${ENV}-frontend-tg mia-${ENV}-backend-tg mia-${ENV}-agents-tg \
  --query 'TargetGroups[].TargetGroupArn' \
  --output text \
  --region $AWS_REGION)

# Check health of each target group
for tg_arn in $TG_ARNS; do
  echo "=== $(echo $tg_arn | grep -o '[^/]*$') ==="
  aws elbv2 describe-target-health \
    --target-group-arn $tg_arn \
    --query 'TargetHealthDescriptions[].{Target:Target.Id,Port:Target.Port,Health:TargetHealth.State}' \
    --output table \
    --region $AWS_REGION
done
```

Expected: All targets show `Health: healthy`

### 10.3 — Test the application

```bash
# Get the ALB DNS name
ALB_DNS=$(terraform output -raw alb_dns_name)

# Test frontend
curl -s -o /dev/null -w "%{http_code}" http://$ALB_DNS/
# Expected: 200

# Test backend health
curl -s http://$ALB_DNS/api/health
# Expected: {"status":"healthy"} or similar

# Test agents health
curl -s http://$ALB_DNS/agents/health
# Expected: {"status":"healthy"} or similar
```

### 10.4 — Check OpenSearch is accessible

```bash
OS_ENDPOINT=$(terraform output -raw opensearch_endpoint)

# From a bastion host or via ECS Exec (dev only):
curl -s https://$OS_ENDPOINT/_cluster/health
# Expected: {"status":"green"} or {"status":"yellow"} (yellow is OK for single-node dev)
```

### 10.5 — Check CloudWatch logs

```bash
# View recent logs for the backend service
aws logs tail /ecs/mia-${ENV}/backend \
  --since 30m \
  --follow \
  --region $AWS_REGION
```

### 10.6 — Test WebSocket connectivity

```bash
WS_URL=$(terraform output -raw websocket_endpoint)
echo "WebSocket endpoint: $WS_URL"

# Use wscat to test (install: npm install -g wscat)
wscat -c $WS_URL
# If connected successfully, you'll see a > prompt
# Type: {"action":"sendMessage","data":"hello"}
```

---

## 11. Day-2 Operations

### 11.1 — Deploying a new application version

When you have a new version of the application code:

```bash
# 1. Build and push the new image
docker build -t mia-prod-backend:v1.1.0 .
docker tag mia-prod-backend:v1.1.0 \
  $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/mia-prod-backend:v1.1.0
docker push \
  $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/mia-prod-backend:v1.1.0

# 2. Update the container_image in main.tf or use:
aws ecs update-service \
  --cluster mia-prod-cluster \
  --service mia-prod-backend \
  --force-new-deployment \
  --region $AWS_REGION

# 3. Watch the deployment roll out
aws ecs wait services-stable \
  --cluster mia-prod-cluster \
  --services mia-prod-backend \
  --region $AWS_REGION
echo "Deployment complete!"
```

The circuit breaker will automatically roll back if the new tasks fail health checks.

### 11.2 — Scaling a service manually

```bash
# Scale backend to 6 tasks
aws ecs update-service \
  --cluster mia-prod-cluster \
  --service mia-prod-backend \
  --desired-count 6 \
  --region $AWS_REGION
```

> Note: If auto-scaling is enabled, it may adjust this value based on CPU/memory utilization.

### 11.3 — Viewing auto-scaling activity

```bash
aws application-autoscaling describe-scaling-activities \
  --service-namespace ecs \
  --resource-id service/mia-prod-cluster/mia-prod-backend \
  --region $AWS_REGION \
  --query 'ScalingActivities[0:5].{Time:StartTime,Status:StatusCode,Cause:Cause}' \
  --output table
```

### 11.4 — Debugging with ECS Exec (dev only)

```bash
# Get a task ID
TASK_ID=$(aws ecs list-tasks \
  --cluster mia-dev-cluster \
  --service-name mia-dev-backend \
  --query 'taskArns[0]' \
  --output text \
  --region $AWS_REGION)

# Open a shell inside the container
aws ecs execute-command \
  --cluster mia-dev-cluster \
  --task $TASK_ID \
  --container backend \
  --command "/bin/sh" \
  --interactive \
  --region $AWS_REGION
```

### 11.5 — Modifying infrastructure

```bash
cd infrastructure/environments/prod

# Edit terraform.tfvars or main.tf as needed
# Then:
terraform plan -out=tfplan    # ALWAYS review the plan
terraform apply tfplan
```

**Golden rule:** Never `terraform apply` without reviewing the plan first, especially in prod.

### 11.6 — Rotating secrets

```bash
# Update the secret value
aws secretsmanager update-secret \
  --secret-id "mia-prod/langsmith-api-key" \
  --secret-string '{"api_key":"ls-NEW_API_KEY"}' \
  --region $AWS_REGION

# Force ECS to pick up the new secret by restarting tasks
aws ecs update-service \
  --cluster mia-prod-cluster \
  --service mia-prod-backend \
  --force-new-deployment \
  --region $AWS_REGION
```

---

## 12. Rollback Procedures

### 12.1 — ECS service rollback (automatic)

The deployment circuit breaker handles this automatically. If new tasks fail:
1. ECS detects repeated health check failures
2. Marks the deployment as FAILED
3. Rolls back to the previous task definition
4. No manual intervention needed

Check rollback status:
```bash
aws ecs describe-services \
  --cluster mia-prod-cluster \
  --services mia-prod-backend \
  --query 'services[0].deployments[].{Status:rolloutState,TaskDef:taskDefinition,Running:runningCount}' \
  --output table \
  --region $AWS_REGION
```

### 12.2 — Manual ECS rollback

```bash
# List recent task definitions
aws ecs list-task-definitions \
  --family-prefix mia-prod-backend \
  --sort DESC \
  --query 'taskDefinitionArns[0:5]' \
  --output table \
  --region $AWS_REGION

# Roll back to a specific task definition
aws ecs update-service \
  --cluster mia-prod-cluster \
  --service mia-prod-backend \
  --task-definition mia-prod-backend:PREVIOUS_REVISION \
  --region $AWS_REGION
```

### 12.3 — Terraform infrastructure rollback

```bash
# Option 1: Revert the code change and re-apply
git revert HEAD
cd infrastructure/environments/prod
terraform plan -out=tfplan
terraform apply tfplan

# Option 2: Restore state from a previous version (S3 versioning)
# List state file versions
aws s3api list-object-versions \
  --bucket mia-terraform-state \
  --prefix environments/prod/terraform.tfstate \
  --query 'Versions[0:5].{VersionId:VersionId,Modified:LastModified,Size:Size}' \
  --output table

# Download a previous version
aws s3api get-object \
  --bucket mia-terraform-state \
  --key environments/prod/terraform.tfstate \
  --version-id "PREVIOUS_VERSION_ID" \
  restored-state.tfstate
```

### 12.4 — DynamoDB point-in-time recovery

```bash
# Restore a table to a specific point in time
aws dynamodb restore-table-to-point-in-time \
  --source-table-name mia-prod-mia-chat-sessions \
  --target-table-name mia-prod-mia-chat-sessions-restored \
  --restore-date-time "2026-03-09T14:00:00Z" \
  --region $AWS_REGION
```

---

## 13. Tear Down

### 13.1 — Destroy an environment

> **Warning:** This permanently deletes all resources and data. Only use for dev/preprod cleanup.

Before destroying, you must disable protections:

```bash
cd infrastructure/environments/dev

# Step 1: Remove prevent_destroy from stateful resources
# Edit modules or override with:
# (Only needed if you truly want to destroy — normally these protect you)
```

For dev (no deletion protection, prevent_destroy can be overridden):

```bash
# Destroy all resources in the environment
terraform destroy
```

Type `yes` when prompted. Takes 10-20 minutes.

**Destroy order matters.** Terraform handles dependencies, but if you have issues:
```bash
# Destroy in reverse dependency order
terraform destroy -target=module.api_gateway
terraform destroy -target=module.agents
terraform destroy -target=module.backend
terraform destroy -target=module.frontend
terraform destroy -target=module.ecs_cluster
terraform destroy -target=module.alb
terraform destroy -target=module.cloudwatch
terraform destroy -target=module.opensearch
terraform destroy -target=module.secrets_manager
terraform destroy -target=module.dynamodb
terraform destroy -target=module.s3
terraform destroy -target=module.ecr
terraform destroy -target=module.iam
terraform destroy -target=module.security_groups
terraform destroy -target=module.vpc
```

### 13.2 — Destroy the state bucket (if truly decommissioning)

```bash
# Empty the bucket first (required before deletion)
aws s3 rm s3://mia-terraform-state --recursive

# Remove prevent_destroy from global/state-bucket/main.tf, then:
cd infrastructure/global/state-bucket
terraform destroy
```

---

## 14. Troubleshooting

### ECS tasks failing to start

**Symptom:** Running count stays at 0, desired count is > 0.

```bash
# Check stopped task reasons
aws ecs list-tasks \
  --cluster mia-dev-cluster \
  --service-name mia-dev-backend \
  --desired-status STOPPED \
  --region $AWS_REGION

TASK_ARN=$(aws ecs list-tasks \
  --cluster mia-dev-cluster \
  --service-name mia-dev-backend \
  --desired-status STOPPED \
  --query 'taskArns[0]' \
  --output text \
  --region $AWS_REGION)

aws ecs describe-tasks \
  --cluster mia-dev-cluster \
  --tasks $TASK_ARN \
  --query 'tasks[0].{StopCode:stopCode,Reason:stoppedReason,Containers:containers[].{Name:name,ExitCode:exitCode,Reason:reason}}' \
  --output json \
  --region $AWS_REGION
```

**Common causes and fixes:**

| Error | Cause | Fix |
|-------|-------|-----|
| `CannotPullContainerError` | Image doesn't exist in ECR | Push image to ECR (Step 5) |
| `ResourceNotFoundException: Secret not found` | Secret ARN doesn't match | Verify secret names in Secrets Manager |
| `OutOfMemoryError` | Container exceeds memory limit | Increase `memory` in terraform.tfvars |
| `HealthCheckFailure` | Container health check failing | Check application logs, verify health endpoint |
| `STOPPED (Essential container exited)` | Application crashed on startup | Check CloudWatch logs for the service |

### OpenSearch cluster status red/yellow

```bash
# Check from ECS Exec or bastion
curl -s https://$OS_ENDPOINT/_cluster/health?pretty

# Yellow = unassigned replica shards (normal for single-node dev)
# Red = unassigned primary shards (data loss risk)

# Check unassigned shards
curl -s https://$OS_ENDPOINT/_cat/shards?v&h=index,shard,prirep,state,unassigned.reason | grep UNASSIGNED
```

### NAT Gateway connectivity issues

**Symptom:** ECS tasks in private subnets can't reach the internet.

```bash
# Check NAT Gateway state
aws ec2 describe-nat-gateways \
  --filter Name=tag:Name,Values="mia-dev-*" \
  --query 'NatGateways[].{Id:NatGatewayId,State:State,SubnetId:SubnetId}' \
  --output table \
  --region $AWS_REGION
```

State should be `available`. If `failed`, check that the EIP was allocated and the Internet Gateway exists.

### Terraform state lock errors

```bash
# If you see "Error acquiring the state lock"
# This means another terraform process is running, OR a previous run crashed

# Check if another apply is running (ask your team)
# If no one is running terraform, force-unlock:
terraform force-unlock LOCK_ID
```

> **Warning:** Only force-unlock if you are certain no other process is using the state. Concurrent state modifications can corrupt your infrastructure.

### ALB returning 502 or 503 errors

```bash
# 502 = ALB can't reach the target (container not listening on expected port)
# 503 = No healthy targets in the target group

# Check target health
aws elbv2 describe-target-health \
  --target-group-arn $TG_ARN \
  --query 'TargetHealthDescriptions[].{Target:Target.Id,Health:TargetHealth.State,Reason:TargetHealth.Reason}' \
  --output table \
  --region $AWS_REGION
```

| Health Reason | Fix |
|---------------|-----|
| `Target.NotRegistered` | ECS service hasn't registered tasks yet — wait 1-2 minutes |
| `Target.FailedHealthChecks` | Application isn't responding on the health check path — check app logs |
| `Elb.InternalError` | Transient ALB issue — usually resolves in minutes |
| `Target.NotInUse` | Target group not attached to a listener — check ALB rules |

### Insufficient IAM permissions during deployment

```bash
# If Terraform fails with "AccessDenied" errors, check which API call failed:
# The error message will show the action (e.g., "ecs:CreateCluster")

# Verify your current identity
aws sts get-caller-identity

# Check which policies are attached
aws iam list-attached-user-policies --user-name terraform-deployer
```

Add the missing permission to the Terraform deployer user/role as described in Section 2.1.

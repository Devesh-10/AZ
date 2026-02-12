# Agentic KPI Assistant

An intelligent KPI analytics assistant powered by Claude 3.5 Sonnet on AWS Bedrock. This system uses a multi-agent architecture to answer business KPI questions with natural language understanding, data retrieval, and visualization.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        React Frontend                           │
│  ┌──────────┐  ┌──────────────┐  ┌──────────┐  ┌────────────┐ │
│  │   Chat   │  │Visualization │  │ Telemetry│  │  Knowledge │ │
│  │  Panel   │  │    Panel     │  │   Panel  │  │   Graph    │ │
│  └──────────┘  └──────────────┘  └──────────┘  └────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     API Gateway (REST)                          │
│         POST /api/chat/query    GET /api/chat/telemetry         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Lambda Function                              │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                   Agent Orchestrator                        │ │
│  │  ┌──────────┐ ┌───────────┐ ┌─────────┐ ┌───────────────┐ │ │
│  │  │Supervisor│→│KPI Gateway│→│Validator│→│ Visualization │ │ │
│  │  │  Agent   │ │   Agent   │ │  Agent  │ │    Agent      │ │ │
│  │  └──────────┘ └───────────┘ └─────────┘ └───────────────┘ │ │
│  │       │                                                     │ │
│  │       └──────────►┌─────────┐                              │ │
│  │                   │ Analyst │ (for complex queries)        │ │
│  │                   │  Agent  │                              │ │
│  │                   └─────────┘                              │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              │                                   │
│  ┌───────────────┐  ┌────────────────┐  ┌──────────────────┐   │
│  │  Local JSON   │  │   Knowledge    │  │  Bedrock Claude  │   │
│  │   KPI Mart    │  │     Graph      │  │   3.5 Sonnet     │   │
│  └───────────────┘  └────────────────┘  └──────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Agent Flow

1. **Supervisor Agent**: Classifies queries as REJECT, KPI_SIMPLE, or KPI_COMPLEX
2. **KPI Gateway Agent**: Handles simple queries - parses intent, fetches data, generates explanations
3. **Analyst Agent**: Handles complex queries - plans analysis, executes sub-queries, generates narrative
4. **Validator Agent**: Validates results, generates follow-up questions if needed
5. **Visualization Agent**: Maps results to appropriate chart configurations

## Prerequisites

- **Node.js** 18+ and npm
- **AWS CLI** configured with appropriate credentials
- **AWS CDK** installed globally: `npm install -g aws-cdk`
- **Amazon Bedrock** access with Claude 3.5 Sonnet enabled in your region

### Enable Bedrock Model Access

1. Go to AWS Console → Amazon Bedrock → Model access
2. Request access to `anthropic.claude-3-5-sonnet-20241022-v2:0`
3. Wait for approval (usually instant for Claude models)

## Project Structure

```
agentic-kpi-assistant/
├── backend/                    # Lambda backend
│   ├── src/
│   │   ├── agents/            # Agent implementations
│   │   ├── core/              # Bedrock client, telemetry
│   │   ├── data/              # KPI data & knowledge graph
│   │   ├── dataAccess/        # Repository layer
│   │   ├── orchestrator/      # Agent orchestration
│   │   ├── handler.ts         # Lambda entry point
│   │   └── types.ts           # TypeScript types
│   └── package.json
├── frontend/                   # React frontend
│   ├── src/
│   │   ├── api/               # API client
│   │   ├── components/        # React components
│   │   └── types/             # Frontend types
│   └── package.json
├── infra/                      # CDK infrastructure
│   ├── lib/
│   │   └── agentic-kpi-stack.ts
│   └── bin/
│       └── app.ts
├── scripts/                    # Utility scripts
│   └── convertCsvToJson.ts    # CSV to JSON converter
└── README.md
```

## Quick Start

### 1. Clone and Install Dependencies

```bash
cd agentic-kpi-assistant

# Install backend dependencies
cd backend
npm install

# Install frontend dependencies
cd ../frontend
npm install

# Install infra dependencies
cd ../infra
npm install
```

### 2. Configure Your Data

The KPI data is stored in `backend/src/data/kpiMart.json`. You can either:

**Option A: Use the sample data** (default)
- The sample data includes revenue, cost, units_sold, customer_count, and margin_pct
- Dimensions: region (EMEA, APAC, Americas), product (Product A, B), segment (Enterprise, SMB)

**Option B: Replace with your own data**

Expected JSON format:
```json
[
  {
    "date": "2024-01-01",
    "region": "EMEA",
    "product": "Product A",
    "segment": "Enterprise",
    "kpi": "revenue",
    "value": 125000
  },
  ...
]
```

**Option C: Convert from CSV**
```bash
# If you have a CSV file with columns: date,region,product,segment,kpi,value
npx ts-node scripts/convertCsvToJson.ts mydata.csv backend/src/data/kpiMart.json
```

### 3. Build the Backend

```bash
cd backend
npm run build
```

### 4. Deploy to AWS

```bash
cd infra

# Bootstrap CDK (first time only)
cdk bootstrap

# Deploy the stack
cdk deploy

# Note the outputs:
# - ApiUrl: Your API Gateway endpoint
# - FrontendUrl: CloudFront URL for the frontend
# - FrontendBucketName: S3 bucket for frontend files
```

### 5. Configure Frontend

Create a `.env` file in the frontend directory:
```bash
cd frontend
echo "VITE_API_BASE_URL=<your-api-url-from-cdk-output>" > .env
```

### 6. Run Frontend Locally (Development)

```bash
cd frontend
npm run dev
```

Open http://localhost:3000

### 7. Deploy Frontend to S3/CloudFront (Production)

```bash
cd frontend
npm run build

# Upload to S3 (replace with your bucket name from CDK output)
aws s3 sync dist/ s3://<frontend-bucket-name> --delete

# Invalidate CloudFront cache (optional, for updates)
aws cloudfront create-invalidation --distribution-id <dist-id> --paths "/*"
```

## API Endpoints

### POST /api/chat/query
Send a KPI question.

**Request:**
```json
{
  "sessionId": "optional-session-id",
  "message": "What was total revenue in Q1 2024?"
}
```

**Response:**
```json
{
  "sessionId": "generated-or-provided-session-id",
  "answer": "Total revenue in Q1 2024 was $1.2M across all regions...",
  "visualizationConfig": {
    "chartType": "bar",
    "title": "Revenue by Region",
    "series": [...]
  },
  "kpiResult": [...],
  "validationResult": {...}
}
```

### GET /api/chat/telemetry/{sessionId}
Get agent telemetry logs for a session.

### GET /api/meta/schema
Get available KPIs and dimensions.

### GET /api/meta/knowledge-graph
Get the knowledge graph structure.

## Example Queries

**Simple queries (KPI Gateway):**
- "What was total revenue in January 2024?"
- "Show me revenue by region"
- "Compare revenue and cost by month"
- "What's the customer count in EMEA?"

**Complex queries (Analyst):**
- "Why is APAC revenue lower than Americas?"
- "What's driving the margin improvement?"
- "Analyze the revenue trend over Q1"
- "Which products are underperforming?"

## Customization

### Adding New KPIs

1. Add data to `backend/src/data/kpiMart.json`
2. Update `backend/src/data/knowledgeGraph.json` with KPI metadata
3. Rebuild and redeploy

### Modifying Agent Behavior

- **Supervisor prompts**: `backend/src/agents/SupervisorAgent.ts`
- **KPI parsing**: `backend/src/agents/KpiGatewayAgent.ts`
- **Analysis logic**: `backend/src/agents/AnalystAgent.ts`
- **Validation rules**: `backend/src/agents/ValidatorAgent.ts`
- **Chart selection**: `backend/src/agents/VisualizationAgent.ts`

### Using DynamoDB for Telemetry (Persistent)

By default, telemetry is stored in-memory (lost on cold start). To enable DynamoDB:

1. Uncomment the DynamoDB code in `backend/src/core/telemetryStore.ts`
2. Add DynamoDB table to the CDK stack
3. Grant Lambda permissions to the table

## Telemetry Store Options

The system supports two telemetry options:

**Option A (Default): In-Memory**
- Fast, no extra infrastructure
- Telemetry lost on Lambda cold start
- Good for demos and development

**Option B: DynamoDB**
- Persistent across restarts
- Requires additional table
- Better for production

Current implementation uses **Option A** for simplicity.

## Troubleshooting

### "Access denied" errors from Bedrock
- Ensure Claude 3.5 Sonnet is enabled in your Bedrock console
- Check the model ID matches your region's available models
- Verify IAM permissions include `bedrock:InvokeModel`

### CORS errors in browser
- API Gateway CORS is configured in the CDK stack
- Ensure you're using the full API URL including `/prod` stage

### Empty responses
- Check CloudWatch logs for the Lambda function
- Verify KPI data file is properly formatted
- Ensure the query mentions KPIs that exist in your data

## Cost Considerations

- **Lambda**: Pay per invocation and duration
- **API Gateway**: Pay per request
- **Bedrock Claude**: Pay per input/output tokens (~$15/1M input, $75/1M output tokens)
- **CloudFront + S3**: Minimal for low-traffic demos

For a demo with ~100 queries/day, expect < $5/day primarily from Bedrock usage.

## License

MIT License - feel free to use and modify for your projects.

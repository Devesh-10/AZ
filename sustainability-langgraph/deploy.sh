#!/bin/bash
set -e

echo "=========================================="
echo "SIA LangGraph Deployment Script"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Step 1: Build Frontend
echo -e "\n${YELLOW}Step 1: Building Frontend...${NC}"
cd frontend
npm install
VITE_API_BASE_URL="" npm run build
cd ..

# Step 1.5: Build Lambda package
echo -e "\n${YELLOW}Step 1.5: Building Lambda package...${NC}"
bash scripts/build-lambda.sh

# Step 2: Install CDK dependencies
echo -e "\n${YELLOW}Step 2: Installing CDK dependencies...${NC}"
cd infra
npm install
cd ..

# Step 3: Bootstrap CDK (if needed)
echo -e "\n${YELLOW}Step 3: Bootstrapping CDK (if needed)...${NC}"
cd infra
npx cdk bootstrap 2>/dev/null || true

# Step 4: Deploy Stack
echo -e "\n${YELLOW}Step 4: Deploying to AWS...${NC}"
npx cdk deploy --require-approval never --outputs-file ../cdk-outputs.json

cd ..

# Step 5: Display outputs
echo -e "\n${GREEN}=========================================="
echo "Deployment Complete!"
echo "==========================================${NC}"

if [ -f cdk-outputs.json ]; then
    echo -e "\n${GREEN}Deployment Outputs:${NC}"
    cat cdk-outputs.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
stack = data.get('SiaLanggraphStack', {})
print(f\"\\n  Frontend URL: {stack.get('FrontendUrl', 'N/A')}\")
print(f\"  API URL: {stack.get('ApiUrl', 'N/A')}\")
print(f\"  S3 Bucket: {stack.get('FrontendBucketName', 'N/A')}\")
print(f\"  CloudFront ID: {stack.get('CloudFrontDistributionId', 'N/A')}\")
"
fi

echo -e "\n${GREEN}Done! Share the Frontend URL with your team.${NC}"

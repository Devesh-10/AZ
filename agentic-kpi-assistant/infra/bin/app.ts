#!/usr/bin/env node
import "source-map-support/register";
import * as cdk from "aws-cdk-lib";
import { AgenticKpiStack } from "../lib/agentic-kpi-stack";

const app = new cdk.App();

// Get configuration from context or environment
const bedrockRegion = app.node.tryGetContext("bedrockRegion") || process.env.BEDROCK_REGION || "us-east-1";
const bedrockModelId = app.node.tryGetContext("bedrockModelId") || process.env.BEDROCK_MODEL_ID || "anthropic.claude-3-5-sonnet-20241022-v2:0";

new AgenticKpiStack(app, "AgenticKpiStack", {
  bedrockRegion,
  bedrockModelId,
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION || "us-east-1",
  },
  description: "Agentic KPI Assistant - AWS Infrastructure",
});

app.synth();

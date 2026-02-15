#!/usr/bin/env node
import "source-map-support/register";
import * as cdk from "aws-cdk-lib";
import { SiaLanggraphStack } from "../lib/sia-stack";

const app = new cdk.App();

new SiaLanggraphStack(app, "SiaLanggraphStack", {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION || "us-east-1",
  },
  description: "SIA LangGraph - Sustainability Insight Agent Infrastructure",
});

app.synth();

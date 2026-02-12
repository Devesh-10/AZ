#!/usr/bin/env node
import "source-map-support/register";
import * as cdk from "aws-cdk-lib";
import { MiaLanggraphStack } from "../lib/mia-stack";

const app = new cdk.App();

new MiaLanggraphStack(app, "MiaLanggraphStack", {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION || "us-east-1",
  },
  description: "MIA LangGraph - Manufacturing Insight Agent Infrastructure",
});

app.synth();

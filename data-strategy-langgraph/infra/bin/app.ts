#!/usr/bin/env node
import "source-map-support/register";
import * as cdk from "aws-cdk-lib";
import { DsaLanggraphStack } from "../lib/dsa-stack";

const app = new cdk.App();

new DsaLanggraphStack(app, "DsaLanggraphStack", {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION || "us-east-1",
  },
  description: "DSA LangGraph - Data Strategy Agent Infrastructure",
});

app.synth();

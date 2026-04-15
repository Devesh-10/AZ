#!/usr/bin/env node
import "source-map-support/register";
import * as cdk from "aws-cdk-lib";
import { TiaStack } from "../lib/tia-stack";

const app = new cdk.App();

new TiaStack(app, "TiaStack", {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION || "us-east-1",
  },
  description: "TIA - Test Intelligence Agent Infrastructure",
});

app.synth();

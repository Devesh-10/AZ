import * as cdk from "aws-cdk-lib";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as apigateway from "aws-cdk-lib/aws-apigateway";
import * as s3 from "aws-cdk-lib/aws-s3";
import * as s3deploy from "aws-cdk-lib/aws-s3-deployment";
import * as cloudfront from "aws-cdk-lib/aws-cloudfront";
import * as origins from "aws-cdk-lib/aws-cloudfront-origins";
import * as iam from "aws-cdk-lib/aws-iam";
import { Construct } from "constructs";
import * as path from "path";

export class TiaStack extends cdk.Stack {
  public readonly apiUrl: cdk.CfnOutput;
  public readonly frontendUrl: cdk.CfnOutput;

  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // ==========================================
    // Lambda Function (pre-built locally)
    // ==========================================
    // Note: Run scripts/build-lambda.sh before deploying

    const backendLambda = new lambda.Function(this, "TiaBackendHandler", {
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: "lambda_handler.handler",
      code: lambda.Code.fromAsset(path.join(__dirname, "../../lambda-build")),
      timeout: cdk.Duration.seconds(180),
      memorySize: 2048,
      environment: {
        ORCHESTRATOR_MODEL: "us.anthropic.claude-sonnet-4-20250514-v1:0",
        REQUIREMENT_MODEL: "us.anthropic.claude-sonnet-4-20250514-v1:0",
        TEST_GEN_MODEL: "us.anthropic.claude-sonnet-4-20250514-v1:0",
        SYNTHETIC_DATA_MODEL: "us.anthropic.claude-sonnet-4-20250514-v1:0",
        EXECUTION_MODEL: "us.anthropic.claude-sonnet-4-20250514-v1:0",
        ANALYSIS_MODEL: "us.anthropic.claude-sonnet-4-20250514-v1:0",
        REFACTOR_MODEL: "us.anthropic.claude-sonnet-4-20250514-v1:0",
        REPORTING_MODEL: "us.anthropic.claude-sonnet-4-20250514-v1:0",
      },
      description: "TIA LangGraph Backend - Test Intelligence Agent (7-step pipeline)",
    });

    // Grant Bedrock permissions
    backendLambda.addToRolePolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream",
          "bedrock:Converse",
          "bedrock:ConverseStream",
        ],
        resources: ["*"],
      })
    );

    // ==========================================
    // Lambda Function URL (no 29s timeout limit)
    // ==========================================
    const functionUrl = backendLambda.addFunctionUrl({
      authType: lambda.FunctionUrlAuthType.NONE,
      invokeMode: lambda.InvokeMode.BUFFERED,
    });

    // ==========================================
    // API Gateway
    // ==========================================

    const api = new apigateway.RestApi(this, "TiaApi", {
      restApiName: "TIA - Test Intelligence Agent API",
      description: "Test Intelligence Agent API - 7-step AI testing pipeline",
      defaultCorsPreflightOptions: {
        allowOrigins: apigateway.Cors.ALL_ORIGINS,
        allowMethods: apigateway.Cors.ALL_METHODS,
        allowHeaders: [
          "Content-Type",
          "Authorization",
          "X-Amz-Date",
          "X-Api-Key",
        ],
      },
      deployOptions: {
        stageName: "prod",
        throttlingRateLimit: 100,
        throttlingBurstLimit: 200,
      },
    });

    const lambdaIntegration = new apigateway.LambdaIntegration(backendLambda);

    // Proxy all requests to Lambda
    api.root.addMethod("ANY", lambdaIntegration);
    api.root.addProxy({
      defaultIntegration: lambdaIntegration,
      anyMethod: true,
    });

    // ==========================================
    // S3 + CloudFront for Frontend
    // ==========================================

    const frontendBucket = new s3.Bucket(this, "TiaFrontendBucket", {
      bucketName: `tia-frontend-${this.account}`,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
    });

    const originAccessIdentity = new cloudfront.OriginAccessIdentity(
      this,
      "TiaOAI"
    );
    frontendBucket.grantRead(originAccessIdentity);

    const distribution = new cloudfront.Distribution(
      this,
      "TiaFrontendDistribution",
      {
        comment: "TIA - Test Intelligence Agent Frontend",
        defaultBehavior: {
          origin: new origins.S3Origin(frontendBucket, {
            originAccessIdentity,
          }),
          viewerProtocolPolicy:
            cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
          cachePolicy: cloudfront.CachePolicy.CACHING_DISABLED,
        },
        additionalBehaviors: {
          "/api/*": {
            origin: new origins.HttpOrigin(
              `${api.restApiId}.execute-api.${this.region}.amazonaws.com`,
              {
                originPath: "/prod",
                readTimeout: cdk.Duration.seconds(60),
              }
            ),
            viewerProtocolPolicy:
              cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
            cachePolicy: cloudfront.CachePolicy.CACHING_DISABLED,
            originRequestPolicy:
              cloudfront.OriginRequestPolicy.ALL_VIEWER,
            allowedMethods: cloudfront.AllowedMethods.ALLOW_ALL,
          },
          "/health": {
            origin: new origins.HttpOrigin(
              `${api.restApiId}.execute-api.${this.region}.amazonaws.com`,
              {
                originPath: "/prod",
              }
            ),
            viewerProtocolPolicy:
              cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
            cachePolicy: cloudfront.CachePolicy.CACHING_DISABLED,
            allowedMethods: cloudfront.AllowedMethods.ALLOW_ALL,
          },
        },
        defaultRootObject: "index.html",
        errorResponses: [
          {
            httpStatus: 404,
            responseHttpStatus: 200,
            responsePagePath: "/index.html",
          },
          {
            httpStatus: 403,
            responseHttpStatus: 200,
            responsePagePath: "/index.html",
          },
        ],
      }
    );

    // Deploy frontend to S3
    new s3deploy.BucketDeployment(this, "DeployFrontend", {
      sources: [
        s3deploy.Source.asset(path.join(__dirname, "../../frontend/dist")),
      ],
      destinationBucket: frontendBucket,
      distribution,
      distributionPaths: ["/*"],
    });

    // ==========================================
    // Outputs
    // ==========================================

    this.apiUrl = new cdk.CfnOutput(this, "ApiUrl", {
      value: api.url,
      description: "API Gateway URL",
      exportName: "TiaApiUrl",
    });

    this.frontendUrl = new cdk.CfnOutput(this, "FrontendUrl", {
      value: `https://${distribution.distributionDomainName}`,
      description: "CloudFront Distribution URL",
      exportName: "TiaFrontendUrl",
    });

    new cdk.CfnOutput(this, "FrontendBucketName", {
      value: frontendBucket.bucketName,
      description: "S3 Bucket for Frontend",
      exportName: "TiaFrontendBucket",
    });

    new cdk.CfnOutput(this, "LambdaFunctionName", {
      value: backendLambda.functionName,
      description: "Lambda function name",
    });

    new cdk.CfnOutput(this, "CloudFrontDistributionId", {
      value: distribution.distributionId,
      description: "CloudFront Distribution ID",
    });

    new cdk.CfnOutput(this, "LambdaFunctionUrl", {
      value: functionUrl.url,
      description: "Lambda Function URL (direct, no 29s timeout)",
      exportName: "TiaLambdaFunctionUrl",
    });
  }
}

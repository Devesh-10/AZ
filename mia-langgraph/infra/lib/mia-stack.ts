import * as cdk from "aws-cdk-lib";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as apigateway from "aws-cdk-lib/aws-apigateway";
import * as s3 from "aws-cdk-lib/aws-s3";
import * as s3deploy from "aws-cdk-lib/aws-s3-deployment";
import * as cloudfront from "aws-cdk-lib/aws-cloudfront";
import * as origins from "aws-cdk-lib/aws-cloudfront-origins";
import * as dynamodb from "aws-cdk-lib/aws-dynamodb";
import * as iam from "aws-cdk-lib/aws-iam";
import { Construct } from "constructs";
import * as path from "path";

export class MiaLanggraphStack extends cdk.Stack {
  public readonly apiUrl: cdk.CfnOutput;
  public readonly frontendUrl: cdk.CfnOutput;

  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // ==========================================
    // DynamoDB Table for Session History
    // ==========================================

    const sessionTable = new dynamodb.Table(this, "MiaSessionTable", {
      tableName: "mia-session-history",
      partitionKey: {
        name: "session_id",
        type: dynamodb.AttributeType.STRING,
      },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      timeToLiveAttribute: "ttl",
    });

    // ==========================================
    // DynamoDB Table for LangGraph Traces & Query Cache
    // ==========================================

    const traceTable = new dynamodb.Table(this, "MiaTraceTable", {
      tableName: "mia-langgraph-traces",
      partitionKey: {
        name: "query_hash",
        type: dynamodb.AttributeType.STRING,
      },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      timeToLiveAttribute: "ttl",
    });

    // ==========================================
    // Lambda Function (pre-built locally)
    // ==========================================
    // Note: Run scripts/build-lambda.sh before deploying

    const backendLambda = new lambda.Function(this, "MiaBackendHandler", {
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: "lambda_handler.handler",
      code: lambda.Code.fromAsset(path.join(__dirname, "../../lambda-build")),
      timeout: cdk.Duration.seconds(120),
      memorySize: 2048,
      environment: {
        AWS_REGION_NAME: "us-east-1",
        SUPERVISOR_MODEL: "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
        KPI_MODEL: "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
        ANALYST_MODEL: "us.anthropic.claude-sonnet-4-20250514-v1:0",
        VALIDATOR_MODEL: "us.anthropic.claude-3-5-haiku-20241022-v1:0",
        SESSION_TABLE_NAME: sessionTable.tableName,
        TRACE_TABLE_NAME: traceTable.tableName,
      },
      description: "MIA LangGraph Backend - Manufacturing Insight Agent",
    });

    // Grant DynamoDB permissions
    sessionTable.grantReadWriteData(backendLambda);
    traceTable.grantReadWriteData(backendLambda);

    // Grant Bedrock permissions
    backendLambda.addToRolePolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream",
        ],
        resources: ["*"],
      })
    );

    // ==========================================
    // API Gateway
    // ==========================================

    const api = new apigateway.RestApi(this, "MiaApi", {
      restApiName: "MIA LangGraph API",
      description: "Manufacturing Insight Agent API",
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

    const frontendBucket = new s3.Bucket(this, "MiaFrontendBucket", {
      bucketName: `mia-langgraph-frontend-${this.account}`,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
    });

    const originAccessIdentity = new cloudfront.OriginAccessIdentity(
      this,
      "MiaOAI"
    );
    frontendBucket.grantRead(originAccessIdentity);

    const distribution = new cloudfront.Distribution(
      this,
      "MiaFrontendDistribution",
      {
        comment: "MIA LangGraph Frontend",
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
              }
            ),
            viewerProtocolPolicy:
              cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
            cachePolicy: cloudfront.CachePolicy.CACHING_DISABLED,
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
      exportName: "MiaApiUrl",
    });

    this.frontendUrl = new cdk.CfnOutput(this, "FrontendUrl", {
      value: `https://${distribution.distributionDomainName}`,
      description: "CloudFront Distribution URL",
      exportName: "MiaFrontendUrl",
    });

    new cdk.CfnOutput(this, "FrontendBucketName", {
      value: frontendBucket.bucketName,
      description: "S3 Bucket for Frontend",
      exportName: "MiaFrontendBucket",
    });

    new cdk.CfnOutput(this, "LambdaFunctionName", {
      value: backendLambda.functionName,
      description: "Lambda function name",
    });

    new cdk.CfnOutput(this, "CloudFrontDistributionId", {
      value: distribution.distributionId,
      description: "CloudFront Distribution ID",
    });

    new cdk.CfnOutput(this, "SessionTableName", {
      value: sessionTable.tableName,
      description: "DynamoDB Session History Table",
    });

    new cdk.CfnOutput(this, "TraceTableName", {
      value: traceTable.tableName,
      description: "DynamoDB LangGraph Traces Table",
    });
  }
}

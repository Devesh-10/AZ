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

export class DsaLanggraphStack extends cdk.Stack {
  public readonly apiUrl: cdk.CfnOutput;
  public readonly frontendUrl: cdk.CfnOutput;

  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // ==========================================
    // Lambda Function (pre-built locally)
    // ==========================================

    const backendLambda = new lambda.Function(this, "DsaBackendHandler", {
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: "lambda_handler.handler",
      code: lambda.Code.fromAsset(path.join(__dirname, "../../lambda-build")),
      timeout: cdk.Duration.seconds(120),
      memorySize: 2048,
      environment: {
        AWS_REGION_NAME: "us-east-1",
        SUPERVISOR_MODEL: "us.anthropic.claude-sonnet-4-20250514-v1:0",
        KPI_MODEL: "us.anthropic.claude-sonnet-4-20250514-v1:0",
        ANALYST_MODEL: "us.anthropic.claude-opus-4-20250514-v1:0",
        VALIDATOR_MODEL: "us.anthropic.claude-3-5-haiku-20241022-v1:0",
      },
      description: "DSA LangGraph Backend - Data Strategy Agent",
    });

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

    const api = new apigateway.RestApi(this, "DsaApi", {
      restApiName: "DSA LangGraph API",
      description: "Data Strategy Agent API",
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

    api.root.addMethod("ANY", lambdaIntegration);
    api.root.addProxy({
      defaultIntegration: lambdaIntegration,
      anyMethod: true,
    });

    // ==========================================
    // S3 + CloudFront for Frontend
    // ==========================================

    const frontendBucket = new s3.Bucket(this, "DsaFrontendBucket", {
      bucketName: `dsa-langgraph-frontend-${this.account}`,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
    });

    const originAccessIdentity = new cloudfront.OriginAccessIdentity(
      this,
      "DsaOAI"
    );
    frontendBucket.grantRead(originAccessIdentity);

    const distribution = new cloudfront.Distribution(
      this,
      "DsaFrontendDistribution",
      {
        comment: "DSA LangGraph Frontend",
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
      exportName: "DsaApiUrl",
    });

    this.frontendUrl = new cdk.CfnOutput(this, "FrontendUrl", {
      value: `https://${distribution.distributionDomainName}`,
      description: "CloudFront Distribution URL",
      exportName: "DsaFrontendUrl",
    });

    new cdk.CfnOutput(this, "FrontendBucketName", {
      value: frontendBucket.bucketName,
      description: "S3 Bucket for Frontend",
      exportName: "DsaFrontendBucket",
    });

    new cdk.CfnOutput(this, "LambdaFunctionName", {
      value: backendLambda.functionName,
      description: "Lambda function name",
    });

    new cdk.CfnOutput(this, "CloudFrontDistributionId", {
      value: distribution.distributionId,
      description: "CloudFront Distribution ID",
    });
  }
}

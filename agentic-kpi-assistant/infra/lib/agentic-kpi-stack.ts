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

export interface AgenticKpiStackProps extends cdk.StackProps {
  bedrockRegion?: string;
  bedrockModelId?: string;
}

export class AgenticKpiStack extends cdk.Stack {
  public readonly apiUrl: cdk.CfnOutput;
  public readonly frontendUrl: cdk.CfnOutput;

  constructor(scope: Construct, id: string, props?: AgenticKpiStackProps) {
    super(scope, id, props);

    const bedrockRegion = props?.bedrockRegion || "us-east-1";
    const bedrockModelId =
      props?.bedrockModelId || "anthropic.claude-3-5-sonnet-20241022-v2:0";

    // ==========================================
    // Lambda Function
    // ==========================================

    const backendLambda = new lambda.Function(this, "AgenticKpiHandler", {
      runtime: lambda.Runtime.NODEJS_20_X,
      handler: "lambda.handler",
      code: lambda.Code.fromAsset(path.join(__dirname, "../../backend"), {
        exclude: ["src", "*.ts", "tsconfig.json", ".aws-sam"],
      }),
      timeout: cdk.Duration.seconds(120),
      memorySize: 1024,
      environment: {
        BEDROCK_REGION: bedrockRegion,
        BEDROCK_MODEL_ID: bedrockModelId,
        NODE_OPTIONS: "--enable-source-maps",
      },
      description: "Agentic KPI Assistant Backend",
    });

    // Grant Bedrock permissions
    backendLambda.addToRolePolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream",
        ],
        resources: [
          `arn:aws:bedrock:${bedrockRegion}::foundation-model/${bedrockModelId}`,
          `arn:aws:bedrock:${bedrockRegion}::foundation-model/anthropic.claude-*`,
        ],
      })
    );

    // ==========================================
    // API Gateway
    // ==========================================

    const api = new apigateway.RestApi(this, "AgenticKpiApi", {
      restApiName: "Agentic KPI Assistant API",
      description: "API for the Agentic KPI Assistant",
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

    const lambdaIntegration = new apigateway.LambdaIntegration(backendLambda, {
      requestTemplates: { "application/json": '{ "statusCode": "200" }' },
    });

    // API routes
    const apiResource = api.root.addResource("api");

    // /api/chat
    const chatResource = apiResource.addResource("chat");

    // POST /api/chat/query
    const queryResource = chatResource.addResource("query");
    queryResource.addMethod("POST", lambdaIntegration);

    // GET /api/chat/telemetry/{sessionId}
    const telemetryResource = chatResource.addResource("telemetry");
    const sessionResource = telemetryResource.addResource("{sessionId}");
    sessionResource.addMethod("GET", lambdaIntegration);

    // /api/meta
    const metaResource = apiResource.addResource("meta");

    // GET /api/meta/schema
    const schemaResource = metaResource.addResource("schema");
    schemaResource.addMethod("GET", lambdaIntegration);

    // GET /api/meta/knowledge-graph
    const kgResource = metaResource.addResource("knowledge-graph");
    kgResource.addMethod("GET", lambdaIntegration);

    // GET /api/health
    const healthResource = apiResource.addResource("health");
    healthResource.addMethod("GET", lambdaIntegration);

    // ==========================================
    // S3 + CloudFront for Frontend (Optional)
    // ==========================================

    const frontendBucket = new s3.Bucket(this, "FrontendBucket", {
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
    });

    const originAccessIdentity = new cloudfront.OriginAccessIdentity(
      this,
      "OAI"
    );
    frontendBucket.grantRead(originAccessIdentity);

    const distribution = new cloudfront.Distribution(
      this,
      "FrontendDistribution",
      {
        defaultBehavior: {
          origin: new origins.S3Origin(frontendBucket, {
            originAccessIdentity,
          }),
          viewerProtocolPolicy:
            cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
        },
        defaultRootObject: "index.html",
        errorResponses: [
          {
            httpStatus: 404,
            responseHttpStatus: 200,
            responsePagePath: "/index.html",
          },
        ],
      }
    );

    // ==========================================
    // Outputs
    // ==========================================

    this.apiUrl = new cdk.CfnOutput(this, "ApiUrl", {
      value: api.url,
      description: "API Gateway URL",
      exportName: "AgenticKpiApiUrl",
    });

    this.frontendUrl = new cdk.CfnOutput(this, "FrontendUrl", {
      value: `https://${distribution.distributionDomainName}`,
      description: "CloudFront Distribution URL for Frontend",
      exportName: "AgenticKpiFrontendUrl",
    });

    new cdk.CfnOutput(this, "FrontendBucketName", {
      value: frontendBucket.bucketName,
      description: "S3 Bucket for Frontend deployment",
      exportName: "AgenticKpiFrontendBucket",
    });

    new cdk.CfnOutput(this, "LambdaFunctionName", {
      value: backendLambda.functionName,
      description: "Lambda function name",
    });
  }
}

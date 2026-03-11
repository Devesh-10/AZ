data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

locals {
  account_id = data.aws_caller_identity.current.account_id
  region     = data.aws_region.current.name
}

################################################################################
# ECS Task Execution Role (used by ECS agent to pull images, write logs)
################################################################################

resource "aws_iam_role" "ecs_execution" {
  name = "${var.name_prefix}-ecs-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      }
    }]
  })

  tags = {
    Name = "${var.name_prefix}-ecs-execution-role"
  }
}

resource "aws_iam_role_policy_attachment" "ecs_execution_default" {
  role       = aws_iam_role.ecs_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Allow pulling secrets from Secrets Manager at task startup
resource "aws_iam_role_policy" "ecs_execution_secrets" {
  name = "${var.name_prefix}-ecs-execution-secrets"
  role = aws_iam_role.ecs_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid    = "AllowSecretsManager"
      Effect = "Allow"
      Action = [
        "secretsmanager:GetSecretValue"
      ]
      Resource = "arn:aws:secretsmanager:${local.region}:${local.account_id}:secret:${var.name_prefix}/*"
    }]
  })
}

################################################################################
# ECS Task Role (used by application containers at runtime)
################################################################################

resource "aws_iam_role" "ecs_task" {
  name = "${var.name_prefix}-ecs-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      }
    }]
  })

  tags = {
    Name = "${var.name_prefix}-ecs-task-role"
  }
}

# DynamoDB access
resource "aws_iam_role_policy" "task_dynamodb" {
  name = "${var.name_prefix}-task-dynamodb"
  role = aws_iam_role.ecs_task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid    = "AllowDynamoDB"
      Effect = "Allow"
      Action = [
        "dynamodb:PutItem",
        "dynamodb:GetItem",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem",
        "dynamodb:Query",
        "dynamodb:Scan",
        "dynamodb:BatchGetItem",
        "dynamodb:BatchWriteItem"
      ]
      Resource = [
        "arn:aws:dynamodb:${local.region}:${local.account_id}:table/${var.name_prefix}-*",
        "arn:aws:dynamodb:${local.region}:${local.account_id}:table/${var.name_prefix}-*/index/*"
      ]
    }]
  })
}

# S3 access
resource "aws_iam_role_policy" "task_s3" {
  name = "${var.name_prefix}-task-s3"
  role = aws_iam_role.ecs_task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid    = "AllowS3"
      Effect = "Allow"
      Action = [
        "s3:GetObject",
        "s3:PutObject",
        "s3:ListBucket",
        "s3:DeleteObject"
      ]
      Resource = [
        "arn:aws:s3:::${var.name_prefix}-*",
        "arn:aws:s3:::${var.name_prefix}-*/*"
      ]
    }]
  })
}

# Bedrock access (LLM inference + embeddings)
resource "aws_iam_role_policy" "task_bedrock" {
  name = "${var.name_prefix}-task-bedrock"
  role = aws_iam_role.ecs_task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid    = "AllowBedrock"
      Effect = "Allow"
      Action = [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream",
        "bedrock:ListFoundationModels",
        "bedrock:GetFoundationModel"
      ]
      Resource = [
        "arn:aws:bedrock:${local.region}::foundation-model/us.anthropic.*",
        "arn:aws:bedrock:${local.region}::foundation-model/cohere.*"
      ]
    }]
  })
}

# OpenSearch access
resource "aws_iam_role_policy" "task_opensearch" {
  name = "${var.name_prefix}-task-opensearch"
  role = aws_iam_role.ecs_task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid    = "AllowOpenSearch"
      Effect = "Allow"
      Action = [
        "es:ESHttpGet",
        "es:ESHttpPost",
        "es:ESHttpPut",
        "es:ESHttpDelete"
      ]
      Resource = "arn:aws:es:${local.region}:${local.account_id}:domain/${var.name_prefix}-*/*"
    }]
  })
}

# Secrets Manager runtime access
resource "aws_iam_role_policy" "task_secrets" {
  name = "${var.name_prefix}-task-secrets"
  role = aws_iam_role.ecs_task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid    = "AllowSecretsManager"
      Effect = "Allow"
      Action = [
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret"
      ]
      Resource = "arn:aws:secretsmanager:${local.region}:${local.account_id}:secret:${var.name_prefix}/*"
    }]
  })
}

# CloudWatch Logs
resource "aws_iam_role_policy" "task_logs" {
  name = "${var.name_prefix}-task-logs"
  role = aws_iam_role.ecs_task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid    = "AllowCloudWatchLogs"
      Effect = "Allow"
      Action = [
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ]
      Resource = "arn:aws:logs:${local.region}:${local.account_id}:log-group:/ecs/${var.name_prefix}/*:*"
    }]
  })
}

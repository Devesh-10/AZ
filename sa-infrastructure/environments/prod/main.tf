################################################################################
# Locals
################################################################################

locals {
  name_prefix = "${var.project_name}-${var.environment}"
}

################################################################################
# Networking
################################################################################

module "vpc" {
  source = "../../modules/vpc"

  name_prefix        = local.name_prefix
  vpc_cidr           = var.vpc_cidr
  availability_zones = var.availability_zones
  single_nat_gateway = var.single_nat_gateway
  aws_region         = var.aws_region
}

module "security_groups" {
  source = "../../modules/security-groups"

  name_prefix = local.name_prefix
  vpc_id      = module.vpc.vpc_id
}

################################################################################
# IAM
################################################################################

module "iam" {
  source = "../../modules/iam"

  name_prefix = local.name_prefix
}

################################################################################
# Container Registry
################################################################################

module "ecr" {
  source = "../../modules/ecr"

  name_prefix      = local.name_prefix
  repository_names = ["frontend", "backend", "agents"]
  force_delete     = var.environment == "dev" ? true : false
}

################################################################################
# Storage
################################################################################

module "s3" {
  source = "../../modules/s3"

  name_prefix   = local.name_prefix
  bucket_suffix = "csv-data"
}

module "dynamodb" {
  source = "../../modules/dynamodb"

  name_prefix                   = local.name_prefix
  billing_mode                  = "PAY_PER_REQUEST"
  enable_point_in_time_recovery = var.environment != "dev"
}

################################################################################
# Secrets
################################################################################

module "secrets_manager" {
  source = "../../modules/secrets-manager"

  name_prefix = local.name_prefix
  secret_names = [
    "snowflake-credentials",
    "langsmith-api-key",
    "azure-ad-config"
  ]
}

################################################################################
# Search
################################################################################

module "opensearch" {
  source = "../../modules/opensearch"

  name_prefix        = local.name_prefix
  instance_type      = var.opensearch_instance_type
  instance_count     = var.opensearch_instance_count
  ebs_volume_size    = var.opensearch_ebs_volume_size
  private_subnet_ids = module.vpc.private_subnet_ids
  security_group_id  = module.security_groups.opensearch_security_group_id
}

################################################################################
# Monitoring
################################################################################

module "cloudwatch" {
  source = "../../modules/cloudwatch"

  name_prefix        = local.name_prefix
  ecs_service_names  = ["frontend", "backend", "agents"]
  ecs_cluster_name   = module.ecs_cluster.cluster_name
  log_retention_days = var.log_retention_days
}

################################################################################
# Load Balancer
################################################################################

module "alb" {
  source = "../../modules/alb"

  name_prefix                = local.name_prefix
  vpc_id                     = module.vpc.vpc_id
  public_subnet_ids          = module.vpc.public_subnet_ids
  security_group_id          = module.security_groups.alb_security_group_id
  enable_deletion_protection = var.enable_deletion_protection
}

################################################################################
# ECS Cluster
################################################################################

module "ecs_cluster" {
  source = "../../modules/ecs-cluster"

  name_prefix               = local.name_prefix
  enable_container_insights = var.enable_container_insights
}

################################################################################
# ECS Services
################################################################################

module "frontend" {
  source = "../../modules/ecs-service"

  name_prefix        = local.name_prefix
  service_name       = "frontend"
  cluster_id         = module.ecs_cluster.cluster_id
  cluster_name       = module.ecs_cluster.cluster_name
  cpu                = var.frontend_cpu
  memory             = var.frontend_memory
  desired_count      = var.frontend_desired_count
  container_image    = "${module.ecr.repository_urls["frontend"]}:latest"
  container_port     = 80
  execution_role_arn = module.iam.ecs_execution_role_arn
  task_role_arn      = module.iam.ecs_task_role_arn
  private_subnet_ids = module.vpc.private_subnet_ids
  security_group_id  = module.security_groups.ecs_security_group_id
  target_group_arn   = module.alb.frontend_target_group_arn
  log_group_name     = module.cloudwatch.log_group_names["frontend"]
  aws_region         = var.aws_region
  enable_autoscaling = var.enable_autoscaling
  min_capacity       = var.frontend_desired_count
  max_capacity       = var.frontend_desired_count * 3

  environment_variables = {
    NODE_ENV = var.environment
    API_URL  = "http://${module.alb.alb_dns_name}/api"
    WS_URL   = module.api_gateway.websocket_stage_invoke_url
  }
}

module "backend" {
  source = "../../modules/ecs-service"

  name_prefix        = local.name_prefix
  service_name       = "backend"
  cluster_id         = module.ecs_cluster.cluster_id
  cluster_name       = module.ecs_cluster.cluster_name
  cpu                = var.backend_cpu
  memory             = var.backend_memory
  desired_count      = var.backend_desired_count
  container_image    = "${module.ecr.repository_urls["backend"]}:latest"
  container_port     = 8000
  execution_role_arn = module.iam.ecs_execution_role_arn
  task_role_arn      = module.iam.ecs_task_role_arn
  private_subnet_ids = module.vpc.private_subnet_ids
  security_group_id  = module.security_groups.ecs_security_group_id
  target_group_arn   = module.alb.backend_target_group_arn
  log_group_name     = module.cloudwatch.log_group_names["backend"]
  aws_region         = var.aws_region
  enable_autoscaling = var.enable_autoscaling
  enable_exec        = var.environment == "dev"
  min_capacity       = var.backend_desired_count
  max_capacity       = var.backend_desired_count * 3

  health_check_command = "curl -f http://localhost:8000/health || exit 1"

  environment_variables = {
    ENVIRONMENT                = var.environment
    DYNAMODB_SESSION_TABLE     = module.dynamodb.session_turns_table_name
    DYNAMODB_CHAT_TABLE        = module.dynamodb.chat_sessions_table_name
    DYNAMODB_CHECKPOINTS_TABLE = module.dynamodb.checkpoints_table_name
    S3_DATA_BUCKET             = module.s3.bucket_id
    OPENSEARCH_ENDPOINT        = "https://${module.opensearch.domain_endpoint}"
    AWS_DEFAULT_REGION         = var.aws_region
  }

  secret_arns = {
    SNOWFLAKE_CREDENTIALS = module.secrets_manager.secret_arns["snowflake-credentials"]
    LANGSMITH_API_KEY     = module.secrets_manager.secret_arns["langsmith-api-key"]
    AZURE_AD_CONFIG       = module.secrets_manager.secret_arns["azure-ad-config"]
  }
}

module "agents" {
  source = "../../modules/ecs-service"

  name_prefix        = local.name_prefix
  service_name       = "agents"
  cluster_id         = module.ecs_cluster.cluster_id
  cluster_name       = module.ecs_cluster.cluster_name
  cpu                = var.agents_cpu
  memory             = var.agents_memory
  desired_count      = var.agents_desired_count
  container_image    = "${module.ecr.repository_urls["agents"]}:latest"
  container_port     = 8001
  execution_role_arn = module.iam.ecs_execution_role_arn
  task_role_arn      = module.iam.ecs_task_role_arn
  private_subnet_ids = module.vpc.private_subnet_ids
  security_group_id  = module.security_groups.ecs_security_group_id
  target_group_arn   = module.alb.agents_target_group_arn
  log_group_name     = module.cloudwatch.log_group_names["agents"]
  aws_region         = var.aws_region
  enable_autoscaling = var.enable_autoscaling
  enable_exec        = var.environment == "dev"
  min_capacity       = var.agents_desired_count
  max_capacity       = var.agents_desired_count * 3

  health_check_command      = "curl -f http://localhost:8001/health || exit 1"
  health_check_start_period = 120

  environment_variables = {
    ENVIRONMENT                = var.environment
    DYNAMODB_SESSION_TABLE     = module.dynamodb.session_turns_table_name
    DYNAMODB_CHAT_TABLE        = module.dynamodb.chat_sessions_table_name
    DYNAMODB_CHECKPOINTS_TABLE = module.dynamodb.checkpoints_table_name
    S3_DATA_BUCKET             = module.s3.bucket_id
    OPENSEARCH_ENDPOINT        = "https://${module.opensearch.domain_endpoint}"
    BEDROCK_SUPERVISOR_MODEL   = "us.anthropic.claude-sonnet-4-5-20251001-v1:0"
    BEDROCK_ANALYST_MODEL      = "us.anthropic.claude-opus-4-6-20250501-v1:0"
    BEDROCK_EMBEDDING_MODEL    = "cohere.embed-english-v3"
    AWS_DEFAULT_REGION         = var.aws_region
  }

  secret_arns = {
    SNOWFLAKE_CREDENTIALS = module.secrets_manager.secret_arns["snowflake-credentials"]
    LANGSMITH_API_KEY     = module.secrets_manager.secret_arns["langsmith-api-key"]
  }
}

################################################################################
# API Gateway (WebSocket)
################################################################################

module "api_gateway" {
  source = "../../modules/api-gateway"

  name_prefix     = local.name_prefix
  backend_alb_dns = module.alb.alb_dns_name
  backend_port    = 8000
  stage_name      = var.environment
}

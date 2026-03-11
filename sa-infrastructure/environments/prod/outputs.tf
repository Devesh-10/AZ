output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = module.alb.alb_dns_name
}

output "websocket_endpoint" {
  description = "WebSocket API Gateway endpoint"
  value       = module.api_gateway.websocket_stage_invoke_url
}

output "ecr_repository_urls" {
  description = "ECR repository URLs for CI/CD"
  value       = module.ecr.repository_urls
}

output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = module.ecs_cluster.cluster_name
}

output "opensearch_endpoint" {
  description = "OpenSearch domain endpoint"
  value       = module.opensearch.domain_endpoint
}

output "s3_bucket_name" {
  description = "CSV data S3 bucket name"
  value       = module.s3.bucket_id
}

output "dynamodb_tables" {
  description = "DynamoDB table names"
  value = {
    session_turns = module.dynamodb.session_turns_table_name
    chat_sessions = module.dynamodb.chat_sessions_table_name
    checkpoints   = module.dynamodb.checkpoints_table_name
  }
}

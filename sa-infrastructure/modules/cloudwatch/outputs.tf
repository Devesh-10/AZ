output "log_group_names" {
  description = "Map of service name to CloudWatch log group name"
  value       = { for name, lg in aws_cloudwatch_log_group.ecs_services : name => lg.name }
}

output "log_group_arns" {
  description = "Map of service name to CloudWatch log group ARN"
  value       = { for name, lg in aws_cloudwatch_log_group.ecs_services : name => lg.arn }
}

output "alb_log_group_name" {
  description = "ALB CloudWatch log group name"
  value       = aws_cloudwatch_log_group.alb.name
}

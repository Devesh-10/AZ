variable "name_prefix" {
  description = "Prefix for all resource names"
  type        = string
}

variable "service_name" {
  description = "Name of the ECS service (e.g., frontend, backend, agents)"
  type        = string
}

variable "cluster_id" {
  description = "ID of the ECS cluster"
  type        = string
}

variable "cluster_name" {
  description = "Name of the ECS cluster (for autoscaling resource ID)"
  type        = string
}

variable "cpu" {
  description = "CPU units for the task (1 vCPU = 1024)"
  type        = number

  validation {
    condition     = contains([256, 512, 1024, 2048, 4096], var.cpu)
    error_message = "CPU must be a valid Fargate value: 256, 512, 1024, 2048, or 4096."
  }
}

variable "memory" {
  description = "Memory in MiB for the task"
  type        = number
}

variable "desired_count" {
  description = "Desired number of running tasks"
  type        = number
  default     = 1
}

variable "container_image" {
  description = "Docker image URI (ECR repository URL with tag)"
  type        = string
}

variable "container_port" {
  description = "Port the container listens on"
  type        = number
}

variable "execution_role_arn" {
  description = "ARN of the ECS task execution role"
  type        = string
}

variable "task_role_arn" {
  description = "ARN of the ECS task role"
  type        = string
}

variable "private_subnet_ids" {
  description = "Private subnet IDs for Fargate tasks"
  type        = list(string)
}

variable "security_group_id" {
  description = "Security group ID for the ECS service"
  type        = string
}

variable "target_group_arn" {
  description = "ALB target group ARN for service registration"
  type        = string
}

variable "log_group_name" {
  description = "CloudWatch log group name for container logs"
  type        = string
}

variable "aws_region" {
  description = "AWS region for CloudWatch log configuration"
  type        = string
}

variable "environment_variables" {
  description = "Map of environment variables for the container"
  type        = map(string)
  default     = {}
}

variable "secret_arns" {
  description = "Map of secret name to Secrets Manager ARN for the container"
  type        = map(string)
  default     = {}
}

variable "health_check_command" {
  description = "Shell command for container health check"
  type        = string
  default     = null
}

variable "health_check_start_period" {
  description = "Grace period in seconds before health checks start"
  type        = number
  default     = 60
}

variable "enable_exec" {
  description = "Enable ECS Exec for debugging"
  type        = bool
  default     = false
}

# Auto Scaling

variable "enable_autoscaling" {
  description = "Enable auto scaling for the service"
  type        = bool
  default     = false
}

variable "min_capacity" {
  description = "Minimum number of tasks for autoscaling"
  type        = number
  default     = 1
}

variable "max_capacity" {
  description = "Maximum number of tasks for autoscaling"
  type        = number
  default     = 10
}

variable "autoscaling_cpu_target" {
  description = "Target CPU utilization percentage for autoscaling"
  type        = number
  default     = 70
}

variable "autoscaling_memory_target" {
  description = "Target memory utilization percentage for autoscaling"
  type        = number
  default     = 80
}

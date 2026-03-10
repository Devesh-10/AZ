################################################################################
# General
################################################################################

variable "aws_region" {
  description = "AWS region to deploy to"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string

  validation {
    condition     = contains(["dev", "preprod", "prod"], var.environment)
    error_message = "Environment must be dev, preprod, or prod."
  }
}

variable "project_name" {
  description = "Project name used for tagging"
  type        = string
  default     = "mia"
}

variable "owner" {
  description = "Team or individual owning these resources"
  type        = string
}

################################################################################
# Networking
################################################################################

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
}

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
}

variable "single_nat_gateway" {
  description = "Use a single NAT Gateway (true for cost savings in non-prod)"
  type        = bool
  default     = true
}

################################################################################
# ECS Service Sizing
################################################################################

variable "frontend_desired_count" {
  description = "Number of frontend tasks"
  type        = number
}

variable "frontend_cpu" {
  description = "Frontend CPU units (1 vCPU = 1024)"
  type        = number
}

variable "frontend_memory" {
  description = "Frontend memory in MiB"
  type        = number
}

variable "backend_desired_count" {
  description = "Number of backend API tasks"
  type        = number
}

variable "backend_cpu" {
  description = "Backend CPU units"
  type        = number
}

variable "backend_memory" {
  description = "Backend memory in MiB"
  type        = number
}

variable "agents_desired_count" {
  description = "Number of LangGraph agent tasks"
  type        = number
}

variable "agents_cpu" {
  description = "Agents CPU units"
  type        = number
}

variable "agents_memory" {
  description = "Agents memory in MiB"
  type        = number
}

################################################################################
# OpenSearch
################################################################################

variable "opensearch_instance_type" {
  description = "OpenSearch instance type"
  type        = string
}

variable "opensearch_instance_count" {
  description = "Number of OpenSearch instances"
  type        = number
}

variable "opensearch_ebs_volume_size" {
  description = "EBS volume size per OpenSearch node (GB)"
  type        = number
}

################################################################################
# Feature Flags
################################################################################

variable "enable_autoscaling" {
  description = "Enable ECS auto scaling"
  type        = bool
  default     = false
}

variable "enable_container_insights" {
  description = "Enable CloudWatch Container Insights"
  type        = bool
  default     = true
}

variable "enable_deletion_protection" {
  description = "Enable deletion protection on ALB"
  type        = bool
  default     = false
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 30
}

variable "name_prefix" {
  description = "Prefix for all resource names"
  type        = string
}

variable "engine_version" {
  description = "OpenSearch engine version"
  type        = string
  default     = "OpenSearch_2.11"
}

variable "instance_type" {
  description = "OpenSearch instance type"
  type        = string
  default     = "t3.medium.search"
}

variable "instance_count" {
  description = "Number of OpenSearch instances"
  type        = number
  default     = 2

  validation {
    condition     = var.instance_count >= 1 && var.instance_count <= 10
    error_message = "Instance count must be between 1 and 10."
  }
}

variable "ebs_volume_size" {
  description = "EBS volume size in GB per node"
  type        = number
  default     = 100
}

variable "ebs_throughput" {
  description = "EBS throughput in MiB/s (gp3 only)"
  type        = number
  default     = 125
}

variable "ebs_iops" {
  description = "EBS IOPS (gp3 only)"
  type        = number
  default     = 3000
}

variable "private_subnet_ids" {
  description = "Private subnet IDs for OpenSearch VPC placement"
  type        = list(string)
}

variable "security_group_id" {
  description = "Security group ID for OpenSearch"
  type        = string
}

variable "log_retention_days" {
  description = "CloudWatch log retention for OpenSearch logs"
  type        = number
  default     = 30
}

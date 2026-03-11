variable "name_prefix" {
  description = "Prefix for all resource names"
  type        = string
}

variable "ecs_service_names" {
  description = "List of ECS service names for log groups and alarms"
  type        = list(string)
  default     = ["frontend", "backend", "agents"]
}

variable "ecs_cluster_name" {
  description = "Name of the ECS cluster (for alarm dimensions)"
  type        = string
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 30

  validation {
    condition     = contains([1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1096, 1827, 2192, 2557, 2922, 3288, 3653], var.log_retention_days)
    error_message = "Log retention days must be a valid CloudWatch retention value."
  }
}

variable "cpu_alarm_threshold" {
  description = "CPU utilization alarm threshold percentage"
  type        = number
  default     = 80
}

variable "memory_alarm_threshold" {
  description = "Memory utilization alarm threshold percentage"
  type        = number
  default     = 85
}

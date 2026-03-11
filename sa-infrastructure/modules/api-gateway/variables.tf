variable "name_prefix" {
  description = "Prefix for all resource names"
  type        = string
}

variable "backend_alb_dns" {
  description = "DNS name of the ALB for backend integration"
  type        = string
}

variable "backend_port" {
  description = "Backend service port"
  type        = number
  default     = 8000
}

variable "stage_name" {
  description = "API Gateway stage name"
  type        = string
  default     = "v1"
}

variable "throttling_burst_limit" {
  description = "Throttling burst limit"
  type        = number
  default     = 500
}

variable "throttling_rate_limit" {
  description = "Throttling rate limit"
  type        = number
  default     = 1000
}

variable "log_retention_days" {
  description = "CloudWatch log retention for API Gateway logs"
  type        = number
  default     = 30
}

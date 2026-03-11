variable "name_prefix" {
  description = "Prefix for all resource names"
  type        = string
}

variable "vpc_id" {
  description = "ID of the VPC"
  type        = string
}

variable "public_subnet_ids" {
  description = "Public subnet IDs for ALB placement"
  type        = list(string)
}

variable "security_group_id" {
  description = "Security group ID for the ALB"
  type        = string
}

variable "frontend_port" {
  description = "Port for the frontend container"
  type        = number
  default     = 80
}

variable "backend_port" {
  description = "Port for the backend container"
  type        = number
  default     = 8000
}

variable "agents_port" {
  description = "Port for the agents container"
  type        = number
  default     = 8001
}

variable "enable_deletion_protection" {
  description = "Enable ALB deletion protection"
  type        = bool
  default     = false
}

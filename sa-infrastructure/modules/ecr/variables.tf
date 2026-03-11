variable "name_prefix" {
  description = "Prefix for all resource names"
  type        = string
}

variable "repository_names" {
  description = "List of ECR repository names to create"
  type        = list(string)
  default     = ["frontend", "backend", "agents"]
}

variable "image_retention_count" {
  description = "Number of images to retain per repository"
  type        = number
  default     = 10
}

variable "force_delete" {
  description = "Force delete repository even if it contains images (use only in non-prod)"
  type        = bool
  default     = false
}

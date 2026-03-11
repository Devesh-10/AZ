variable "name_prefix" {
  description = "Prefix for all resource names"
  type        = string
}

variable "bucket_suffix" {
  description = "Suffix for the S3 bucket name"
  type        = string
  default     = "knowledge-base"
}

variable "enable_lifecycle_rules" {
  description = "Enable lifecycle rules for cost optimization"
  type        = bool
  default     = true
}

variable "name_prefix" {
  description = "Prefix for all resource names"
  type        = string
}

variable "secret_names" {
  description = "List of secret names to create"
  type        = list(string)
  default = [
    "azure-ad-client-secret",
    "langsmith-api-key",
    "snowflake-connection-string"
  ]
}

variable "recovery_window_in_days" {
  description = "Number of days before a secret can be fully deleted"
  type        = number
  default     = 7
}

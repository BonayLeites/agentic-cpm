variable "project_name" {
  type        = string
  default     = "cpm-accelerator"
  description = "Project name used as resource naming prefix"
}

variable "environment" {
  type        = string
  description = "Environment: staging or production"
}

variable "location" {
  type        = string
  default     = "japaneast"
  description = "Azure region"
}

variable "vnet_address_space" {
  type    = list(string)
  default = ["10.0.0.0/16"]
}

variable "db_admin_password" {
  type        = string
  sensitive   = true
  description = "PostgreSQL admin password"
}

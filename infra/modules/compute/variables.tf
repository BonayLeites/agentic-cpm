variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "location" {
  type = string
}

variable "resource_group_name" {
  type = string
}

variable "container_app_environment_id" {
  type = string
}

variable "database_url" {
  type      = string
  sensitive = true
}

variable "azure_ai_endpoint" {
  type      = string
  sensitive = true
}

variable "azure_ai_api_key" {
  type      = string
  sensitive = true
}

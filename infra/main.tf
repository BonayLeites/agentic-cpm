terraform {
  required_version = ">= 1.5"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.100"
    }
  }
}

provider "azurerm" {
  features {}
}

module "network" {
  source             = "./modules/network"
  project_name       = var.project_name
  environment        = var.environment
  location           = var.location
  vnet_address_space = var.vnet_address_space
}

module "database" {
  source              = "./modules/database"
  project_name        = var.project_name
  environment         = var.environment
  location            = var.location
  resource_group_name = module.network.resource_group_name
  subnet_id           = module.network.database_subnet_id
  private_dns_zone_id = module.network.private_dns_zone_id
  db_admin_password   = var.db_admin_password
}

module "ai" {
  source              = "./modules/ai"
  project_name        = var.project_name
  environment         = var.environment
  location            = var.location
  resource_group_name = module.network.resource_group_name
}

module "compute" {
  source                         = "./modules/compute"
  project_name                   = var.project_name
  environment                    = var.environment
  location                       = var.location
  resource_group_name            = module.network.resource_group_name
  container_app_environment_id   = module.network.container_app_environment_id
  database_url                   = module.database.connection_string
  azure_ai_endpoint              = module.ai.endpoint
  azure_ai_api_key               = module.ai.api_key
}

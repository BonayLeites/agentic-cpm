resource "azurerm_container_app" "backend" {
  name                         = "ca-${var.project_name}-backend-${var.environment}"
  container_app_environment_id = var.container_app_environment_id
  resource_group_name          = var.resource_group_name
  revision_mode                = "Single"

  template {
    container {
      name   = "backend"
      image  = "ghcr.io/${var.project_name}/backend:latest"
      cpu    = 0.5
      memory = "1Gi"

      env {
        name        = "DATABASE_URL"
        secret_name = "database-url"
      }
      env {
        name        = "AZURE_AI_ENDPOINT"
        secret_name = "azure-ai-endpoint"
      }
      env {
        name        = "AZURE_AI_API_KEY"
        secret_name = "azure-ai-api-key"
      }
      env {
        name  = "CORS_ORIGINS"
        value = "[\"https://${var.project_name}-frontend-${var.environment}.azurecontainerapps.io\"]"
      }
    }
  }

  ingress {
    external_enabled = true
    target_port      = 8000
    transport        = "auto"

    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }

  secret {
    name  = "database-url"
    value = var.database_url
  }
  secret {
    name  = "azure-ai-endpoint"
    value = var.azure_ai_endpoint
  }
  secret {
    name  = "azure-ai-api-key"
    value = var.azure_ai_api_key
  }

  tags = {
    project     = var.project_name
    environment = var.environment
  }
}

resource "azurerm_container_app" "frontend" {
  name                         = "ca-${var.project_name}-frontend-${var.environment}"
  container_app_environment_id = var.container_app_environment_id
  resource_group_name          = var.resource_group_name
  revision_mode                = "Single"

  template {
    container {
      name   = "frontend"
      image  = "ghcr.io/${var.project_name}/frontend:latest"
      cpu    = 0.25
      memory = "0.5Gi"

      env {
        name  = "VITE_API_URL"
        value = "https://${azurerm_container_app.backend.ingress[0].fqdn}"
      }
    }
  }

  ingress {
    external_enabled = true
    target_port      = 3000
    transport        = "auto"

    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }

  tags = {
    project     = var.project_name
    environment = var.environment
  }
}

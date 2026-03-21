# Infrastructure — Terraform (Azure)

Terraform modules that provision the Azure resources for a cloud deployment.

## What it provisions

| Module | Resources |
|--------|-----------|
| `network` | Resource Group, VNet, subnets, Container Apps Environment, Private DNS zone |
| `database` | Azure Database for PostgreSQL Flexible Server (B_Standard_B1ms) |
| `compute` | 2 Container Apps (backend + frontend) with secrets |
| `ai` | Azure Cognitive Services (OpenAI) + model deployments (gpt-4o, gpt-4o-mini) |

## Usage

```bash
cd infra

# Initialize Terraform
terraform init

# Plan with your environment
terraform plan \
  -var="environment=staging" \
  -var="db_admin_password=YOUR_SECURE_PASSWORD" \
  -var-file=environments/staging/terraform.tfvars

# Apply
terraform apply \
  -var="environment=staging" \
  -var="db_admin_password=YOUR_SECURE_PASSWORD" \
  -var-file=environments/staging/terraform.tfvars
```

## Required variables

| Variable | Description | Default |
|----------|-------------|---------|
| `environment` | `staging` or `production` | — |
| `db_admin_password` | PostgreSQL admin password (sensitive) | — |
| `project_name` | Resource naming prefix | `cpm-accelerator` |
| `location` | Azure region | `japaneast` |

## Environments

Pre-configured tfvars in `environments/`:
- `staging/terraform.tfvars`
- `production/terraform.tfvars`

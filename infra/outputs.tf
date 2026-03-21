output "backend_url" {
  value       = module.compute.backend_fqdn
  description = "URL del backend (FastAPI)"
}

output "frontend_url" {
  value       = module.compute.frontend_fqdn
  description = "URL del frontend (React)"
}

output "database_host" {
  value       = module.database.host
  sensitive   = true
  description = "Host de PostgreSQL"
}

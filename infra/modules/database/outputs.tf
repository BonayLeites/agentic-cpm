output "host" {
  value     = azurerm_postgresql_flexible_server.main.fqdn
  sensitive = true
}

output "connection_string" {
  value     = "postgresql+asyncpg://cpmadmin:${var.db_admin_password}@${azurerm_postgresql_flexible_server.main.fqdn}:5432/cpm"
  sensitive = true
}

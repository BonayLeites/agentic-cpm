output "resource_group_name" {
  value = azurerm_resource_group.main.name
}

output "database_subnet_id" {
  value = azurerm_subnet.database.id
}

output "private_dns_zone_id" {
  value = azurerm_private_dns_zone.postgres.id
}

output "container_app_environment_id" {
  value = azurerm_container_app_environment.main.id
}

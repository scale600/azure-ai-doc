# =============================================================================
# Azure SQL Server + Database (Free offer, one-per-subscription)
# =============================================================================

resource "random_password" "sql_admin" {
  length      = 20
  special     = true
  min_special = 1
  min_lower   = 1
  min_upper   = 1
  min_numeric = 1
}

resource "azurerm_mssql_server" "main" {
  name                         = local.sql_server_name
  resource_group_name          = azurerm_resource_group.main.name
  location                     = var.location
  version                      = "12.0"
  administrator_login          = "sqladmin"
  administrator_login_password = random_password.sql_admin.result
  minimum_tls_version          = "1.2"
  tags                         = var.tags
}

# Free offer database. NOTE: the Azure SQL free offer (32GB, 100k vCore-s/month,
# auto-pause after 7 days idle) is provisioned through a special "Free" SKU.
# If the provider/API rejects sku_name = "Free", create it via the portal and
# `terraform import azurerm_mssql_database.main <id>`, or fall back to
# sku_name = "Basic" / "S0". See docs/implementation-checklist.md §6.
resource "azurerm_mssql_database" "main" {
  name      = local.sql_database_name
  server_id = azurerm_mssql_server.main.id
  sku_name  = var.sql_database_sku
  tags      = var.tags
}

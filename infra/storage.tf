# =============================================================================
# Storage: single account for both the Function App platform and the document
# blob container. (A dedicated function-storage account is possible but this
# keeps the free-tier footprint minimal.)
# =============================================================================

resource "azurerm_storage_account" "main" {
  name                       = local.storage_account_name
  resource_group_name        = azurerm_resource_group.main.name
  location                   = var.location
  account_tier               = "Standard"
  account_replication_type   = "LRS"
  account_kind               = "StorageV2"
  min_tls_version            = "TLS1_2"
  https_traffic_only_enabled = true
  tags                       = var.tags
}

resource "azurerm_storage_container" "documents" {
  name                  = "documents"
  storage_account_id    = azurerm_storage_account.main.id
  container_access_type = "private"
}

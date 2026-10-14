# =============================================================================
# Key Vault + secrets + access policies
# =============================================================================

data "azurerm_client_config" "current" {}

resource "azurerm_key_vault" "main" {
  name                       = local.keyvault_name
  resource_group_name        = azurerm_resource_group.main.name
  location                   = var.location
  tenant_id                  = data.azurerm_client_config.current.tenant_id
  sku_name                   = "standard"
  soft_delete_retention_days = 7
  purge_protection_enabled   = false
  tags                       = var.tags
}

# --- secrets ---------------------------------------------------------------

resource "azurerm_key_vault_secret" "storage_connection" {
  name         = "storage-connection"
  value        = azurerm_storage_account.main.primary_connection_string
  key_vault_id = azurerm_key_vault.main.id
  depends_on   = [azurerm_key_vault_access_policy.admin]
}

resource "azurerm_key_vault_secret" "di_key" {
  name         = "di-key"
  value        = azurerm_cognitive_account.document_intelligence.primary_access_key
  key_vault_id = azurerm_key_vault.main.id
  depends_on   = [azurerm_key_vault_access_policy.admin]
}

resource "azurerm_key_vault_secret" "openai_key" {
  name         = "openai-key"
  value        = azurerm_cognitive_account.openai.primary_access_key
  key_vault_id = azurerm_key_vault.main.id
  depends_on   = [azurerm_key_vault_access_policy.admin]
}

resource "azurerm_key_vault_secret" "sql_password" {
  name         = "sql-password"
  value        = random_password.sql_admin.result
  key_vault_id = azurerm_key_vault.main.id
  depends_on   = [azurerm_key_vault_access_policy.admin]
}

resource "random_password" "api_key" {
  length      = 32
  special     = false
  min_lower   = 1
  min_upper   = 1
  min_numeric = 1
}

resource "azurerm_key_vault_secret" "api_key" {
  name         = "api-key"
  value        = random_password.api_key.result
  key_vault_id = azurerm_key_vault.main.id
  depends_on   = [azurerm_key_vault_access_policy.admin]
}

# --- access policies --------------------------------------------------------

# Current user (admin): full secret access for local dev / rotation.
resource "azurerm_key_vault_access_policy" "admin" {
  key_vault_id = azurerm_key_vault.main.id
  tenant_id    = data.azurerm_client_config.current.tenant_id
  object_id    = data.azurerm_client_config.current.object_id

  secret_permissions = ["Get", "List", "Set", "Delete", "Recover", "Backup", "Restore", "Purge"]
}

# Function App system-assigned identity: read-only secret access for KV refs.
resource "azurerm_key_vault_access_policy" "function" {
  key_vault_id = azurerm_key_vault.main.id
  tenant_id    = azurerm_linux_function_app.function.identity[0].tenant_id
  object_id    = azurerm_linux_function_app.function.identity[0].principal_id

  secret_permissions = ["Get", "List"]
}

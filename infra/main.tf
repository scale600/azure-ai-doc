# =============================================================================
# Core: resource group + naming locals
# =============================================================================

locals {
  # Short, globally-unique-safe names. unique_suffix disambiguates across tenants.
  storage_account_name       = "stidp${var.unique_suffix}"
  function_app_name          = "func-idp-${var.unique_suffix}"
  function_plan_name         = "plan-idp-${var.unique_suffix}"
  document_intelligence_name = "di-idp-${var.unique_suffix}"
  openai_name                = "oai-idp-${var.unique_suffix}"
  sql_server_name            = "sql-idp-${var.unique_suffix}"
  sql_database_name          = "idpdb"
  keyvault_name              = "kv-idp-${var.unique_suffix}"
  app_insights_name          = "appi-idp-${var.unique_suffix}"
  log_analytics_name         = "law-idp-${var.unique_suffix}"
  static_web_app_name        = "swa-idp-${var.unique_suffix}"

  resource_group_name = "idp-prototype"
}

resource "azurerm_resource_group" "main" {
  name     = local.resource_group_name
  location = var.location
  tags     = var.tags
}

# =============================================================================
# Function App (Python, Consumption plan)
# =============================================================================

resource "azurerm_service_plan" "function" {
  name                = local.function_plan_name
  resource_group_name = azurerm_resource_group.main.name
  location            = var.location
  os_type             = "Linux"
  sku_name            = "Y1" # Consumption — 1M requests + 400k GB-s free/month
  tags                = var.tags
}

resource "azurerm_linux_function_app" "function" {
  name                       = local.function_app_name
  resource_group_name        = azurerm_resource_group.main.name
  location                   = var.location
  service_plan_id            = azurerm_service_plan.function.id
  storage_account_name       = azurerm_storage_account.main.name
  storage_account_access_key = azurerm_storage_account.main.primary_access_key

  identity {
    type = "SystemAssigned"
  }

  site_config {
    application_stack {
      python_version = var.function_python_version
    }
    cors {
      allowed_origins = [
        "https://${azurerm_static_web_app.dashboard.default_host_name}",
        "https://${var.custom_domain}",
      ]
    }
  }

  app_settings = {
    "AzureWebJobsFeatureFlags"    = "EnableWorkerIndexing"
    "WEBSITE_RUN_FROM_PACKAGE"    = "1"
    "FUNCTIONS_EXTENSION_VERSION" = "~4"

    # --- non-secret config (endpoints / names) ---
    "DOCUMENT_STORAGE_CONNECTION"           = "@Microsoft.KeyVault(SecretUri=${azurerm_key_vault_secret.storage_connection.id})"
    "DOCUMENT_INTELLIGENCE_ENDPOINT"        = azurerm_cognitive_account.document_intelligence.endpoint
    "DOCUMENT_INTELLIGENCE_KEY"             = "@Microsoft.KeyVault(SecretUri=${azurerm_key_vault_secret.di_key.id})"
    "AZURE_OPENAI_ENDPOINT"                 = azurerm_cognitive_account.openai.endpoint
    "AZURE_OPENAI_KEY"                      = "@Microsoft.KeyVault(SecretUri=${azurerm_key_vault_secret.openai_key.id})"
    "AZURE_OPENAI_DEPLOYMENT"               = var.openai_model_name
    "SQL_SERVER"                            = azurerm_mssql_server.main.fully_qualified_domain_name
    "SQL_DATABASE"                          = azurerm_mssql_database.main.name
    "SQL_USER"                              = azurerm_mssql_server.main.administrator_login
    "SQL_PASSWORD"                          = "@Microsoft.KeyVault(SecretUri=${azurerm_key_vault_secret.sql_password.id})"
    "API_KEY"                               = "@Microsoft.KeyVault(SecretUri=${azurerm_key_vault_secret.api_key.id})"
    "CORS_ALLOWED_ORIGIN"                   = "https://${azurerm_static_web_app.dashboard.default_host_name},https://${var.custom_domain}"
    "APPLICATIONINSIGHTS_CONNECTION_STRING" = azurerm_application_insights.main.connection_string
  }

  tags = var.tags
}

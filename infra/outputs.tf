# =============================================================================
# Outputs — surfaced by `terraform output` for the CI/CD and local dev.
# =============================================================================

output "resource_group_name" {
  value = azurerm_resource_group.main.name
}

output "storage_account_name" {
  value = azurerm_storage_account.main.name
}

output "function_app_name" {
  value = azurerm_linux_function_app.function.name
}

output "function_app_default_hostname" {
  value = azurerm_linux_function_app.function.default_hostname
}

output "document_intelligence_endpoint" {
  value = azurerm_cognitive_account.document_intelligence.endpoint
}

output "openai_endpoint" {
  value = azurerm_cognitive_account.openai.endpoint
}

output "openai_deployment_name" {
  value = azurerm_cognitive_deployment.gpt_model.name
}

output "sql_server_fqdn" {
  value = azurerm_mssql_server.main.fully_qualified_domain_name
}

output "sql_database_name" {
  value = azurerm_mssql_database.main.name
}

output "key_vault_uri" {
  value = azurerm_key_vault.main.vault_uri
}

output "static_web_app_name" {
  value = azurerm_static_web_app.dashboard.name
}

output "static_web_app_default_hostname" {
  value = azurerm_static_web_app.dashboard.default_host_name
}

output "application_insights_connection_string" {
  value     = azurerm_application_insights.main.connection_string
  sensitive = true
}

output "custom_domain" {
  value = var.custom_domain
}

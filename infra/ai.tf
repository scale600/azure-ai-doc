# =============================================================================
# AI services: Document Intelligence (OCR) + Azure OpenAI (classification/LLM)
# =============================================================================

# Document Intelligence — F0 free tier (500 pages/month, first 2 pages/request).
resource "azurerm_cognitive_account" "document_intelligence" {
  name                  = local.document_intelligence_name
  location              = var.location
  resource_group_name   = azurerm_resource_group.main.name
  kind                  = "FormRecognizer"
  sku_name              = var.document_intelligence_sku
  custom_subdomain_name = local.document_intelligence_name
  tags                  = var.tags
}

# Azure OpenAI — S0 pay-as-you-go (no free tier).
resource "azurerm_cognitive_account" "openai" {
  name                  = local.openai_name
  location              = var.location
  resource_group_name   = azurerm_resource_group.main.name
  kind                  = "OpenAI"
  sku_name              = var.openai_sku
  custom_subdomain_name = local.openai_name
  tags                  = var.tags
}

# Deploy the chosen model. GlobalStandard uses global quota (already available
# in eastus per account review — 2000 TPM for gpt-4o-mini).
resource "azurerm_cognitive_deployment" "gpt_model" {
  name                 = var.openai_model_name
  cognitive_account_id = azurerm_cognitive_account.openai.id

  model {
    format  = "OpenAI"
    name    = var.openai_model_name
    version = var.openai_model_version
  }

  sku {
    name = var.openai_deployment_sku
  }
}

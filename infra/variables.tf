# =============================================================================
# Input variables
# =============================================================================

variable "subscription_id" {
  description = "Azure subscription ID. Falls back to the AZURE_SUBSCRIPTION_ID env var."
  type        = string
  default     = ""
}

variable "location" {
  description = "Azure region for all resources (US)."
  type        = string
  default     = "centralus"
}

variable "environment" {
  description = "Environment label used in resource names and tags."
  type        = string
  default     = "proto"
}

variable "unique_suffix" {
  description = "4-6 lowercase alphanumeric chars appended to globally-unique names (storage, keyvault, etc.)."
  type        = string
  validation {
    condition     = can(regex("^[a-z0-9]{4,6}$", var.unique_suffix))
    error_message = "unique_suffix must be 4-6 lowercase alphanumeric characters."
  }
}

variable "project_name" {
  description = "Project tag / prefix for non-unique resource names."
  type        = string
  default     = "ai-doc"
}

variable "document_intelligence_sku" {
  description = "Document Intelligence SKU. F0 = free (500 pages/month, 2 pages/request)."
  type        = string
  default     = "F0"
}

variable "openai_sku" {
  description = "Azure OpenAI SKU. S0 = pay-as-you-go (no free tier)."
  type        = string
  default     = "S0"
}

variable "openai_model_name" {
  description = "Azure OpenAI model to deploy."
  type        = string
  default     = "gpt-4o-mini"
}

variable "openai_model_version" {
  description = "Azure OpenAI model version."
  type        = string
  default     = "2024-07-18"
}

variable "openai_deployment_sku" {
  description = "Deployment SKU. GlobalStandard is available in eastus with default quota."
  type        = string
  default     = "GlobalStandard"
}

variable "sql_database_sku" {
  description = "SQL DB SKU. 'Free' uses the one-per-subscription Azure SQL free offer."
  type        = string
  default     = "Free"
}

variable "function_python_version" {
  description = "Azure Functions Python runtime version."
  type        = string
  default     = "3.11"
}

variable "static_web_app_sku" {
  description = "Static Web App SKU. Free tier supports custom domains + TLS."
  type        = string
  default     = "Free"
}

variable "custom_domain" {
  description = "Custom domain for the dashboard (managed via Cloudflare DNS)."
  type        = string
  default     = "azure-ai-doc.techcloudup.com"
}

# --- Cloudflare (OPTIONAL — manual DNS by default) ---------------------------

variable "cloudflare_api_token" {
  description = "Cloudflare API token (Zone:DNS:Edit). Empty = manual DNS."
  type        = string
  default     = ""
  sensitive   = true
}

variable "cloudflare_zone_id" {
  description = "Cloudflare zone ID for techcloudup.com (only if using automated DNS)."
  type        = string
  default     = ""
}

# --- Tags --------------------------------------------------------------------

variable "tags" {
  description = "Tags applied to all resources."
  type        = map(string)
  default = {
    project = "ai-doc"
    env     = "proto"
  }
}

terraform {
  required_version = ">= 1.5"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
    # Cloudflare is optional — only needed for automated DNS. Manual DNS is the
    # default; uncomment (and provide a token) if you want Terraform to manage it.
    # cloudflare = {
    #   source  = "cloudflare/cloudflare"
    #   version = "~> 4.0"
    # }
  }
}

provider "azurerm" {
  features {
    resource_group {
      prevent_deletion_if_contains_resources = false
    }
  }
  # The subscription is selected via `az login` / `az account set`.
  # Override per environment via: TF_VAR_subscription_id or -var-file.
  subscription_id = var.subscription_id
}

provider "random" {}

# provider "cloudflare" {
#   api_token = var.cloudflare_api_token
# }

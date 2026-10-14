# -----------------------------------------------------------------------------
# Remote state backend (recommended). Uncomment AFTER you bootstrap a storage
# account + container for state. See docs/implementation-checklist.md §4.
#
# Quick bootstrap (one-time, manual):
#   az group create --name idp-prototype-tfstate --location eastus
#   az storage account create --name stidpstate<uniq> --resource-group idp-prototype-tfstate \
#     --location eastus --sku Standard_LRS --kind StorageV2 --min-tls-version TLS1_2
#   az storage container create --name tfstate --account-name stidpstate<uniq> \
#     --auth-mode login
#
# terraform {
#   backend "azurerm" {
#     resource_group_name  = "idp-prototype-tfstate"
#     storage_account_name = "stidpstate<uniq>"
#     container_name       = "tfstate"
#     key                  = "idp-prototype.tfstate"
#   }
# }
# -----------------------------------------------------------------------------

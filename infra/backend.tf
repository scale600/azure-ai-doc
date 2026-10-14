# -----------------------------------------------------------------------------
# Remote state backend (Azure Storage). Bootstrapped in §4:
#   resource group: idp-prototype-tfstate
#   storage account: stidpstaterl01
#   container:       tfstate
# -----------------------------------------------------------------------------
terraform {
  backend "azurerm" {
    resource_group_name  = "idp-prototype-tfstate"
    storage_account_name = "stidpstaterl01"
    container_name       = "tfstate"
    key                  = "idp-prototype.tfstate"
  }
}

# =============================================================================
# Static Web App — dashboard frontend (Free tier, supports custom domains + TLS)
# =============================================================================

# NOTE: Static Web Apps has a limited region set; "eastus" is NOT supported.
# Use "eastus2" (US East 2). Other supported US regions: centralus, westus2.
resource "azurerm_static_web_app" "dashboard" {
  name                = local.static_web_app_name
  resource_group_name = azurerm_resource_group.main.name
  location            = "eastus2"
  sku_tier            = var.static_web_app_sku
  sku_size            = var.static_web_app_sku
  tags                = var.tags
}

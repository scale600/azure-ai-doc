# =============================================================================
# DNS — MANUAL by default (Cloudflare). See docs/implementation-checklist.md §7.
#
# Manual record (create in the Cloudflare dashboard for the techcloudup.com zone):
#   Type:  CNAME
#   Name:  azure-ai-doc
#   Target: <static-web-app default hostname>  (e.g. <name>.azurestaticapps.net)
#   Proxy: Proxied (orange cloud) — lets Cloudflare issue TLS + cache.
#
# OPTIONAL automated DNS (uncomment + provide cloudflare_api_token/zone_id):
#
# data "cloudflare_zone" "techcloudup" {
#   zone_id = var.cloudflare_zone_id
# }
#
# resource "cloudflare_record" "dashboard" {
#   zone_id = var.cloudflare_zone_id
#   name    = "azure-ai-doc"
#   type    = "CNAME"
#   content = azurerm_static_web_app.dashboard.default_host_name
#   proxied = true
# }
# =============================================================================

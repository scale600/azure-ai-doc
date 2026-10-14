# Implementation Checklist

Ordered, executable steps to build and deploy the IDP prototype end-to-end.
Check off each step. All resource names below assume `unique_suffix` is set
(§3); replace placeholders `<uniq>`, `<sub-id>`, `<tenant-id>` accordingly.

---

## 0. Prerequisites

- [x] Azure CLI logged in (`az login`) with the target subscription active
      (`az account set -s <sub-id>`).
- [x] Terraform ≥ 1.5 installed (`terraform version`).
- [x] GitHub CLI logged in (`gh auth login`), or use the GitHub web UI.
- [x] `gh` authenticated account has `repo` + `workflow` scopes.
- [x] A Cloudflare account with the `techcloudup.com` zone (manual DNS).

## 1. Create the GitHub repository (private)

- [ ] Create a **private** repo `azure-ai-doc`:
      ```bash
      gh repo create azure-ai-doc --private --source . --remote origin --push
      ```
- [ ] Verify the push excludes secrets:
      ```bash
      git check-ignore .env infra/terraform.tfvars web/config.js
      # → should list all three
      ```

## 2. Pick a globally-unique suffix

- [ ] Choose `unique_suffix` (4–6 lowercase alphanumerics, e.g. `rl01`).
      It disambiguates storage/keyvault/function names across all Azure tenants.

## 3. Configure the local `terraform.tfvars`

- [ ] Copy the example and set the suffix:
      ```bash
      cp infra/terraform.tfvars.example infra/terraform.tfvars
      # edit: unique_suffix = "rl01"
      ```

## 4. Bootstrap the Terraform state backend (one-time)

Terraform state should be remote (PRD §12). Create a storage account + container
for it **before** first `terraform init`:

- [ ] Create a dedicated resource group and storage account:
      ```bash
      az group create --name idp-prototype-tfstate --location eastus
      az storage account create --name stidpstate<uniq> --resource-group idp-prototype-tfstate \
        --location eastus --sku Standard_LRS --kind StorageV2 --min-tls-version TLS1_2
      az storage container create --name tfstate --account-name stidpstate<uniq> --auth-mode login
      ```
- [ ] Uncomment the `backend "azurerm"` block in `infra/backend.tf` and set the
      storage account name + `key`.

## 5. Set up Azure OIDC for GitHub Actions

GitHub Actions authenticates to Azure without secrets using OIDC federated
credentials (PRD §12). One-time setup:

- [ ] Create a service principal:
      ```bash
      az ad sp create-for-rbac --name "gh-idp-prototype" --role Contributor \
        --scopes /subscriptions/<sub-id> --sdk-auth
      ```
      Save the JSON (contains `appId`, `tenant`).
- [ ] Create the app registration's federated credential (or use
      `azure/actions/github-oidc`). The simplest path: add federated credentials
      in the portal (Microsoft Entra → App registrations → `<sp>` →
      Certificates & secrets → Federated credentials) for:
      - `repo:scale600/azure-ai-doc:pull_request` (plan)
      - `repo:scale600/azure-ai-doc:ref:refs/heads/main` (apply/deploy)
- [ ] Grant the service principal `User Access Administrator` or use a separate
      principal for Key Vault if you later need role-based access (optional).

## 6. Add GitHub Secrets & Variables

Repo → Settings → Secrets and variables → Actions.

**Secrets:**
| Name | Value |
|---|---|
| `AZURE_CLIENT_ID` | service principal `appId` |
| `AZURE_TENANT_ID` | `<tenant-id>` |
| `AZURE_SUBSCRIPTION_ID` | `<sub-id>` |
| `TF_VAR_UNIQUE_SUFFIX` | the suffix from §2 (e.g. `rl01`) |
| `AZURE_STATIC_WEB_APPS_API_TOKEN` | from §11 (filled after apply) |
| `API_KEY` | dashboard API key from Key Vault (filled after §10) |

**Variables:**
| Name | Value |
|---|---|
| `FUNCTION_APP_NAME` | `func-idp-<uniq>` (from `terraform output`) |
| `FUNCTION_APP_URL` | `https://func-idp-<uniq>.azurewebsites.net` |

## 7. Run Terraform (local first, then CI)

- [ ] `cd infra && terraform init && terraform plan`
- [ ] Review the plan (resource group `idp-prototype`, region `eastus`,
      Document Intelligence F0, OpenAI S0 + `gpt-4o-mini` GlobalStandard
      deployment, SQL Free, SWA Free).
- [ ] `terraform apply`
- [ ] Record outputs:
      ```bash
      terraform output
      ```

## 8. Apply the SQL schema

- [ ] Create the tables from `src/schema.sql` against the new database
      (`sql-idp-<uniq>`, database `idpdb`). Use Azure Data Studio, `sqlcmd`,
      or the Azure SQL Query Editor (portal). Requires the SQL admin password
      from Key Vault secret `sql-password`.

## 9. Configure Function App CORS

The dashboard (Static Web App) calls the Function App cross-origin.

- [ ] ```bash
      az functionapp cors add -g idp-prototype -n func-idp-<uniq> \
        --allowed-origins "https://swa-idp-<uniq>.azurestaticapps.net" \
                          "https://azure-ai-doc.techcloudup.com"
      ```

## 10. Retrieve the dashboard API key

- [ ] Read the generated API key from Key Vault:
      ```bash
      az keyvault secret show --vault-name kv-idp-<uniq> --name api-key \
        --query value -o tsv
      ```
- [ ] Store it as the `API_KEY` GitHub secret (used to inject `web/config.js`
      at deploy time).

## 11. Get the Static Web App deployment token

- [ ] ```bash
      az staticwebapp secrets list --name swa-idp-<uniq> --resource-group idp-prototype \
        --query "properties.apiKey" -o tsv
      ```
- [ ] Store it as `AZURE_STATIC_WEB_APPS_API_TOKEN`.

## 12. Deploy via CI/CD (or manually)

- [ ] Push to `main` (or open a PR first to see `terraform plan`).
      The workflows run: `terraform apply` → `deploy-function` → `deploy-web`.
- [ ] Manual fallback (if not using CI yet):
      ```bash
      # function
      cd src && pip install -r requirements.txt --target=".python_packages/lib/site-packages"
      cd .. && func azure functionapp publish func-idp-<uniq>
      # web — use the SWA CLI or az staticwebapp
      ```

## 13. Configure the custom domain (Cloudflare DNS, manual)

- [ ] In Cloudflare (zone `techcloudup.com`), add a CNAME:
      | Type | Name | Target | Proxy |
      |---|---|---|---|
      | CNAME | `azure-ai-doc` | `swa-idp-<uniq>.azurestaticapps.net` | Proxied |
- [ ] Add the custom domain to the Static Web App:
      ```bash
      az staticwebapp hostname set --name swa-idp-<uniq> --resource-group idp-prototype \
        --hostname azure-ai-doc.techcloudup.com
      ```
- [ ] Wait for validation/TLS (Cloudflare proxied → use "Cloudflare" for the
      SSL mode if asked; otherwise switch the record to DNS-only for validation,
      then back to proxied).

## 14. End-to-end smoke test

- [ ] Upload a 1-page synthetic KYC image (or PDF) via the dashboard.
- [ ] Observe: `UPLOADED → PROCESSING → COMPLETED` with summary, classification,
      key fields, and confidence.
- [ ] Upload a 3-page PDF → expect immediate `413` rejection.
- [ ] Upload a 6MB file → expect `413`.
- [ ] Call `/api/health` → `{"status":"ok"}`.
- [ ] Call `/api/documents` without `x-api-key` → `401`.

## 15. Verify observability

- [ ] Check Application Insights for function traces, token usage, and errors.

---

**Done criteria**: a document uploaded through `azure-ai-doc.techcloudup.com`
is processed end-to-end within 60 seconds, results are visible on the dashboard,
and all secrets live in Key Vault / GitHub Secrets — none in the repo.

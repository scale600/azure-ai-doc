# Deployment & Operations (Runbook)

## Deploy paths

Two equivalent paths:

1. **CI/CD (preferred)** — push to `main` triggers:
   - `terraform-apply.yml` → provisions/changes infrastructure
   - `deploy-function.yml` → zips and deploys `src/` to the Function App
   - `deploy-web.yml` → injects `web/config.js` and uploads to Static Web App
2. **Local/manual** — `terraform apply` + `func azure functionapp publish` +
   `az staticwebapp` CLI (see `implementation-checklist.md` §12).

## Prerequisites

- `infra/terraform.tfvars` with `unique_suffix` set.
- Remote state backend bootstrapped (`infra/backend.tf` uncommented).
- GitHub Secrets/Variables configured (see checklist §5–§6).

## Common operations

### Apply infrastructure changes
```bash
cd infra && terraform plan && terraform apply
```

### Redeploy the Function App manually
```bash
cd src
pip install -r requirements.txt --target=".python_packages/lib/site-packages"
func azure functionapp publish func-idp-<uniq>
```

### Read a Key Vault secret
```bash
az keyvault secret show --vault-name kv-idp-<uniq> --name api-key --query value -o tsv
```

## Troubleshooting

| Symptom | Likely cause | Action |
|---|---|---|
| Blob trigger not firing | Event source misconfigured | Check the Function App's trigger config + `DOCUMENT_STORAGE_CONNECTION`; verify the container is `documents` |
| `401 unauthorized` from dashboard | `API_KEY` mismatch | Confirm `web/config.js` key equals Key Vault `api-key` |
| CORS error in browser | Origin not allowed | `az functionapp cors add` (checklist §9) |
| Function fails with `pyodbc` error | ODBC driver missing | Ensure `ODBC Driver 18 for SQL Server` is present (present in Linux runtime); verify SQL password/connection |
| OpenAI `404` / `429` | Wrong deployment name / quota | Verify deployment `gpt-4o-mini` exists and GlobalStandard quota is not exhausted |
| Document Intelligence `400` | >2 pages or >4MB | F0 limit — reject at upload, guide PDF splitting |
| SQL connection refused | Free DB auto-paused | The free offer auto-pauses after 7 days idle; reconnect wakes it (first request may be slow) |

## Rollback

- **Infra**: `git revert` the Terraform change → `terraform apply`.
- **Function**: redeploy the previous commit (`deploy-function.yml`).
- **Web**: redeploy the previous commit (`deploy-web.yml`).

## Data retention

- Source blobs: retained 30 days after the operating period, then delete.
- Audit/processing history: retained 90 days.
- No raw PII stored (see `security.md`).

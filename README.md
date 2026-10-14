# Azure AI Document Processing (IDP) — Service Prototype

An Azure-based, event-driven pipeline that classifies, extracts, and summarizes
financial documents (KYC, loan, service applications) using **Document
Intelligence** (OCR) + **Azure OpenAI** (LLM), deployed with **Terraform** and
**GitHub Actions**, and served by a **Static Web App** dashboard on
`azure-ai-doc.techcloudup.com`.

> **Status**: proposal → scaffold. Infrastructure, code, and CI/CD are generated
> but **not yet deployed**. Follow `docs/implementation-checklist.md` to build.

## Architecture at a glance

```
Upload ─► Functions HTTP API ─► Blob Storage ─(trigger)─► Functions
                                                            ├─ Document Intelligence (F0)
                                                            ├─ Azure OpenAI (gpt-4o-mini)
                                                            └─ Azure SQL (Free)
Dashboard (Static Web App) ◄── HTTPS + x-api-key ── HTTP API
Secrets: Key Vault + Managed Identity    Observability: App Insights
```

## Repository layout

```
├── PRD.md                      # Product requirements (authoritative)
├── docs/
│   ├── implementation-checklist.md  # ★ ordered build steps
│   ├── architecture.md         # components + ADRs
│   ├── deployment.md           # runbook / ops
│   ├── security.md             # secrets / auth / PII
│   ├── api-spec.md             # API + OpenAPI
│   └── data-model.md           # SQL schema
├── infra/                      # Terraform (eastus, idp-prototype RG)
├── src/                        # Azure Functions (Python 3.11)
├── web/                        # Static Web App dashboard
└── .github/workflows/          # terraform plan/apply + function/web deploy
```

## Quick start

```bash
# 1. Configure
cp infra/terraform.tfvars.example infra/terraform.tfvars   # set unique_suffix

# 2. Bootstrap remote state (one-time) — see checklist §4

# 3. Provision infrastructure
cd infra && terraform init && terraform plan && terraform apply

# 4. Apply schema, set CORS, deploy — see checklist §8–§14
```

Full step-by-step: **`docs/implementation-checklist.md`**.

## Key decisions

- **Dashboard on Static Web App (Free)**, not App Service F1 — F1 cannot use
  custom domains/TLS; SWA Free can.
- **Azure OpenAI `gpt-4o-mini` (GlobalStandard, `eastus`)** — pay-as-you-go, the
  only billable service.
- **Everything else free tier** — Document Intelligence F0, Functions
  Consumption, Azure SQL Free, SWA Free.
- **Manual Cloudflare DNS** for `azure-ai-doc.techcloudup.com`.

## Security

Secrets in Key Vault, accessed via Managed Identity; CI/CD uses OIDC; synthetic
data only; PII masked before storage. See `docs/security.md`.

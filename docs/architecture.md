# Architecture

## Overview

Event-driven document processing pipeline on Azure, deployed with Terraform,
operated with a serverless Functions backend and a Static Web App dashboard.

```text
                       ┌──────────────────────────────┐
                       │  Static Web App (dashboard)  │
                       │  azure-ai-doc.techcloudup.com│
                       └──────────────┬───────────────┘
                                      │ HTTPS (x-api-key)
                                      ▼
[Upload] ──► [Azure Functions HTTP API] ──► [Blob Storage `documents`]
                                              │ Blob Trigger
                                              ▼
                       ┌──────────────────────────────────────┐
                       │ Azure Functions (Consumption, Python) │
                       │  ① Document Intelligence (F0) — OCR   │
                       │  ② Azure OpenAI (S0, gpt-4o-mini)     │
                       │  ③ Azure SQL (Free) — persist          │
                       └──────────────────────────────────────┘
        Secrets: Key Vault (+ Managed Identity)   |   Observability: App Insights
```

## Components

| Component | SKU / tier | Purpose |
|---|---|---|
| Blob Storage | Standard LRS | Source document storage (`documents` container) |
| Azure Functions | Consumption (Y1) | HTTP API + Blob trigger processing pipeline |
| Document Intelligence | F0 | OCR + field extraction |
| Azure OpenAI | S0 (pay-as-you-go) | Classification, summary, risk signals |
| Azure SQL | Free | Structured results |
| Static Web App | Free | Dashboard frontend (custom domain + TLS) |
| Key Vault | Standard | Secrets |
| Application Insights + Log Analytics | PerGB2018 | Traces, metrics, token usage |

## Processing flow

1. `POST /api/documents` (multipart) → validate size ≤ 4MB, page count ≤ 2
   → insert `Documents` row (`UPLOADED`) → upload blob (with `document_type_hint`
   metadata) → `202 Accepted`.
2. Blob trigger fires → read content + hint → `PROCESSING`.
3. Document Intelligence extracts text/fields (model chosen by hint, else
   `prebuilt-read`).
4. Azure OpenAI returns a strictly-validated `AIInsight` (camelCase JSON).
5. Persist `ExtractionResults` + `AIInsights`, mark `COMPLETED`.
6. Dashboard polls `GET /api/documents/{id}`.

## Architecture Decision Records

### ADR-1: Static Web App instead of App Service F1 for the dashboard
**Decision**: host the dashboard on **Static Web App (Free)**.
**Reason**: App Service **F1 does not support custom domains or TLS**, which the
`azure-ai-doc.techcloudup.com` requirement needs. SWA Free supports custom
domains + free TLS. The dashboard is static (HTML/JS) and calls the Functions
API directly.

### ADR-2: Azure OpenAI `GlobalStandard` deployment in `eastus`
**Decision**: deploy `gpt-4o-mini` with scale type `GlobalStandard` in `eastus`.
**Reason**: account review confirmed `GlobalStandard.gpt-4o-mini` quota (2000
TPM) is already available in `eastus`; no regional Standard quota exists in
`koreacentral`. GlobalStandard also allows routing across regions.

### ADR-3: Single storage account for platform + documents
**Decision**: one `Standard_LRS` storage account serves both the Function App
platform storage and the `documents` container.
**Reason**: minimizes the free-tier footprint; acceptable isolation for a
prototype. Split later if needed.

### ADR-4: Custom `x-api-key` over Function host key
**Decision**: protect the HTTP API with a custom `x-api-key` header validated
in-code, sourced from Key Vault (`api-key` secret).
**Reason**: keeps the dashboard↔API auth simple and independent of Azure's
function-host key; matches the PRD "API Key or Entra" requirement.

### ADR-5: Manual Cloudflare DNS
**Decision**: manage `azure-ai-doc.techcloudup.com` DNS manually in Cloudflare;
keep the Cloudflare Terraform provider optional.
**Reason**: no Cloudflare API token was provided; avoids storing a zone-scoped
secret. Automated DNS can be enabled later via `infra/dns.tf`.

### ADR-6: Azure SQL Free offer (with fallback)
**Decision**: target the one-per-subscription Azure SQL **Free** offer
(32GB, 100k vCore-s/month, auto-pause after 7 days idle).
**Reason**: only free relational option that fits the "extreme minimal cost"
goal. If the provider/API rejects `sku_name = "Free"`, provision via portal and
`terraform import`, or fall back to `Basic`.

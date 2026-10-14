# PRD: Intelligent Document Processing Pipeline (IDP) — Service Prototype

## 0. Document Overview

| Field | Content |
|---|---|
| Project name | AI-Powered Intelligent Document Processing Pipeline (IDP) |
| Purpose | Automatically classify, extract, and summarize financial documents (KYC, loan documents, service applications) to support user assistance and operational automation |
| Project type | Personal project (service prototype) |
| Application domain | Financial document processing (KYC, loan documents, user service) |
| Tech stack | Azure Functions, Azure AI Document Intelligence, Azure OpenAI, Azure SQL, Blob Storage, Key Vault, Terraform, GitHub Actions, Flask/Power BI |
| Cost strategy | Azure free tier + pay-as-you-go (Azure OpenAI only) + F0/Consumption/Free SQL |
| Deployment region | `eastus` (US) |
| Project URL | `ai-doc.techcloudup.com` |
| Status | Proposal / Project MVP |

---

## 1. Background and Problem Definition

Financial institutions manually review a wide range of documents, such as KYC IDs, loan application documents, and user service request forms. This process is slow, error-prone, and difficult to audit.

This project uses Azure's managed AI services to automate the following:

- Document upload and storage
- OCR / document field extraction
- Document type classification
- Key content summarization
- Risk signal and missing field detection
- Structured data storage and dashboard queries

---

## 2. Goals and Success Metrics

### 2.1 Product Goals
1. Return structured results within 60 seconds for 1–2 page financial documents.
2. Implement an AI/LLM integration pipeline combining Document Intelligence + Azure OpenAI.
3. Build a deployable and secure operational setup with Terraform + GitHub Actions + Key Vault.
4. Complete within the free tier, with only Azure OpenAI billed pay-as-you-go.

### 2.2 Success Metrics
| Metric | Target |
|---|---|
| Document processing success rate | ≥ 95% on test documents |
| Average processing time | ≤ 60 seconds for 1–2 page documents |
| Field extraction accuracy | ≥ 90% on key fields (synthetic data) |
| Monthly cost | ≤ $5 pay-as-you-go (Azure OpenAI tokens only) during the operating period |
| Security | Zero secrets in code/repos; Key Vault + Managed Identity |
| Deployment automation | Reproducible via `terraform apply` + GitHub Actions |

---

## 3. Users and Personas

| Persona | Description | Key needs |
|---|---|---|
| User service representative | Reviews documents uploaded by users | Fast classification, summary, missing-field checks |
| Loan officer | Reviews income/identity/address proof | Key field extraction, risk signal detection |
| Operations manager | Monitors processing status | Dashboard, audit logs, error alerts |

---

## 4. Scope

### 4.1 In Scope
- PDF/PNG/JPEG document upload (max 4MB, 1–2 pages; PDF page count pre-validated at upload)
- Blob Storage persistence
- Azure Functions-based processing trigger
- OCR/field extraction via Document Intelligence F0
- Summary/classification/risk-signal generation via Azure OpenAI
- Result persistence in Azure SQL
- Flask or Power BI dashboard
- Key Vault + Managed Identity
- Terraform + GitHub Actions deployment
- Synthetic test documents and README/Runbook

### 4.2 Out of Scope
- Real user PII
- Documents of 3+ pages
- Real-time streaming processing
- Production-grade HA/DR
- Private Endpoint/VNet integration (optional extension)
- Full KYC compliance certification

---

## 5. Core User Scenarios

### Scenario A: KYC ID Processing
1. A user uploads an ID image.
2. The system extracts name, date of birth, document number, and expiration date using `prebuilt-idDocument`.
3. Azure OpenAI classifies the document type as `KYC_ID` and generates a summary and risk signals.
4. The masked results and confidence are displayed on the dashboard.

### Scenario B: Loan Invoice/Document Processing
1. A user uploads a 1–2 page loan-related invoice.
2. `prebuilt-invoice` extracts supplier, amount, due date, and account number.
3. OpenAI returns "missing fields", "further review required", and "anomalies" as JSON.
4. Results are stored in Azure SQL and shown on the dashboard.

### Scenario C: Failure / Reprocessing
1. A user uploads a document exceeding 4MB or 3 pages.
2. The upload handler pre-validates file size and PDF page count, rejects it immediately, and stores the status as `REJECTED`.
3. An administrator reviews the error reason, splits it into 1–2 pages, and re-uploads.

---

## 6. Functional Requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-01 | Users can upload documents via a web UI or REST API. | Must |
| FR-02 | Uploaded files are limited to PDF, PNG, JPEG, ≤ 4MB, ≤ 2 pages. PDF page count is pre-validated at upload (e.g., via pypdf), and over-limit files are rejected immediately. | Must |
| FR-03 | Uploaded files are stored in Azure Blob Storage. | Must |
| FR-04 | A blob creation event triggers an Azure Function. | Must |
| FR-05 | The Function determines the document type before selecting a Document Intelligence model. Determination uses (a) user selection at upload, or (b) a 2-pass flow of `prebuilt-read` first-pass extraction → OpenAI classification. | Must |
| FR-06 | Extracted results are transformed and validated against a camelCase normalization schema (Pydantic/JSON Schema). | Must |
| FR-07 | OCR text and extracted fields are passed to Azure OpenAI to generate summary/classification/risk signals. | Must |
| FR-08 | Results are stored in Azure SQL. | Must |
| FR-09 | The dashboard displays document list, status, summary, confidence, and risk signals. | Must |
| FR-10 | Secrets are stored in Key Vault and accessed via Managed Identity. | Must |
| FR-11 | Processing history and error logs are stored. | Should |
| FR-12 | Retries and dead-letter handling on failure. | Should |
| FR-13 | Administrators can reprocess a document. | Could |
| FR-14 | Send completion/failure notifications via n8n or Teams/Email. | Could |

---

## 7. Non-Functional Requirements

| Category | Requirement |
|---|---|
| Performance | ≤ 60 seconds for 1–2 page documents |
| Scalability | Auto-scaling on a Consumption Plan |
| Security | TLS, Key Vault, Managed Identity, no hardcoded secrets |
| Privacy | Synthetic data only, PII masking, no raw storage in logs |
| Observability | Application Insights + Log Analytics; record processing time / failure rate / token usage |
| Cost | F0, Consumption, Azure SQL Free, small models first |
| Reproducibility | Infrastructure-as-code with Terraform, CI/CD with GitHub Actions |
| Documentation | README, architecture diagram, runbook, draft SLO |

---

## 8. Architecture

```text
[Flask UI / REST API]  (API Key / Entra auth)
        │ upload
        ▼
[Azure Blob Storage] ──(Blob Trigger)──▶ [Azure Functions]
                                                │ ① OCR/field extraction (2-pass)
                                                ├──────────▶ [Azure AI Document Intelligence F0]
                                                │ ② classification/summary/risk signals
                                                ├──────────▶ [Azure OpenAI GPT-4o Mini]
                                                │ ③ persist
                                                └──────────▶ [Azure SQL Database Free]
                                                                │
                                                                ▼
                                                        [Flask Dashboard / Power BI]
```

### Components
| Component | Role |
|---|---|
| Azure Blob Storage | Stores source documents |
| Azure Functions | Upload validation (size·page count), document type determination, DI call, OpenAI call, SQL persistence |
| Document Intelligence F0 | OCR and field extraction |
| Azure OpenAI | Summary, classification, risk signals, missing fields |
| Azure SQL Free | Stores structured results |
| Azure Storage Queue | (optional, FR-12) failure retry / dead-letter |
| Key Vault | Stores API keys and connection strings |
| Managed Identity | Key Vault access |
| Terraform | Infrastructure provisioning |
| GitHub Actions | Build/deploy/test |
| Flask | Simple upload/query UI |
| Power BI | Optional visualization (Pro license required for service sharing; free tier is Desktop-local only) |

---

## 9. Data Model (Example)

### 9.1 Documents
```sql
CREATE TABLE Documents (
    DocumentId UNIQUEIDENTIFIER PRIMARY KEY,
    FileName NVARCHAR(255),
    BlobUrl NVARCHAR(1000),
    DocumentType NVARCHAR(50),
    Status NVARCHAR(20), -- UPLOADED, PROCESSING, COMPLETED, FAILED, REJECTED, REPROCESSING
    PageCount INT,
    SizeBytes BIGINT,
    UploadedBy NVARCHAR(100),
    UploadedAt DATETIME2,
    ProcessedAt DATETIME2 NULL
);
```

### 9.2 ExtractionResults
```sql
CREATE TABLE ExtractionResults (
    ResultId UNIQUEIDENTIFIER PRIMARY KEY,
    DocumentId UNIQUEIDENTIFIER FOREIGN KEY REFERENCES Documents(DocumentId),
    ModelId NVARCHAR(100),
    FieldsJson NVARCHAR(MAX),
    ConfidenceJson NVARCHAR(MAX),
    RawResponseJson NVARCHAR(MAX), -- stored after PII masking (redaction); no raw PII
    CreatedAt DATETIME2
);
```

### 9.3 AIInsights
```sql
CREATE TABLE AIInsights (
    InsightId UNIQUEIDENTIFIER PRIMARY KEY,
    DocumentId UNIQUEIDENTIFIER FOREIGN KEY REFERENCES Documents(DocumentId),
    Summary NVARCHAR(MAX),
    Classification NVARCHAR(100),
    RiskFlags NVARCHAR(MAX),
    MissingFields NVARCHAR(MAX),
    RecommendedAction NVARCHAR(500),
    ModelName NVARCHAR(100),
    PromptVersion NVARCHAR(20),
    TokensIn INT,
    TokensOut INT,
    CreatedAt DATETIME2
);
```

---

### 9.4 State Transitions (State Machine)
```
UPLOADED → PROCESSING → COMPLETED  (success)
UPLOADED → PROCESSING → FAILED     (processing error, reprocessable)
UPLOADED → REJECTED                (validation failure: size/page limit exceeded, not reprocessable)
FAILED → REPROCESSING → PROCESSING (admin reprocessing)
```

- Reprocessing (`POST /api/documents/{id}/reprocess`) replaces existing `ExtractionResults`/`AIInsights` but preserves history via the `CreatedAt` version.
- Reprocessing is idempotent (same input → same processing).

---

## 10. API Design (Example)

> Authentication: all APIs use API Key or Entra ID (OAuth2) authentication.

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/documents` | Upload document (multipart). **Async**: returns `202 Accepted` + `documentId` |
| GET | `/api/documents` | List documents |
| GET | `/api/documents/{id}` | Get document details/results (results included once processing completes; client polls) |
| POST | `/api/documents/{id}/reprocess` | Reprocess (transitions status to `REPROCESSING`) |
| GET | `/api/health` | Health check |

### Processing Flow
1. `POST /api/documents` → validate file size and page count → store in Blob → return `202 Accepted` + `documentId`
2. Blob Trigger runs the Function → DI extraction → OpenAI classification/summary → SQL persistence
3. The client polls `GET /api/documents/{id}` to check the final status

### Query Response Example (final status at `GET /api/documents/{id}` polling time)
```json
{
  "documentId": "0f8c...",
  "status": "COMPLETED",
  "documentType": "KYC_ID",
  "summary": "Name, date of birth, and expiration date confirmed on the ID. Expiration date 2026-08-31 is valid.",
  "keyFields": {
    "name": "H*** G******",
    "dateOfBirth": "1990-01-01",
    "documentNumber": "M****1234",
    "expirationDate": "2026-08-31"
  },
  "riskFlags": [],
  "missingFields": [],
  "confidence": 0.94
}
```

> See section 12 for the masking policy. `name` and `documentNumber` are masked; date fields are exposed because they are synthetic test values.

---

## 11. AI/LLM Design

### 11.1 Model Selection
- Document Intelligence: `prebuilt-idDocument`, `prebuilt-invoice`
- Azure OpenAI: small models first (e.g., `gpt-4o-mini`)
- Temperature: 0.2
- Response format: JSON

### 11.2 Prompt Example
```text
System:
You are an AI assistant for a financial institution document processing pipeline.
Use only the provided OCR text and extracted fields.
Do not invent values. If uncertain, mark confidence as low.
Return JSON only.

User:
Document type hint: {hint}
Extracted fields: {fields_json}
OCR text: {ocr_text}

Return (camelCase, JSON only):
{
  "classification": "",
  "summary": "",
  "keyFields": {},
  "riskFlags": [],
  "missingFields": [],
  "recommendedAction": "",
  "confidence": 0.0
}
```

### 11.3 Safeguards
- Only OCR text and extracted fields are provided as context
- PII is masked before storage
- Prompt versioning
- Token usage logging
- Retry or fail on model output JSON schema validation failure
- Model output keys are normalized to camelCase; `classification` maps to `Documents.DocumentType` / API response `documentType`

---

## 12. Security and Compliance

- All secrets stored in Key Vault
- Function accesses Key Vault via System-assigned Managed Identity
- SQL connection string referenced from Key Vault
- Blob/SQL access via Managed Identity preferred
- API authentication: API Key or Entra ID (OAuth2) on web UI/REST API
- No raw PII in logs
- Only synthetic documents used for testing
- Terraform state uses a remote backend + locking (recommended)
- GitHub Actions OIDC for Azure authentication (where possible)

### PII Masking Policy
| Field | Policy |
|---|---|
| name | Expose first letter only, mask the rest with `*` (e.g., `H*** G******`) |
| documentNumber | Mask the leading part, expose last 4 digits (e.g., `M****1234`) |
| dateOfBirth / expirationDate | Exposure allowed for synthetic test values (separate production policy defined) |
| summary / raw OCR | No PII; raw content redacted before storage |

### Data Retention Policy
- `ExtractionResults.RawResponseJson` is stored after PII redaction.
- Source blobs of completed documents are retained 30 days after the operating period ends, then auto-deleted.
- Audit logs (processing history) are retained 90 days.

---

## 13. Deployment and Operations

### 13.1 Terraform Resources

> All resources deploy to the `eastus` (US) region in a dedicated resource group `idp-prototype`, isolated from the existing `oc-health-dba-ml` and `arc-hybrid-lab` workloads.

- Resource Group (`idp-prototype`, `eastus`)
- Storage Account + Blob Container
- Function App + Consumption Plan
- Document Intelligence F0
- Azure OpenAI + Deployment
- Azure SQL Server + Free Database
- Key Vault
- Application Insights
- Log Analytics Workspace
- (optional, FR-12) Storage Queue — failure retry / dead-letter

> FR-12 (retry/dead-letter) uses a Storage Queue; FR-14 (n8n/Teams notifications) is an optional extension.

### 13.2 GitHub Actions
- `terraform fmt`, `validate`, `plan`
- `terraform apply` (main branch)
- Function app deployment
- Flask app deployment (App Service F1)
- Smoke test with test documents

### 13.3 Runbook Draft
1. On Function failure, check errors in Application Insights
2. On Document Intelligence quota exhaustion, review next-month or S0 migration
3. On OpenAI token overrun, reduce model/prompt size
4. On SQL connection failure, check Key Vault secrets and Managed Identity permissions
5. On blob trigger not firing, check Event Grid/Function trigger configuration

---

## 14. Free Tier and Cost Management

> **Billing note**: this subscription is **pay-as-you-go (Microsoft Customer Agreement)**, not a free-trial account, so there is no $200 new-account credit. The only billable service is Azure OpenAI (no free tier); all other components run on free tiers. The "monthly cost" target in 2.2 is therefore driven by Azure OpenAI token usage alone.

| Service | Strategy |
|---|---|
| Document Intelligence | F0: 500 pages/month, first 2 pages per document, max 4MB |
| Azure OpenAI | GPT-4o Mini (`GlobalStandard`, `eastus`, pay-as-you-go — no free tier); token limits, caching, and per-minute request cap |
| Azure Functions | Consumption: 1M requests, 400,000 GB-s free per month |
| Azure SQL | Free tier: 32GB, 100,000 vCore-seconds/month (auto-pauses after 7 days idle) |
| Key Vault | $0.03 per 10,000 transactions |
| App Service | F1 free (Linux, **60 CPU-min/day** — may throttle under continuous access) |
| Power BI | Desktop free; Pro license required for service sharing → use Flask dashboard for demos |
| GitHub Actions | Free plan |

### Cost Alerts
- Set $1, $5, $10 alerts in Azure Cost Management + Budgets
- Monitor Document Intelligence F0 page usage
- Dashboard OpenAI token usage

---

## 15. Testing and Acceptance Criteria

### 15.1 Test Types
- Unit tests: file validation, JSON normalization, prompt builder
- Integration tests: Blob → Function → DI → OpenAI → SQL
- E2E tests: upload → dashboard query
- Security tests: secret exposure scan, Key Vault access verification
- Cost tests: processing within free-tier limits

### 15.2 Acceptance Criteria
- [ ] A 1-page KYC document shows results within 60 seconds
- [ ] ≥ 90% of key fields extracted from a 2-page invoice
- [ ] Documents over 4MB or 3 pages are rejected with a clear error
- [ ] All secrets stored in Key Vault, none in code
- [ ] Full infrastructure reproducible via Terraform
- [ ] Deployment automated via GitHub Actions
- [ ] README includes architecture, cost, security, and runbook
- [ ] Synthetic data only

---

## 16. Milestones

| Week | Deliverables |
|---|---|
| Week 1 | Terraform infrastructure, Blob, Function skeleton, Key Vault, **OpenAI deployment (`gpt-4o-mini` GlobalStandard, `eastus`)** |
| Week 2 | Document Intelligence integration, SQL schema, upload API |
| Week 3 | Azure OpenAI summary/classification, Flask dashboard |
| Week 4 | GitHub Actions, tests, README/Runbook, demo video |

---

## 17. Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| F0 2-page limit | Document processing failure | Use 1–2 page test documents; guide PDF splitting |
| OpenAI region/quota not secured | Project delay | Quota already available in `eastus` (`GlobalStandard` gpt-4o-mini, 2000 TPM); deploy in `eastus` and confirm quota in Week 1 |
| OpenAI cost overrun | Pay-as-you-go overrun | Small models, token limits, caching, per-minute request cap, cost alerts |
| PII exposure | Compliance issues | Synthetic data, masking policy (section 12), minimal logging |
| Function cold start | Latency | Warm-up before demo, adjust timeout |
| Document Intelligence rate limit | Processing delay | Queue-based retry, backoff |
| SQL Free limit | Storage failure | Operate within 32GB, auto-cleanup per retention policy (section 12) |
| App Service F1 CPU limit | Dashboard throttling | Start only during demo hours or have Function serve the UI |
| Power BI sharing license | Visualization cost | Use Flask dashboard; Power BI for local demos |

---

## 18. Deliverables

- Terraform code
- Azure Functions code
- Flask dashboard
- SQL schema and migrations
- GitHub Actions workflow
- README + architecture diagram
- Runbook + draft SLO
- Synthetic test documents
- Demo video/screenshots

---

## 19. Project Summary

### Project Introduction
> An Azure-based AI document processing pipeline that combines Document Intelligence (OCR) with Azure OpenAI to generate document summaries, classification, and risk signals, deployed via Terraform/GitHub Actions and operated with Key Vault-managed secrets and Azure SQL.

### Key Implementation Points
| Implementation item | Details |
|---|---|
| AI/LLM integration | Document Intelligence + Azure OpenAI |
| Document processing | IDP pipeline for KYC and loan documents |
| Operations/documentation | Terraform, GitHub Actions, README, Runbook |
| Security/compliance | Key Vault, Managed Identity, PII masking |
| Event-driven | Blob Trigger + Functions |

---

## 20. Conclusion

This PRD defines the project not as a "demo-only AI document processor" but as a **reproducible, free/ultra-low-cost Azure AI/LLM integrated service prototype**. The three key points are:

1. **Reflect F0/Free Tier constraints in the design** so it actually works.
2. **Implement a deployable and secure operational setup** with Key Vault + Managed Identity + Terraform + GitHub Actions.
3. **Build a service prototype that solves document processing requirements** for financial institutions.

Once implemented, `ai-doc.techcloudup.com` becomes a working financial institution document processing service prototype.

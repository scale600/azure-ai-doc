# API Specification

Base URL: `https://func-idp-<uniq>.azurewebsites.net`
All endpoints are prefixed with `/api` automatically by Azure Functions.

## Authentication

`x-api-key: <key>` header on all endpoints except `/api/health`.

## Endpoints

| Method | Path | Description | Auth |
|---|---|---|---|
| GET | `/api/health` | Health check | none |
| POST | `/api/documents` | Upload document (multipart) | key |
| GET | `/api/documents` | List documents | key |
| GET | `/api/documents/{id}` | Get document + results | key |
| POST | `/api/documents/{id}/reprocess` | Reprocess | key |

## POST /api/documents

- Content-Type: `multipart/form-data`
- Form fields:
  - `file` (file, required): PDF/PNG/JPEG, ≤ 4MB, ≤ 2 pages
  - `document_type` (text, optional): `KYC_ID` | `INVOICE`

Responses:
- `202` — `{"documentId": "...", "status": "ACCEPTED"}`
- `400` — invalid file / unsupported type / invalid PDF
- `413` — size or page limit exceeded
- `401` — missing/invalid key

## GET /api/documents/{id}

Response (after completion):
```json
{
  "documentId": "0f8c...",
  "fileName": "scan.pdf",
  "documentType": "KYC_ID",
  "status": "COMPLETED",
  "classification": "KYC_ID",
  "summary": "Name, date of birth, and expiration date confirmed...",
  "keyFields": {
    "name": "H*** G******",
    "documentNumber": "M****1234",
    "expirationDate": "2026-08-31"
  },
  "riskFlags": [],
  "missingFields": [],
  "recommendedAction": "",
  "confidence": 0.94,
  "modelName": "gpt-4o-mini",
  "uploadedAt": "2026-10-14T00:00:00Z",
  "processedAt": "2026-10-14T00:00:03Z"
}
```

## OpenAPI (abbreviated)

```yaml
openapi: 3.0.3
info: { title: IDP API, version: 0.1.0 }
servers:
  - url: https://func-idp-<uniq>.azurewebsites.net/api
security:
  - ApiKeyAuth: []
paths:
  /health:
    get:
      responses: { "200": { description: ok } }
  /documents:
    post:
      summary: Upload a document
      requestBody:
        content:
          multipart/form-data:
            schema:
              type: object
              properties:
                file: { type: string, format: binary }
                document_type: { type: string, enum: [KYC_ID, INVOICE] }
      responses:
        "202": { description: accepted }
        "413": { description: too large / too many pages }
    get:
      summary: List documents
      responses: { "200": { description: list } }
  /documents/{id}:
    get:
      parameters: [{ name: id, in: path, required: true, schema: { type: string } }]
      responses: { "200": { description: document detail } }
components:
  securitySchemes:
    ApiKeyAuth:
      type: apiKey
      in: header
      name: x-api-key
```

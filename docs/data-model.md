# Data Model

Applied to Azure SQL via `src/schema.sql` (idempotent DDL).

## Documents

```sql
CREATE TABLE dbo.Documents (
    DocumentId UNIQUEIDENTIFIER PRIMARY KEY,
    FileName NVARCHAR(255) NOT NULL,
    BlobUrl NVARCHAR(1000) NULL,
    DocumentType NVARCHAR(50) NULL,
    Status NVARCHAR(20) NOT NULL DEFAULT 'UPLOADED', -- UPLOADED/PROCESSING/COMPLETED/FAILED/REJECTED/REPROCESSING
    PageCount INT NULL,
    SizeBytes BIGINT NULL,
    UploadedBy NVARCHAR(100) NULL,
    UploadedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    ProcessedAt DATETIME2 NULL
);
```

## ExtractionResults

```sql
CREATE TABLE dbo.ExtractionResults (
    ResultId UNIQUEIDENTIFIER PRIMARY KEY,
    DocumentId UNIQUEIDENTIFIER NOT NULL
        REFERENCES dbo.Documents(DocumentId),
    ModelId NVARCHAR(100) NOT NULL,
    FieldsJson NVARCHAR(MAX) NULL,
    ConfidenceJson NVARCHAR(MAX) NULL,
    RawResponseJson NVARCHAR(MAX) NULL, -- PII-redacted before storage
    CreatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
```

## AIInsights

```sql
CREATE TABLE dbo.AIInsights (
    InsightId UNIQUEIDENTIFIER PRIMARY KEY,
    DocumentId UNIQUEIDENTIFIER NOT NULL
        REFERENCES dbo.Documents(DocumentId),
    Summary NVARCHAR(MAX) NULL,
    Classification NVARCHAR(100) NULL,
    RiskFlags NVARCHAR(MAX) NULL,        -- JSON array
    MissingFields NVARCHAR(MAX) NULL,    -- JSON array
    RecommendedAction NVARCHAR(500) NULL,
    ModelName NVARCHAR(100) NULL,
    PromptVersion NVARCHAR(20) NULL,
    TokensIn INT NULL,
    TokensOut INT NULL,
    CreatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
```

## State machine

```
UPLOADED → PROCESSING → COMPLETED   (success)
UPLOADED → PROCESSING → FAILED      (processing error, reprocessable)
UPLOADED → REJECTED                 (validation failure, not reprocessable)
FAILED → REPROCESSING → PROCESSING  (admin reprocess)
```

## Notes

- `RiskFlags` / `MissingFields` are JSON arrays serialized to `NVARCHAR(MAX)`.
- `keyFields` from the LLM are surfaced in the API response but not persisted as
  a separate column (they live in `FieldsJson`/the LLM output).
- Reprocessing replaces `ExtractionResults`/`AIInsights` rows but history is
  preserved via `CreatedAt`.

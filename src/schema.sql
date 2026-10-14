-- Applied once to the Azure SQL database. See docs/data-model.md.
-- Run via `sqlcmd` or SSMS/Azure Data Studio. Idempotent.

IF OBJECT_ID('dbo.Documents', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Documents (
        DocumentId UNIQUEIDENTIFIER PRIMARY KEY,
        FileName NVARCHAR(255) NOT NULL,
        BlobUrl NVARCHAR(1000) NULL,
        DocumentType NVARCHAR(50) NULL,
        Status NVARCHAR(20) NOT NULL DEFAULT 'UPLOADED',
        PageCount INT NULL,
        SizeBytes BIGINT NULL,
        UploadedBy NVARCHAR(100) NULL,
        UploadedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        ProcessedAt DATETIME2 NULL,
        ErrorMessage NVARCHAR(MAX) NULL
    );
END;

IF OBJECT_ID('dbo.ExtractionResults', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.ExtractionResults (
        ResultId UNIQUEIDENTIFIER PRIMARY KEY,
        DocumentId UNIQUEIDENTIFIER NOT NULL,
        ModelId NVARCHAR(100) NOT NULL,
        FieldsJson NVARCHAR(MAX) NULL,
        ConfidenceJson NVARCHAR(MAX) NULL,
        RawResponseJson NVARCHAR(MAX) NULL, -- PII-redacted before storage
        CreatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        CONSTRAINT FK_ExtractionResults_Documents
            FOREIGN KEY (DocumentId) REFERENCES dbo.Documents(DocumentId)
    );
END;

IF OBJECT_ID('dbo.AIInsights', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.AIInsights (
        InsightId UNIQUEIDENTIFIER PRIMARY KEY,
        DocumentId UNIQUEIDENTIFIER NOT NULL,
        Summary NVARCHAR(MAX) NULL,
        Classification NVARCHAR(100) NULL,
        RiskFlags NVARCHAR(MAX) NULL,
        MissingFields NVARCHAR(MAX) NULL,
        RecommendedAction NVARCHAR(500) NULL,
        ModelName NVARCHAR(100) NULL,
        PromptVersion NVARCHAR(20) NULL,
        TokensIn INT NULL,
        TokensOut INT NULL,
        Confidence FLOAT NULL,
        KeyFieldsJson NVARCHAR(MAX) NULL,
        CreatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        CONSTRAINT FK_AIInsights_Documents
            FOREIGN KEY (DocumentId) REFERENCES dbo.Documents(DocumentId)
    );
END;

-- Idempotent migrations for pre-existing databases (columns added later).
IF COL_LENGTH('dbo.Documents', 'ErrorMessage') IS NULL
    ALTER TABLE dbo.Documents ADD ErrorMessage NVARCHAR(MAX) NULL;

IF COL_LENGTH('dbo.AIInsights', 'Confidence') IS NULL
    ALTER TABLE dbo.AIInsights ADD Confidence FLOAT NULL;

IF COL_LENGTH('dbo.AIInsights', 'KeyFieldsJson') IS NULL
    ALTER TABLE dbo.AIInsights ADD KeyFieldsJson NVARCHAR(MAX) NULL;

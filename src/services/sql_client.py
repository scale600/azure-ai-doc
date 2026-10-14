"""Azure SQL persistence layer (pyodbc, parameterized queries only)."""

from __future__ import annotations

import json
import logging

import pyodbc

from models import AIInsight, DocumentStatus

logger = logging.getLogger(__name__)


class SqlClient:
    def __init__(self, server: str, database: str, user: str, password: str) -> None:
        self._conn_str = (
            "DRIVER={ODBC Driver 18 for SQL Server};"
            f"SERVER={server};DATABASE={database};UID={user};PWD={password};"
            "Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
        )

    def _connect(self) -> pyodbc.Connection:
        return pyodbc.connect(self._conn_str)

    # --- Documents ---------------------------------------------------------

    def insert_document(
        self,
        document_id: str,
        file_name: str,
        blob_url: str,
        size_bytes: int,
        page_count: int | None,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO dbo.Documents
                    (DocumentId, FileName, BlobUrl, SizeBytes, PageCount, Status, UploadedAt)
                VALUES (?, ?, ?, ?, ?, ?, SYSUTCDATETIME())
                """,
                document_id,
                file_name,
                blob_url,
                size_bytes,
                page_count,
                DocumentStatus.UPLOADED,
            )

    def set_blob_url(self, document_id: str, blob_url: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE dbo.Documents SET BlobUrl = ? WHERE DocumentId = ?",
                blob_url,
                document_id,
            )

    def update_status(self, document_id: str, status: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE dbo.Documents SET Status = ? WHERE DocumentId = ?",
                status,
                document_id,
            )

    def mark_completed(self, document_id: str, document_type: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE dbo.Documents
                SET Status = ?, DocumentType = ?, ProcessedAt = SYSUTCDATETIME()
                WHERE DocumentId = ?
                """,
                DocumentStatus.COMPLETED,
                document_type,
                document_id,
            )

    def mark_failed(self, document_id: str, error_message: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE dbo.Documents
                SET Status = ?, ErrorMessage = ?, ProcessedAt = SYSUTCDATETIME()
                WHERE DocumentId = ?
                """,
                DocumentStatus.FAILED,
                error_message,
                document_id,
            )

    def list_documents(self, limit: int = 100) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT TOP (?) DocumentId, FileName, DocumentType, Status,
                       PageCount, SizeBytes, UploadedAt, ProcessedAt, ErrorMessage
                FROM dbo.Documents ORDER BY UploadedAt DESC
                """,
                limit,
            ).fetchall()
        return [self._document_to_dict(r) for r in rows]

    def get_document(self, document_id: str) -> dict | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT DocumentId, FileName, DocumentType, Status,
                       PageCount, SizeBytes, UploadedAt, ProcessedAt, ErrorMessage
                FROM dbo.Documents WHERE DocumentId = ?
                """,
                document_id,
            ).fetchone()
            if row is None:
                return None
            doc = self._document_to_dict(row)

            insight = conn.execute(
                """
                SELECT Summary, Classification, RiskFlags, MissingFields,
                       RecommendedAction, ModelName, TokensIn, TokensOut, Confidence, KeyFieldsJson
                FROM dbo.AIInsights WHERE DocumentId = ? ORDER BY CreatedAt DESC
                """,
                document_id,
            ).fetchone()
            if insight is not None:
                doc["summary"] = insight[0]
                doc["classification"] = insight[1]
                doc["riskFlags"] = json.loads(insight[2] or "[]")
                doc["missingFields"] = json.loads(insight[3] or "[]")
                doc["recommendedAction"] = insight[4]
                doc["modelName"] = insight[5]
                doc["tokensIn"] = insight[6]
                doc["tokensOut"] = insight[7]
                doc["confidence"] = insight[8]
                doc["keyFields"] = json.loads(insight[9] or "{}")
        return doc

    # --- Extraction / Insight ---------------------------------------------

    def insert_extraction(
        self,
        result_id: str,
        document_id: str,
        model_id: str,
        fields: dict,
        confidence: dict,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO dbo.ExtractionResults
                    (ResultId, DocumentId, ModelId, FieldsJson, ConfidenceJson, CreatedAt)
                VALUES (?, ?, ?, ?, ?, SYSUTCDATETIME())
                """,
                result_id,
                document_id,
                model_id,
                json.dumps(fields, ensure_ascii=False),
                json.dumps(confidence, ensure_ascii=False),
            )

    def insert_insight(
        self,
        insight_id: str,
        document_id: str,
        insight: AIInsight,
        model_name: str,
        prompt_version: str,
        tokens_in: int,
        tokens_out: int,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO dbo.AIInsights
                    (InsightId, DocumentId, Summary, Classification, RiskFlags,
                     MissingFields, RecommendedAction, ModelName, PromptVersion,
                     TokensIn, TokensOut, Confidence, KeyFieldsJson, CreatedAt)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, SYSUTCDATETIME())
                """,
                insight_id,
                document_id,
                insight.summary,
                insight.classification,
                json.dumps(insight.riskFlags, ensure_ascii=False),
                json.dumps(insight.missingFields, ensure_ascii=False),
                insight.recommendedAction,
                model_name,
                prompt_version,
                tokens_in,
                tokens_out,
                insight.confidence,
                json.dumps(insight.keyFields, ensure_ascii=False),
            )

    @staticmethod
    def _document_to_dict(row) -> dict:
        return {
            "documentId": str(row[0]),
            "fileName": row[1],
            "documentType": row[2],
            "status": row[3],
            "pageCount": row[4],
            "sizeBytes": row[5],
            "uploadedAt": row[6].isoformat() if row[6] else None,
            "processedAt": row[7].isoformat() if row[7] else None,
            "errorMessage": row[8],
        }

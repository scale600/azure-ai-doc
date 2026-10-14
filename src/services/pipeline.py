"""Core processing pipeline: DI -> OpenAI -> SQL persistence.

Shared by the blob trigger and the reprocess endpoint so both paths are
identical (idempotent reprocessing).
"""

from __future__ import annotations

import json
import logging
import uuid

from models import DocumentStatus
from services.di_client import DocumentIntelligenceClient
from services.openai_client import OpenAIClient
from services.sql_client import SqlClient

logger = logging.getLogger(__name__)

_PROMPT_VERSION = "v1"


def _determine_model(hint: str | None) -> str:
    if hint == "KYC_ID":
        return "prebuilt-idDocument"
    if hint == "INVOICE":
        return "prebuilt-invoice"
    return "prebuilt-read"


def process_document(
    document_id: str,
    file_name: str,
    content: bytes,
    hint: str | None,
    di: DocumentIntelligenceClient,
    openai: OpenAIClient,
    sql: SqlClient,
) -> None:
    """Run the full pipeline for one document. Updates status on every step."""
    sql.update_status(document_id, DocumentStatus.PROCESSING)

    model_id = _determine_model(hint)
    try:
        ocr_text, fields, confidence = di.analyze(content, model_id)

        sql.insert_extraction(
            result_id=str(uuid.uuid4()),
            document_id=document_id,
            model_id=model_id,
            fields=fields,
            confidence=confidence,
        )

        insight, tokens_in, tokens_out = openai.generate_insight(ocr_text, fields, hint)

        sql.insert_insight(
            insight_id=str(uuid.uuid4()),
            document_id=document_id,
            insight=insight,
            model_name=openai.deployment,
            prompt_version=_PROMPT_VERSION,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
        )

        sql.mark_completed(document_id, insight.classification or "UNKNOWN")
        logger.info("Completed document %s (%s)", document_id, model_id)

    except Exception as exc:  # noqa: BLE001 — mark failed and re-raise for retry/visibility
        sql.mark_failed(document_id, str(exc))
        logger.exception("Failed document %s", document_id)
        raise

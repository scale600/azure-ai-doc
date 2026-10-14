"""Document Intelligence (OCR / field extraction) client wrapper."""

from __future__ import annotations

import datetime
import logging
from typing import Any

from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential

logger = logging.getLogger(__name__)


def _to_json(value: Any) -> Any:
    """Normalize a Document Intelligence field value to JSON-serializable form."""
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (datetime.date, datetime.datetime)):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: _to_json(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_json(v) for v in value]
    return str(value)


class DocumentIntelligenceClient:
    def __init__(self, endpoint: str, key: str) -> None:
        self._client = DocumentAnalysisClient(
            endpoint=endpoint, credential=AzureKeyCredential(key)
        )

    def analyze(self, content: bytes, model_id: str) -> tuple[str, dict, dict]:
        """Analyze a document and return (ocr_text, fields, confidence)."""
        poller = self._client.begin_analyze_document(model_id, content)
        result = poller.result()

        ocr_text = result.content or ""

        if not result.documents:
            logger.warning("No documents detected for model %s", model_id)
            return ocr_text, {}, {}

        doc = result.documents[0]
        fields = {name: _to_json(field.value) for name, field in doc.fields.items()}
        confidence = {
            name: (field.confidence if field.confidence is not None else 0.0)
            for name, field in doc.fields.items()
        }
        return ocr_text, fields, confidence

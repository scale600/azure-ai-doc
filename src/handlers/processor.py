"""Blob trigger — fires when a document lands in the `documents` container."""

from __future__ import annotations

import logging
import os

import azure.functions as func
from azure.storage.blob import BlobServiceClient

import config
from services.di_client import DocumentIntelligenceClient
from services.openai_client import OpenAIClient
from services.pipeline import process_document
from services.sql_client import SqlClient

logger = logging.getLogger(__name__)


def _read_hint(blob_name: str) -> str | None:
    """Read the document_type_hint from blob metadata (set at upload)."""
    try:
        svc = BlobServiceClient.from_connection_string(config.DOCUMENT_STORAGE_CONNECTION)
        blob_client = svc.get_container_client(config.DOCUMENT_CONTAINER).get_blob_client(
            blob_name
        )
        props = blob_client.get_blob_properties()
        return (props.metadata or {}).get("document_type_hint")
    except Exception:  # noqa: BLE001 — hint is best-effort
        return None


def register(app: func.FunctionApp) -> None:
    @app.blob_trigger(
        arg_name="blob",
        path="documents/{name}",
        connection="DOCUMENT_STORAGE_CONNECTION",
    )
    def process_blob(blob: func.InputStream) -> None:
        name = os.path.basename(blob.name)
        document_id = os.path.splitext(name)[0]
        content = blob.read()

        hint = _read_hint(name)

        di = DocumentIntelligenceClient(
            config.DOCUMENT_INTELLIGENCE_ENDPOINT, config.DOCUMENT_INTELLIGENCE_KEY
        )
        openai = OpenAIClient(
            config.AZURE_OPENAI_ENDPOINT, config.AZURE_OPENAI_KEY, config.AZURE_OPENAI_DEPLOYMENT
        )
        sql = SqlClient(
            config.SQL_SERVER, config.SQL_DATABASE, config.SQL_USER, config.SQL_PASSWORD
        )

        process_document(document_id, name, content, hint, di, openai, sql)

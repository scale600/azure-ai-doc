"""HTTP API handlers: upload / list / get / reprocess / health.

Auth: custom `x-api-key` header (see auth.py). Platform auth level is ANONYMOUS
because we enforce our own key; `/health` is always open.
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from io import BytesIO

import azure.functions as func
from azure.storage.blob import BlobServiceClient
from pypdf import PdfReader

import config
from auth import is_authorized
from models import DocumentStatus
from services.di_client import DocumentIntelligenceClient
from services.openai_client import OpenAIClient
from services.pipeline import process_document
from services.sql_client import SqlClient

logger = logging.getLogger(__name__)

_CORS = {
    "Access-Control-Allow-Origin": config.CORS_ALLOWED_ORIGIN,
    "Access-Control-Allow-Headers": "x-api-key, content-type",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
}


def _json(data, status: int = 200) -> func.HttpResponse:
    return func.HttpResponse(
        json.dumps(data, ensure_ascii=False),
        status_code=status,
        mimetype="application/json",
        headers=_CORS,
    )


def _error(msg: str, status: int = 400) -> func.HttpResponse:
    return _json({"error": msg}, status)


def _sql() -> SqlClient:
    return SqlClient(
        config.SQL_SERVER, config.SQL_DATABASE, config.SQL_USER, config.SQL_PASSWORD
    )


def _ai_clients() -> tuple[DocumentIntelligenceClient, OpenAIClient]:
    return (
        DocumentIntelligenceClient(
            config.DOCUMENT_INTELLIGENCE_ENDPOINT, config.DOCUMENT_INTELLIGENCE_KEY
        ),
        OpenAIClient(
            config.AZURE_OPENAI_ENDPOINT, config.AZURE_OPENAI_KEY, config.AZURE_OPENAI_DEPLOYMENT
        ),
    )


def _upload_blob(blob_name: str, data: bytes, hint: str | None) -> str:
    svc = BlobServiceClient.from_connection_string(config.DOCUMENT_STORAGE_CONNECTION)
    container = svc.get_container_client(config.DOCUMENT_CONTAINER)
    metadata = {"document_type_hint": hint} if hint else None
    return container.upload_blob(blob_name, data, overwrite=True, metadata=metadata).url


def _pdf_page_count(data: bytes) -> int:
    return len(PdfReader(BytesIO(data)).pages)


def _preflight(req: func.HttpRequest) -> func.HttpResponse | None:
    if req.method == "OPTIONS":
        return func.HttpResponse(status_code=200, headers=_CORS)
    return None


def register(app: func.FunctionApp) -> None:
    @app.route(route="health", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
    def health(req: func.HttpRequest) -> func.HttpResponse:
        return _json({"status": "ok"})

    @app.route(
        route="documents",
        methods=["GET", "POST", "OPTIONS"],
        auth_level=func.AuthLevel.ANONYMOUS,
    )
    def documents(req: func.HttpRequest) -> func.HttpResponse:
        pre = _preflight(req)
        if pre is not None:
            return pre
        if not is_authorized(req):
            return _error("unauthorized", 401)

        if req.method == "GET":
            return _json({"documents": _sql().list_documents()})

        file = req.files.get("file")
        if file is None:
            return _error("missing 'file' field", 400)

        data = file.read()
        filename = file.filename or "document"
        ext = os.path.splitext(filename)[1].lower()
        if ext not in config.ALLOWED_EXTENSIONS:
            return _error("unsupported file type", 400)
        if len(data) > config.MAX_UPLOAD_BYTES:
            return _error("file exceeds 4MB limit", 413)

        page_count: int | None = None
        if ext == ".pdf":
            try:
                page_count = _pdf_page_count(data)
            except Exception:
                return _error("invalid PDF", 400)
            if page_count > config.MAX_PAGES:
                return _error("PDF exceeds 2-page limit", 413)

        hint = (req.form.get("document_type") or "").strip() or None
        document_id = str(uuid.uuid4())
        blob_name = f"{document_id}{ext}"

        sql = _sql()
        # Insert the row BEFORE uploading so the blob trigger never sees a
        # missing Documents row (avoids a race).
        sql.insert_document(document_id, filename, "", len(data), page_count)
        try:
            blob_url = _upload_blob(blob_name, data, hint)
            sql.set_blob_url(document_id, blob_url)
        except Exception:
            sql.update_status(document_id, DocumentStatus.FAILED)
            logger.exception("blob upload failed for %s", document_id)
            return _error("blob upload failed", 500)

        return _json({"documentId": document_id, "status": "ACCEPTED"}, 202)

    @app.route(
        route="documents/{document_id}",
        methods=["GET", "OPTIONS"],
        auth_level=func.AuthLevel.ANONYMOUS,
    )
    def get_document(req: func.HttpRequest) -> func.HttpResponse:
        pre = _preflight(req)
        if pre is not None:
            return pre
        if not is_authorized(req):
            return _error("unauthorized", 401)
        document_id = req.route_params.get("document_id")
        doc = _sql().get_document(document_id)
        if doc is None:
            return _error("not found", 404)
        return _json(doc)

    @app.route(
        route="documents/{document_id}/reprocess",
        methods=["POST", "OPTIONS"],
        auth_level=func.AuthLevel.ANONYMOUS,
    )
    def reprocess(req: func.HttpRequest) -> func.HttpResponse:
        pre = _preflight(req)
        if pre is not None:
            return pre
        if not is_authorized(req):
            return _error("unauthorized", 401)

        document_id = req.route_params.get("document_id")
        sql = _sql()
        doc = sql.get_document(document_id)
        if doc is None:
            return _error("not found", 404)

        ext = os.path.splitext(doc["fileName"] or "")[1].lower()
        blob_name = f"{document_id}{ext}"

        svc = BlobServiceClient.from_connection_string(config.DOCUMENT_STORAGE_CONNECTION)
        blob_client = svc.get_container_client(config.DOCUMENT_CONTAINER).get_blob_client(
            blob_name
        )
        if not blob_client.exists():
            return _error("source blob missing", 404)

        props = blob_client.get_blob_properties()
        hint = (props.metadata or {}).get("document_type_hint")
        content = blob_client.download_blob().readall()

        di, openai = _ai_clients()
        sql.update_status(document_id, DocumentStatus.REPROCESSING)
        try:
            # Synchronous reprocess (acceptable for a prototype; see PRD §10).
            process_document(document_id, doc["fileName"], content, hint, di, openai, sql)
        except Exception:
            return _error("reprocessing failed", 500)

        return _json({"documentId": document_id, "status": "ACCEPTED"}, 202)

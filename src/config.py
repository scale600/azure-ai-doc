"""Runtime configuration loaded from environment variables.

In Azure these values are provided as app settings (some via Key Vault
references, resolved automatically by the platform). Locally they come from
`local.settings.json`.
"""

from __future__ import annotations

import os


def _require(name: str) -> str:
    value = os.environ.get(name, "")
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


DOCUMENT_STORAGE_CONNECTION: str = _require("DOCUMENT_STORAGE_CONNECTION")
DOCUMENT_CONTAINER: str = os.environ.get("DOCUMENT_CONTAINER", "documents")

DOCUMENT_INTELLIGENCE_ENDPOINT: str = _require("DOCUMENT_INTELLIGENCE_ENDPOINT")
DOCUMENT_INTELLIGENCE_KEY: str = _require("DOCUMENT_INTELLIGENCE_KEY")

AZURE_OPENAI_ENDPOINT: str = _require("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_KEY: str = _require("AZURE_OPENAI_KEY")
AZURE_OPENAI_DEPLOYMENT: str = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1-mini")

SQL_SERVER: str = _require("SQL_SERVER")
SQL_DATABASE: str = _require("SQL_DATABASE")
SQL_USER: str = _require("SQL_USER")
SQL_PASSWORD: str = _require("SQL_PASSWORD")

# API key for the HTTP API (empty = auth disabled, local dev only).
API_KEY: str = os.environ.get("API_KEY", "")

CORS_ALLOWED_ORIGIN: str = os.environ.get("CORS_ALLOWED_ORIGIN", "*")

MAX_UPLOAD_BYTES: int = 4 * 1024 * 1024  # 4MB
MAX_PAGES: int = 2
ALLOWED_EXTENSIONS: frozenset[str] = frozenset({".pdf", ".png", ".jpg", ".jpeg"})

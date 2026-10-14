"""Shared API-key authorization helper for the HTTP endpoints."""

from __future__ import annotations

import azure.functions as func

import config


def is_authorized(req: func.HttpRequest) -> bool:
    """Validate the `x-api-key` header against the configured API_KEY.

    Empty API_KEY (local dev) disables the check.
    """
    if not config.API_KEY:
        return True
    supplied = req.headers.get("x-api-key", "")
    return supplied == config.API_KEY


def unauthorized() -> func.HttpResponse:
    return func.HttpResponse(
        '{"error": "unauthorized"}',
        status_code=401,
        mimetype="application/json",
    )

"""Azure OpenAI client for classification / summary / risk-signal generation."""

from __future__ import annotations

import json
import logging

from openai import AzureOpenAI

from models import AIInsight

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are an AI assistant for a financial-institution document processing "
    "pipeline. Use only the provided OCR text and extracted fields. Do not "
    "invent values. If uncertain, mark confidence as low. Return JSON only."
)

_USER_PROMPT_TEMPLATE = """Document type hint: {hint}
Extracted fields: {fields_json}
OCR text: {ocr_text}

Return (camelCase, JSON only):
{{
  "classification": "",
  "summary": "",
  "keyFields": {{}},
  "riskFlags": [],
  "missingFields": [],
  "recommendedAction": "",
  "confidence": 0.0
}}"""


class OpenAIClient:
    def __init__(self, endpoint: str, key: str, deployment: str) -> None:
        self.deployment = deployment
        self._client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=key,
            api_version="2024-06-01",
        )

    def generate_insight(
        self, ocr_text: str, fields: dict, hint: str | None
    ) -> tuple[AIInsight, int, int]:
        """Return (insight, tokens_in, tokens_out). Raises on schema failure."""
        user_prompt = _USER_PROMPT_TEMPLATE.format(
            hint=hint or "unknown",
            fields_json=json.dumps(fields, ensure_ascii=False),
            ocr_text=ocr_text[:32000],
        )

        response = self._client.chat.completions.create(
            model=self.deployment,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content or "{}"
        usage = response.usage
        tokens_in = usage.prompt_tokens if usage else 0
        tokens_out = usage.completion_tokens if usage else 0

        # Strict validation — a malformed response raises and is retried/handled
        # upstream rather than silently stored.
        insight = AIInsight.model_validate_json(content)
        return insight, tokens_in, tokens_out

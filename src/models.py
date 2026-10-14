"""Pydantic schemas (camelCase normalization per PRD §11.3)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class AIInsight(BaseModel):
    """Normalized LLM output. Keys are camelCase and validated strictly."""

    model_config = ConfigDict(extra="forbid")

    classification: str = ""
    summary: str = ""
    keyFields: dict = Field(default_factory=dict)
    riskFlags: list[str] = Field(default_factory=list)
    missingFields: list[str] = Field(default_factory=list)
    recommendedAction: str = ""
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class ExtractionResult(BaseModel):
    """Fields + confidence returned by Document Intelligence."""

    modelId: str
    fields: dict = Field(default_factory=dict)
    confidence: dict = Field(default_factory=dict)


class DocumentStatus:
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REJECTED = "REJECTED"
    REPROCESSING = "REPROCESSING"

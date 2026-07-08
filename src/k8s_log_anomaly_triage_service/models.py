from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

Severity = Literal["low", "medium", "high", "critical"]
ReplayStatus = Literal["pass", "watch", "page"]


class LogEvent(BaseModel):
    timestamp: str | None = None
    namespace: str = Field(default="default", min_length=1)
    pod: str = Field(default="unknown", min_length=1)
    container: str = Field(default="app", min_length=1)
    message: str = Field(min_length=1)


class TriageRequest(BaseModel):
    service: str = Field(default="unknown-service", min_length=1)
    environment: str = Field(default="staging", min_length=1)
    logs: list[LogEvent] = Field(min_length=1)


class Finding(BaseModel):
    category: str
    severity: Severity
    score: float = Field(ge=0)
    evidence_count: int = Field(ge=0)
    example: str
    recommendation: str


class TriageResponse(BaseModel):
    service: str
    environment: str
    risk_score: float = Field(ge=0, le=100)
    incident_class: str
    summary: str
    findings: list[Finding]
    runbook_steps: list[str]
    metrics: dict[str, Any]


class ReplayWindow(BaseModel):
    window_id: str = Field(min_length=1)
    service: str = Field(min_length=1)
    environment: str = Field(min_length=1)
    logs: list[LogEvent] = Field(min_length=1)


class ReplayManifest(BaseModel):
    incident_id: str = Field(min_length=1)
    owner: str = Field(default="platform-oncall", min_length=1)
    windows: list[ReplayWindow] = Field(min_length=1)


class ReplayWindowResult(BaseModel):
    window_id: str
    service: str
    environment: str
    risk_score: float = Field(ge=0, le=100)
    incident_class: str
    findings: int = Field(ge=0)
    summary: str


class ReplayReviewResponse(BaseModel):
    incident_id: str
    owner: str
    status: ReplayStatus
    summary: str
    reviewed_windows: int = Field(ge=0)
    page_windows: int = Field(ge=0)
    highest_risk_score: float = Field(ge=0, le=100)
    dominant_incident_class: str
    recurring_incident_classes: list[str]
    windows: list[ReplayWindowResult]
    recommended_actions: list[str]

from __future__ import annotations

import logging

from fastapi import FastAPI

from .models import TriageRequest, TriageResponse
from .observability import (
    MetricsMiddleware,
    TRIAGE_REQUESTS,
    TRIAGE_RISK_SCORE,
    configure_logging,
    metrics_response,
)
from .rules import triage_logs

configure_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Kubernetes Log Anomaly Triage Service",
    version="0.1.0",
    description="Scores Kubernetes logs, classifies likely incident mode, and returns runbook steps.",
)
app.add_middleware(MetricsMiddleware)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/triage", response_model=TriageResponse)
def triage(request: TriageRequest) -> TriageResponse:
    result = triage_logs(request.service, request.environment, request.logs)
    TRIAGE_REQUESTS.labels(
        service=request.service,
        environment=request.environment,
        incident_class=result.incident_class,
    ).inc()
    TRIAGE_RISK_SCORE.observe(result.risk_score)
    logger.info(
        "triage_completed",
        extra={
            "service": request.service,
            "environment": request.environment,
            "incident_class": result.incident_class,
            "risk_score": result.risk_score,
            "log_events": len(request.logs),
        },
    )
    return result


@app.get("/metrics")
def metrics():
    return metrics_response()

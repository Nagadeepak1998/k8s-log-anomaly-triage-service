from __future__ import annotations

import logging

from fastapi import FastAPI

from .models import (
    DeploymentTrendManifest,
    DeploymentTrendResponse,
    ReplayManifest,
    ReplayReviewResponse,
    TriageRequest,
    TriageResponse,
)
from .observability import (
    DEPLOYMENT_TREND_REVIEWS,
    MetricsMiddleware,
    REPLAY_REVIEWS,
    TRIAGE_REQUESTS,
    TRIAGE_RISK_SCORE,
    configure_logging,
    metrics_response,
)
from .replay import review_replay
from .rules import triage_logs
from .trends import review_deployment_trends

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


@app.post("/replay", response_model=ReplayReviewResponse)
def replay(request: ReplayManifest) -> ReplayReviewResponse:
    result = review_replay(request)
    REPLAY_REVIEWS.labels(
        status=result.status,
        dominant_incident_class=result.dominant_incident_class,
    ).inc()
    logger.info(
        "replay_review_completed",
        extra={
            "incident_id": request.incident_id,
            "owner": request.owner,
            "status": result.status,
            "reviewed_windows": result.reviewed_windows,
            "highest_risk_score": result.highest_risk_score,
        },
    )
    return result


@app.post("/deployments/trends", response_model=DeploymentTrendResponse)
def deployment_trends(request: DeploymentTrendManifest) -> DeploymentTrendResponse:
    result = review_deployment_trends(request)
    DEPLOYMENT_TREND_REVIEWS.labels(status=result.status).inc()
    logger.info(
        "deployment_trend_review_completed",
        extra={
            "review_id": request.review_id,
            "status": result.status,
            "reviewed_deployments": result.reviewed_deployments,
            "unowned_deployments": result.unowned_deployments,
        },
    )
    return result


@app.get("/metrics")
def metrics():
    return metrics_response()

from __future__ import annotations

import logging
import sys
import time
from collections.abc import Callable

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from pythonjsonlogger import jsonlogger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

TRIAGE_REQUESTS = Counter(
    "k8s_log_triage_requests_total",
    "Total triage requests.",
    ["service", "environment", "incident_class"],
)
TRIAGE_RISK_SCORE = Histogram(
    "k8s_log_triage_risk_score",
    "Distribution of triage risk scores.",
    buckets=(0, 10, 25, 50, 75, 90, 100),
)
HTTP_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency.",
    ["method", "path", "status_code"],
)


def configure_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    handler.setFormatter(formatter)
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.INFO)


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        started = time.perf_counter()
        response = await call_next(request)
        elapsed = time.perf_counter() - started
        HTTP_LATENCY.labels(
            method=request.method,
            path=request.url.path,
            status_code=str(response.status_code),
        ).observe(elapsed)
        return response


def metrics_response() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

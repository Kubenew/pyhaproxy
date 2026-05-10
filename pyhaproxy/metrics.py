"""Prometheus metrics for pyhaproxy."""

from __future__ import annotations

from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response


REQ_COUNT = Counter(
    "pyhaproxy_requests_total",
    "Total HTTP requests handled",
    ["frontend", "backend", "method", "status"],
)

REQ_LATENCY = Histogram(
    "pyhaproxy_request_latency_seconds",
    "Request latency in seconds",
    ["frontend", "backend"],
)


def metrics_response() -> Response:
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)

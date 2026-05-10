"""Starlette ASGI application factory."""

from __future__ import annotations

import time
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response
from starlette.routing import Route

from .frontend import Frontend
from .registry import BackendRegistry
from .proxy import forward
from .metrics import REQ_COUNT, REQ_LATENCY, metrics_response


def create_app(
    frontend: Frontend,
    registry: BackendRegistry,
    metrics_enabled: bool = False,
    metrics_path: str = "/metrics",
) -> Starlette:
    async def handler(request: Request) -> Response:
        start = time.perf_counter()

        backend_name = frontend.resolve_backend(request)
        pool = registry.get(backend_name)

        backend = pool.balancer.next()
        if not backend:
            return PlainTextResponse("No healthy backend servers", status_code=503)

        backend.active_connections += 1
        try:
            resp = await forward(request, backend.url)
        finally:
            backend.active_connections -= 1

        duration = time.perf_counter() - start
        REQ_COUNT.labels(
            frontend=frontend.name,
            backend=backend_name,
            method=request.method,
            status=str(resp.status_code),
        ).inc()
        REQ_LATENCY.labels(frontend=frontend.name, backend=backend_name).observe(duration)

        return resp

    routes = [
        Route(
            "/{path:path}",
            endpoint=handler,
            methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
        )
    ]

    if metrics_enabled:
        async def metrics_endpoint(request: Request) -> Response:
            return metrics_response()

        routes.insert(0, Route(metrics_path, endpoint=metrics_endpoint, methods=["GET"]))

    return Starlette(routes=routes)

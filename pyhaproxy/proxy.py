"""HTTP request forwarding with connection pooling and X-Forwarded-* headers."""

from __future__ import annotations

import httpx
from httpx import Limits
from starlette.requests import Request
from starlette.responses import Response


HOP_BY_HOP_HEADERS = frozenset({
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
})

_client: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    """Return a shared httpx client with connection pooling."""
    global _client
    if _client is None:
        _client = httpx.AsyncClient(
            follow_redirects=False,
            timeout=httpx.Timeout(30.0),
            limits=Limits(max_keepalive_connections=100, max_connections=200),
        )
    return _client


async def close_client() -> None:
    """Gracefully shut down the shared HTTP client."""
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None


def _filter_headers(headers: dict[str, str]) -> dict[str, str]:
    return {k: v for k, v in headers.items() if k.lower() not in HOP_BY_HOP_HEADERS}


def _add_forwarded_headers(headers: dict[str, str], request: Request) -> None:
    headers.setdefault("x-forwarded-for", request.client.host if request.client else "unknown")
    headers.setdefault("x-forwarded-proto", request.url.scheme)
    headers.setdefault("x-forwarded-host", request.headers.get("host", "unknown"))


async def forward(request: Request, backend_url: str) -> Response:
    """Forward an ASGI request to a backend server and return the response."""
    target = backend_url.rstrip("/") + request.url.path
    if request.url.query:
        target += "?" + request.url.query

    body = await request.body()
    client = _get_client()

    req_headers = _filter_headers(dict(request.headers))
    _add_forwarded_headers(req_headers, request)

    resp = await client.request(
        method=request.method,
        url=target,
        headers=req_headers,
        content=body,
    )

    return Response(
        content=resp.content,
        status_code=resp.status_code,
        headers=_filter_headers(dict(resp.headers)),
        media_type=resp.headers.get("content-type"),
    )

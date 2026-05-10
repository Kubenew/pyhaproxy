"""Async HTTP health checks for backend servers.

Checks run concurrently across all servers using ``asyncio.gather``
so a single slow server does not block the others.
"""

from __future__ import annotations

import asyncio
import httpx

from .registry import BackendRegistry


async def _check(url: str, path: str, timeout_seconds: int) -> bool:
    """Return ``True`` if *url + path* returns a 2xx or 3xx status."""
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(timeout_seconds)) as client:
            r = await client.get(url.rstrip("/") + path)
            return 200 <= r.status_code < 400
    except asyncio.CancelledError:
        raise
    except Exception:
        return False


async def _check_all(registry: BackendRegistry, timeout_seconds: int, path: str) -> None:
    servers = registry.all_servers()
    results = await asyncio.gather(
        *(_check(s.url, path, timeout_seconds) for s in servers),
        return_exceptions=True,
    )
    for server, ok in zip(servers, results):
        if isinstance(ok, BaseException) and not isinstance(ok, asyncio.CancelledError):
            server.healthy = False
        else:
            server.healthy = bool(ok)


async def loop(
    registry: BackendRegistry,
    interval_seconds: int,
    timeout_seconds: int,
    path: str,
) -> None:
    """Run health checks in a perpetual loop."""
    while True:
        await _check_all(registry, timeout_seconds, path)
        await asyncio.sleep(interval_seconds)

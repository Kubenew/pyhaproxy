from __future__ import annotations

import asyncio
import httpx

from .registry import BackendRegistry


async def _check(url: str, path: str, timeout_seconds: int) -> bool:
    try:
        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            r = await client.get(url.rstrip("/") + path)
            return 200 <= r.status_code < 400
    except Exception:
        return False


async def loop(registry: BackendRegistry, interval_seconds: int, timeout_seconds: int, path: str):
    while True:
        for backend in registry.all_servers():
            backend.healthy = await _check(backend.url, path, timeout_seconds)
        await asyncio.sleep(interval_seconds)

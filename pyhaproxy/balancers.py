"""Load balancing algorithms."""

from __future__ import annotations

import itertools
from dataclasses import dataclass
from typing import Iterator, Optional


@dataclass
class Backend:
    url: str
    healthy: bool = True
    active_connections: int = 0


class RoundRobinBalancer:
    """Round-robin load balancer that skips unhealthy backends."""

    def __init__(self, backends: list[Backend]) -> None:
        if not backends:
            raise ValueError("Backend pool must have at least one server.")
        self.backends = backends
        self._cycle: Iterator[int] = itertools.cycle(range(len(backends)))

    def next(self) -> Optional[Backend]:
        for _ in range(len(self.backends)):
            idx = next(self._cycle)
            b = self.backends[idx]
            if b.healthy:
                return b
        return None


class LeastConnBalancer:
    """Least-connections load balancer — picks the healthiest backend with
    fewest active connections.
    """

    def __init__(self, backends: list[Backend]) -> None:
        if not backends:
            raise ValueError("Backend pool must have at least one server.")
        self.backends = backends

    def next(self) -> Optional[Backend]:
        healthy = [b for b in self.backends if b.healthy]
        if not healthy:
            return None
        return min(healthy, key=lambda b: b.active_connections)

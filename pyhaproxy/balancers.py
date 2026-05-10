from __future__ import annotations

import itertools
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Backend:
    url: str
    healthy: bool = True
    active_connections: int = 0


class RoundRobinBalancer:
    def __init__(self, backends: List[Backend]):
        if not backends:
            raise ValueError("Backend must have at least one server.")
        self.backends = backends
        self._cycle = itertools.cycle(range(len(backends)))

    def next(self) -> Optional[Backend]:
        for _ in range(len(self.backends)):
            idx = next(self._cycle)
            b = self.backends[idx]
            if b.healthy:
                return b
        return None


class LeastConnBalancer:
    def __init__(self, backends: List[Backend]):
        if not backends:
            raise ValueError("Backend must have at least one server.")
        self.backends = backends

    def next(self) -> Optional[Backend]:
        healthy = [b for b in self.backends if b.healthy]
        if not healthy:
            return None
        return min(healthy, key=lambda b: b.active_connections)

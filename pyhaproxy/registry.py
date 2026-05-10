from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from .balancers import Backend, RoundRobinBalancer, LeastConnBalancer


@dataclass
class BackendPool:
    name: str
    algorithm: str
    balancer: object


class BackendRegistry:
    def __init__(self):
        self._backends: Dict[str, BackendPool] = {}

    def register(self, name: str, algorithm: str, urls: List[str]):
        servers = [Backend(url=u) for u in urls]

        algo = algorithm.lower()
        if algo in ("roundrobin", "rr"):
            balancer = RoundRobinBalancer(servers)
        elif algo in ("leastconn", "lc"):
            balancer = LeastConnBalancer(servers)
        else:
            raise ValueError(f"Unsupported balance algorithm: {algorithm}")

        self._backends[name] = BackendPool(name=name, algorithm=algorithm, balancer=balancer)

    def get(self, name: str) -> BackendPool:
        if name not in self._backends:
            raise KeyError(f"Backend not found: {name}")
        return self._backends[name]

    def all_servers(self) -> List[Backend]:
        out: List[Backend] = []
        for pool in self._backends.values():
            out.extend(pool.balancer.backends)
        return out

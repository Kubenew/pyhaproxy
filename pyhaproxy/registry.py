"""Backend pool registry."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Union

from .balancers import Backend, RoundRobinBalancer, LeastConnBalancer

_Balancer = Union[RoundRobinBalancer, LeastConnBalancer]


@dataclass
class BackendPool:
    name: str
    algorithm: str
    balancer: _Balancer


class BackendRegistry:
    """Maps backend names to load-balanced server pools."""

    def __init__(self) -> None:
        self._backends: dict[str, BackendPool] = {}

    def register(self, name: str, algorithm: str, urls: list[str]) -> None:
        servers = [Backend(url=u) for u in urls]

        algo = algorithm.lower()
        if algo in ("roundrobin", "rr"):
            balancer: _Balancer = RoundRobinBalancer(servers)
        elif algo in ("leastconn", "lc"):
            balancer = LeastConnBalancer(servers)
        else:
            raise ValueError(f"Unsupported balance algorithm: {algorithm}")

        self._backends[name] = BackendPool(name=name, algorithm=algorithm, balancer=balancer)

    def get(self, name: str) -> BackendPool:
        if name not in self._backends:
            raise KeyError(f"Backend not found: {name}")
        return self._backends[name]

    def all_servers(self) -> list[Backend]:
        return [b for pool in self._backends.values() for b in pool.balancer.backends]

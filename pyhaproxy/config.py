"""YAML config parsing and dataclass definitions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

import yaml


@dataclass
class RuleConfig:
    if_expr: str
    backend: str


@dataclass
class FrontendConfig:
    name: str
    bind: str
    default_backend: str
    rules: List[RuleConfig] = field(default_factory=list)


@dataclass
class BackendServerConfig:
    url: str


@dataclass
class BackendConfig:
    name: str
    balance: str = "roundrobin"
    servers: List[BackendServerConfig] = field(default_factory=list)


@dataclass
class MetricsConfig:
    enabled: bool = False
    path: str = "/metrics"


@dataclass
class HealthcheckConfig:
    enabled: bool = False
    interval_seconds: int = 5
    timeout_seconds: int = 2
    path: str = "/health"


@dataclass
class HAConfig:
    frontends: List[FrontendConfig] = field(default_factory=list)
    backends: List[BackendConfig] = field(default_factory=list)
    metrics: MetricsConfig = field(default_factory=MetricsConfig)
    healthcheck: HealthcheckConfig = field(default_factory=HealthcheckConfig)


def load_config(path: str) -> HAConfig:
    """Load and parse a YAML configuration file."""
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    frontends: List[FrontendConfig] = []
    for fe in raw.get("frontends") or []:
        rules = [
            RuleConfig(if_expr=str(r["if"]), backend=str(r["backend"]))
            for r in fe.get("rules") or []
        ]
        frontends.append(FrontendConfig(
            name=str(fe["name"]),
            bind=str(fe["bind"]),
            default_backend=str(fe["default_backend"]),
            rules=rules,
        ))

    backends: List[BackendConfig] = []
    for name, be in (raw.get("backends") or {}).items():
        servers_raw = be.get("servers") or []
        backends.append(BackendConfig(
            name=str(name),
            balance=str(be.get("balance", "roundrobin")),
            servers=[BackendServerConfig(url=str(s["url"])) for s in servers_raw],
        ))

    metrics_raw = raw.get("metrics") or {}
    metrics = MetricsConfig(
        enabled=bool(metrics_raw.get("enabled", False)),
        path=str(metrics_raw.get("path", "/metrics")),
    )

    hc_raw = raw.get("healthcheck") or {}
    healthcheck = HealthcheckConfig(
        enabled=bool(hc_raw.get("enabled", False)),
        interval_seconds=int(hc_raw.get("interval_seconds", 5)),
        timeout_seconds=int(hc_raw.get("timeout_seconds", 2)),
        path=str(hc_raw.get("path", "/health")),
    )

    return HAConfig(
        frontends=frontends,
        backends=backends,
        metrics=metrics,
        healthcheck=healthcheck,
    )

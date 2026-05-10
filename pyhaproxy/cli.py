from __future__ import annotations

import asyncio
import typer
import uvicorn

from .config import load_config
from .frontend import build_frontend
from .registry import BackendRegistry
from .app import create_app
from .healthcheck import loop as healthcheck_loop

app = typer.Typer(help="pyhaproxy - HAProxy-like reverse proxy/load balancer in Python")


@app.command()
def run(config: str = typer.Option(..., "--config", "-c", help="Path to YAML config")):
    cfg = load_config(config)

    if not cfg.frontends:
        raise typer.BadParameter("No frontends configured.")

    frontend_cfg = cfg.frontends[0]

    backend_registry = BackendRegistry()
    for be in cfg.backends:
        backend_registry.register(
            name=be.name,
            algorithm=be.balance,
            urls=[s.url for s in be.servers],
        )

    frontend = build_frontend(
        name=frontend_cfg.name,
        default_backend=frontend_cfg.default_backend,
        rules=[{"if_expr": r.if_expr, "backend": r.backend} for r in frontend_cfg.rules],
    )

    bind = frontend_cfg.bind
    host, port = "0.0.0.0", 9000
    if ":" in bind:
        host, port_str = bind.split(":", 1)
        port = int(port_str)
    else:
        raise typer.BadParameter(f"Invalid bind: {bind}")

    starlette_app = create_app(
        frontend=frontend,
        registry=backend_registry,
        metrics_enabled=cfg.metrics.enabled,
        metrics_path=cfg.metrics.path,
    )

    loop = asyncio.get_event_loop()
    if cfg.healthcheck.enabled:
        loop.create_task(
            healthcheck_loop(
                registry=backend_registry,
                interval_seconds=cfg.healthcheck.interval_seconds,
                timeout_seconds=cfg.healthcheck.timeout_seconds,
                path=cfg.healthcheck.path,
            )
        )

    uvicorn.run(starlette_app, host=host, port=port)


if __name__ == "__main__":
    app()

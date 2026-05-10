"""CLI entry point for pyhaproxy.

Supports multiple frontends — each frontend bind gets its own uvicorn
server running concurrently in the same event loop.
"""

from __future__ import annotations

import asyncio
import typer
import uvicorn

from .config import load_config
from .frontend import build_frontend
from .registry import BackendRegistry
from .app import create_app
from .healthcheck import loop as healthcheck_loop

app = typer.Typer(help="pyhaproxy — HAProxy-like reverse proxy/load balancer in Python")


@app.command()
def run(
    config: str = typer.Option(..., "--config", "-c", help="Path to YAML config"),
    log_level: str = typer.Option("info", "--log-level", "-l", help="uvicorn log level"),
) -> None:
    cfg = load_config(config)

    if not cfg.frontends:
        raise typer.BadParameter("No frontends configured.")

    # Shared backend registry across all frontends
    backend_registry = BackendRegistry()
    for be in cfg.backends:
        backend_registry.register(
            name=be.name,
            algorithm=be.balance,
            urls=[s.url for s in be.servers],
        )

    async def _serve_all() -> None:
        servers: list[uvicorn.Server] = []
        for fe in cfg.frontends:
            if ":" not in fe.bind:
                raise typer.BadParameter(f"Invalid bind '{fe.bind}' — expected host:port")

            host, port_str = fe.bind.rsplit(":", 1)
            port = int(port_str)

            frontend = build_frontend(
                name=fe.name,
                default_backend=fe.default_backend,
                rules=[{"if_expr": r.if_expr, "backend": r.backend} for r in fe.rules],
            )

            starlette_app = create_app(
                frontend=frontend,
                registry=backend_registry,
                metrics_enabled=cfg.metrics.enabled,
                metrics_path=cfg.metrics.path,
            )

            uvi_config = uvicorn.Config(
                app=starlette_app,
                host=host,
                port=port,
                log_level=log_level,
            )
            servers.append(uvicorn.Server(uvi_config))

        if cfg.healthcheck.enabled:
            loop = asyncio.get_running_loop()
            loop.create_task(
                healthcheck_loop(
                    registry=backend_registry,
                    interval_seconds=cfg.healthcheck.interval_seconds,
                    timeout_seconds=cfg.healthcheck.timeout_seconds,
                    path=cfg.healthcheck.path,
                )
            )

        # Run all frontend servers concurrently
        await asyncio.gather(*(s.serve() for s in servers))

    asyncio.run(_serve_all())


if __name__ == "__main__":
    app()

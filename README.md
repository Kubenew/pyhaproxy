# pyhaproxy

[![PyPI](https://img.shields.io/pypi/v/pyhaproxy-lb)](https://pypi.org/project/pyhaproxy-lb/)
[![Python Versions](https://img.shields.io/pypi/pyversions/pyhaproxy-lb)](https://pypi.org/project/pyhaproxy-lb/)
[![License](https://img.shields.io/pypi/l/pyhaproxy-lb)](https://github.com/Kubenew/pyhaproxy/blob/main/LICENSE)
[![Tests](https://img.shields.io/github/actions/workflow/status/Kubenew/pyhaproxy/ci.yml?label=tests)](https://github.com/Kubenew/pyhaproxy/actions)
[![GitHub stars](https://img.shields.io/github/stars/Kubenew/pyhaproxy?style=flat&logo=github)](https://github.com/Kubenew/pyhaproxy)
[![Downloads](https://img.shields.io/pepy.tech/dt/pyhaproxy-lb)](https://pepy.tech/project/pyhaproxy-lb)

**pyhaproxy** is a minimal HAProxy-like reverse proxy and load balancer written in Python.

This is **not** a wrapper around the HAProxy binary. It is a pure Python async implementation focused on extensibility.

## MVP Features

- **Frontends** — bind to multiple host:port pairs, each with its own routing rules
- **ACL-like routing** — route requests by `host` or `path_prefix`
- **Backend pools** — groups of servers behind a single backend name
- **Load balancing** — round-robin and least-connections
- **Health checks** — concurrent async HTTP checks per backend
- **Prometheus metrics** — request count and latency histograms
- **Connection pooling** — shared `httpx.AsyncClient` with keep-alive
- **X-Forwarded-* headers** — automatically added to proxied requests

## Quickstart

```bash
pip install pyhaproxy-lb
```

### Run

```bash
pyhaproxy run -c examples/config.yml
```

### Test

```bash
curl -H "Host: example.com" http://localhost:9000/
curl -H "Host: example.com" http://localhost:9000/api/users
```

## Example Config

```yaml
frontends:
  - name: "http_front"
    bind: "0.0.0.0:9000"
    default_backend: "app_backend"
    rules:
      - if: "host == example.com"
        backend: "app_backend"
      - if: "path_prefix == /api"
        backend: "api_backend"

backends:
  app_backend:
    balance: "roundrobin"
    servers:
      - url: "http://localhost:5000"
      - url: "http://localhost:5001"
  api_backend:
    balance: "leastconn"
    servers:
      - url: "http://localhost:6000"

healthcheck:
  enabled: true
  interval_seconds: 5
  timeout_seconds: 2
  path: "/health"

metrics:
  enabled: true
  path: "/metrics"
```

## Architecture

```
Client ──► Uvicorn ──► Starlette ──► Frontend.resolve_backend()
                                         │
                                    ┌─────▼──────┐
                                    │  ACL rules  │
                                    │ host/path   │
                                    └─────┬──────┘
                                          │ backend name
                                          ▼
                                    BackendRegistry
                                          │
                                    ┌─────▼──────┐
                                    │  Balancer   │
                                    │ RR / Least  │
                                    └─────┬──────┘
                                          │ server URL
                                          ▼
                                   proxy.forward()
                                          │
                                    ┌─────▼──────┐
                                    │  Backend    │
                                    │  server     │
                                    └────────────┘
```

## Changelog

### 0.1.1
- **Multi-frontend support**: CLI now runs all configured frontends concurrently.
- **Connection pooling**: Shared `httpx.AsyncClient` with keep-alive limits (was creating a client per request).
- **Concurrent health checks**: Servers are checked in parallel via `asyncio.gather`.
- **X-Forwarded-* headers**: Proxied requests now include `x-forwarded-for`, `x-forwarded-proto`, `x-forwarded-host`.
- **Better error messages**: Balancer errors say "at least one server".
- **Improved type annotations**: Full type hints on all public classes.
- **Comprehensive tests**: Balancers, config, registry, frontend, ACL, proxy.

## License

MIT

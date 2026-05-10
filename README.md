# pyhaproxy

**pyhaproxy** is a minimal HAProxy-like reverse proxy and load balancer written in Python.

This is NOT a wrapper around the HAProxy binary.
It is a pure Python async implementation focused on extensibility.

## MVP Features
- Frontends (bind host:port)
- ACL-like routing (host/path prefix)
- Backends with server pools
- Load balancing:
  - round-robin
  - least-connections (basic)
- Health checks (optional)
- Prometheus metrics (optional)

## Quickstart

### Install (dev)
```bash
pip install -e .
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

## Roadmap
- TCP mode (L4 proxy)
- Stick tables / session affinity
- Rate limiting + circuit breaker
- TLS termination
- Admin API

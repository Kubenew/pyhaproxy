"""Tests for frontend routing."""

from __future__ import annotations

import pytest
from starlette.requests import Request
from pyhaproxy.frontend import build_frontend, Frontend
from pyhaproxy.acls import ACLRule


def _make_request(host: str = "example.com", path: str = "/") -> Request:
    return Request({
        "type": "http",
        "method": "GET",
        "path": path,
        "headers": [(b"host", host.encode())],
        "query_string": b"",
        "server": ("127.0.0.1", 9000),
        "client": ("127.0.0.1", 12345),
        "scheme": "http",
    })


class TestFrontend:
    def test_resolve_backend_rules_first_match(self):
        fe = Frontend(
            name="test",
            default_backend="default",
            rules=[
                ACLRule(raw="host == a.com", matcher=lambda r: False, backend="never"),
                ACLRule(raw="host == b.com", matcher=lambda r: True, backend="matched"),
            ],
        )
        assert fe.resolve_backend(_make_request()) == "matched"

    def test_resolve_backend_falls_to_default(self):
        fe = Frontend(
            name="test",
            default_backend="fallback",
            rules=[
                ACLRule(raw="host == a.com", matcher=lambda r: False, backend="never"),
            ],
        )
        assert fe.resolve_backend(_make_request()) == "fallback"

    def test_resolve_backend_no_rules(self):
        fe = Frontend(name="test", default_backend="fallback", rules=[])
        assert fe.resolve_backend(_make_request()) == "fallback"


class TestBuildFrontend:
    def test_build_frontend_from_dicts(self):
        fe = build_frontend(
            name="web",
            default_backend="app",
            rules=[
                {"if_expr": "host == example.com", "backend": "web_backend"},
                {"if_expr": "path_prefix == /api", "backend": "api_backend"},
            ],
        )
        assert fe.name == "web"
        assert fe.default_backend == "app"
        assert len(fe.rules) == 2
        assert fe.rules[0].raw == "host == example.com"
        assert fe.rules[0].backend == "web_backend"

    def test_build_frontend_parses_acl_expressions(self):
        fe = build_frontend(
            name="test",
            default_backend="default",
            rules=[{"if_expr": "host == example.com", "backend": "matched"}],
        )
        req = _make_request(host="example.com")
        assert fe.resolve_backend(req) == "matched"

    def test_build_frontend_invalid_acl_raises(self):
        with pytest.raises(ValueError, match="Unsupported ACL expression"):
            build_frontend(
                name="test",
                default_backend="default",
                rules=[{"if_expr": "method == GET", "backend": "x"}],
            )

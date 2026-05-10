"""Tests for ACL parsing and matching."""

from starlette.requests import Request
from pyhaproxy.acls import parse_acl


def _request(host: str = "example.com", path: str = "/") -> Request:
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


class TestACLHost:
    def test_matches_exact_host(self):
        m = parse_acl("host == example.com")
        assert m(_request(host="example.com")) is True

    def test_rejects_different_host(self):
        m = parse_acl("host == example.com")
        assert m(_request(host="other.com")) is False

    def test_strips_port_from_host_header(self):
        m = parse_acl("host == example.com")
        assert m(_request(host="example.com:8080")) is True


class TestACLPathPrefix:
    def test_matches_prefix(self):
        m = parse_acl("path_prefix == /api")
        assert m(_request(path="/api/users")) is True

    def test_rejects_non_matching(self):
        m = parse_acl("path_prefix == /api")
        assert m(_request(path="/")) is False

    def test_matches_root_prefix(self):
        m = parse_acl("path_prefix == /")
        assert m(_request(path="/anything")) is True


class TestACLErrors:
    def test_unsupported_expression(self):
        import pytest
        with pytest.raises(ValueError, match="Unsupported ACL expression"):
            parse_acl("method == GET")

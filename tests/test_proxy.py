"""Tests for HTTP proxy forwarding logic."""

from pyhaproxy.proxy import _filter_headers, HOP_BY_HOP_HEADERS


class TestFilterHeaders:
    def test_removes_hop_by_hop(self):
        headers = {
            "host": "example.com",
            "connection": "keep-alive",
            "content-type": "application/json",
            "transfer-encoding": "chunked",
        }
        result = _filter_headers(headers)
        assert "host" in result
        assert "content-type" in result
        assert "connection" not in result
        assert "transfer-encoding" not in result

    def test_case_insensitive(self):
        headers = {"Connection": "close", "X-Custom": "value"}
        result = _filter_headers(headers)
        assert "Connection" not in result
        assert "X-Custom" in result

    def test_empty_headers(self):
        assert _filter_headers({}) == {}

    def test_all_hop_by_hop(self):
        headers = {h: "x" for h in HOP_BY_HOP_HEADERS}
        assert _filter_headers(headers) == {}

"""Tests for backend registry."""

import pytest
from pyhaproxy.registry import BackendRegistry
from pyhaproxy.balancers import RoundRobinBalancer, LeastConnBalancer


class TestBackendRegistry:
    def test_register_and_get_roundrobin(self):
        reg = BackendRegistry()
        reg.register("web", "roundrobin", ["http://a", "http://b"])

        pool = reg.get("web")
        assert pool.name == "web"
        assert isinstance(pool.balancer, RoundRobinBalancer)
        assert len(pool.balancer.backends) == 2

    def test_register_and_get_leastconn(self):
        reg = BackendRegistry()
        reg.register("api", "leastconn", ["http://c"])

        pool = reg.get("api")
        assert isinstance(pool.balancer, LeastConnBalancer)

    def test_register_rr_alias(self):
        reg = BackendRegistry()
        reg.register("web", "rr", ["http://a"])
        assert isinstance(reg.get("web").balancer, RoundRobinBalancer)

    def test_register_lc_alias(self):
        reg = BackendRegistry()
        reg.register("api", "lc", ["http://a"])
        assert isinstance(reg.get("api").balancer, LeastConnBalancer)

    def test_get_unknown_backend_raises(self):
        reg = BackendRegistry()
        with pytest.raises(KeyError, match="not found"):
            reg.get("nonexistent")

    def test_unsupported_algorithm_raises(self):
        reg = BackendRegistry()
        with pytest.raises(ValueError, match="Unsupported"):
            reg.register("bad", "random", ["http://a"])

    def test_all_servers(self):
        reg = BackendRegistry()
        reg.register("a", "roundrobin", ["http://a1", "http://a2"])
        reg.register("b", "roundrobin", ["http://b1"])

        servers = reg.all_servers()
        assert len(servers) == 3
        urls = {s.url for s in servers}
        assert urls == {"http://a1", "http://a2", "http://b1"}

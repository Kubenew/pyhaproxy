"""Tests for load balancing algorithms."""

import pytest
from pyhaproxy.balancers import Backend, RoundRobinBalancer, LeastConnBalancer


class TestRoundRobinBalancer:
    def test_cycles_through_backends(self):
        b1 = Backend(url="http://a")
        b2 = Backend(url="http://b")
        balancer = RoundRobinBalancer([b1, b2])

        assert balancer.next() is b1
        assert balancer.next() is b2
        assert balancer.next() is b1

    def test_skips_unhealthy(self):
        b1 = Backend(url="http://a", healthy=False)
        b2 = Backend(url="http://b")
        balancer = RoundRobinBalancer([b1, b2])

        assert balancer.next() is b2
        assert balancer.next() is b2  # stays on the only healthy one

    def test_returns_none_when_all_unhealthy(self):
        b1 = Backend(url="http://a", healthy=False)
        balancer = RoundRobinBalancer([b1])
        assert balancer.next() is None

    def test_empty_backends_raises(self):
        with pytest.raises(ValueError, match="at least one server"):
            RoundRobinBalancer([])

    def test_single_backend(self):
        b1 = Backend(url="http://a")
        balancer = RoundRobinBalancer([b1])
        assert balancer.next() is b1
        assert balancer.next() is b1  # repeat


class TestLeastConnBalancer:
    def test_picks_least_loaded(self):
        b1 = Backend(url="http://a", active_connections=5)
        b2 = Backend(url="http://b", active_connections=2)
        b3 = Backend(url="http://c", active_connections=10)
        balancer = LeastConnBalancer([b1, b2, b3])

        assert balancer.next() is b2

    def test_skips_unhealthy(self):
        b1 = Backend(url="http://a", healthy=False, active_connections=0)
        b2 = Backend(url="http://b", active_connections=3)
        balancer = LeastConnBalancer([b1, b2])

        assert balancer.next() is b2

    def test_returns_none_when_all_unhealthy(self):
        b1 = Backend(url="http://a", healthy=False)
        balancer = LeastConnBalancer([b1])
        assert balancer.next() is None

    def test_empty_backends_raises(self):
        with pytest.raises(ValueError, match="at least one server"):
            LeastConnBalancer([])

    def test_ties_pick_first(self):
        b1 = Backend(url="http://a", active_connections=3)
        b2 = Backend(url="http://b", active_connections=3)
        balancer = LeastConnBalancer([b1, b2])

        assert balancer.next() is b1  # min returns first of ties

"""Tests for YAML config loading."""

import os
import tempfile

import pytest
import yaml

from pyhaproxy.config import load_config, HAConfig


SAMPLE_CONFIG = {
    "frontends": [
        {
            "name": "http_front",
            "bind": "0.0.0.0:9000",
            "default_backend": "app_backend",
            "rules": [
                {"if": "host == example.com", "backend": "app_backend"},
            ],
        },
    ],
    "backends": {
        "app_backend": {
            "balance": "roundrobin",
            "servers": [
                {"url": "http://localhost:5000"},
                {"url": "http://localhost:5001"},
            ],
        },
    },
    "metrics": {"enabled": True, "path": "/metrics"},
    "healthcheck": {
        "enabled": True,
        "interval_seconds": 10,
        "timeout_seconds": 3,
        "path": "/healthz",
    },
}


def _write_config(data: dict) -> str:
    fd, path = tempfile.mkstemp(suffix=".yml", text=True)
    with os.fdopen(fd, "w") as f:
        yaml.dump(data, f)
    return path


class TestLoadConfig:
    def test_full_config(self):
        path = _write_config(SAMPLE_CONFIG)
        try:
            cfg = load_config(path)
            assert isinstance(cfg, HAConfig)
            assert len(cfg.frontends) == 1
            assert cfg.frontends[0].name == "http_front"
            assert cfg.frontends[0].bind == "0.0.0.0:9000"
            assert len(cfg.frontends[0].rules) == 1
            assert cfg.frontends[0].rules[0].if_expr == "host == example.com"

            assert len(cfg.backends) == 1
            assert cfg.backends[0].name == "app_backend"
            assert cfg.backends[0].balance == "roundrobin"
            assert len(cfg.backends[0].servers) == 2

            assert cfg.metrics.enabled is True
            assert cfg.metrics.path == "/metrics"

            assert cfg.healthcheck.enabled is True
            assert cfg.healthcheck.interval_seconds == 10
            assert cfg.healthcheck.timeout_seconds == 3
            assert cfg.healthcheck.path == "/healthz"
        finally:
            os.unlink(path)

    def test_empty_config_uses_defaults(self):
        path = _write_config({})
        try:
            cfg = load_config(path)
            assert cfg.frontends == []
            assert cfg.backends == []
            assert cfg.metrics.enabled is False
            assert cfg.metrics.path == "/metrics"
            assert cfg.healthcheck.enabled is False
        finally:
            os.unlink(path)

    def test_no_frontends_or_backends(self):
        path = _write_config({"metrics": {"enabled": False}})
        try:
            cfg = load_config(path)
            assert cfg.frontends == []
            assert cfg.backends == []
        finally:
            os.unlink(path)

    def test_multiple_frontends(self):
        data = {
            "frontends": [
                {"name": "web", "bind": "0.0.0.0:8080", "default_backend": "web_backend"},
                {"name": "api", "bind": "0.0.0.0:8081", "default_backend": "api_backend"},
            ],
            "backends": {
                "web_backend": {"servers": [{"url": "http://localhost:5000"}]},
                "api_backend": {"servers": [{"url": "http://localhost:6000"}]},
            },
        }
        path = _write_config(data)
        try:
            cfg = load_config(path)
            assert len(cfg.frontends) == 2
            assert cfg.frontends[0].name == "web"
            assert cfg.frontends[1].name == "api"
            assert len(cfg.backends) == 2
        finally:
            os.unlink(path)

    def test_missing_file_raises(self):
        with pytest.raises(FileNotFoundError):
            load_config("/nonexistent/path.yml")

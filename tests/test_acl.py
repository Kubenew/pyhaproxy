from starlette.requests import Request
from pyhaproxy.acls import parse_acl


def make_request(host: str, path: str):
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


def test_acl_host():
    m = parse_acl("host == example.com")
    assert m(make_request("example.com", "/")) is True
    assert m(make_request("other.com", "/")) is False


def test_acl_path_prefix():
    m = parse_acl("path_prefix == /api")
    assert m(make_request("example.com", "/api/users")) is True
    assert m(make_request("example.com", "/")) is False

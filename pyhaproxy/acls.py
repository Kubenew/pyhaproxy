"""ACL rule parsing and request matching."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from starlette.requests import Request


@dataclass
class ACLRule:
    raw: str
    matcher: Callable[[Request], bool]
    backend: str


def parse_acl(expr: str) -> Callable[[Request], bool]:
    """Parse an ACL expression string into a callable matcher.

    Supported forms::

        host == example.com
        path_prefix == /api
    """
    expr = expr.strip()

    if expr.startswith("host =="):
        host = expr.split("==", 1)[1].strip()

        def match(req: Request) -> bool:
            return (req.headers.get("host") or "").split(":")[0] == host

        return match

    if expr.startswith("path_prefix =="):
        prefix = expr.split("==", 1)[1].strip()

        def match(req: Request) -> bool:
            return req.url.path.startswith(prefix)

        return match

    raise ValueError(f"Unsupported ACL expression: {expr}")

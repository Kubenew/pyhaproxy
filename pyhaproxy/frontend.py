"""Frontend definition with ACL-based routing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from starlette.requests import Request

from .acls import ACLRule, parse_acl


@dataclass
class Frontend:
    name: str
    default_backend: str
    rules: List[ACLRule]

    def resolve_backend(self, request: Request) -> str:
        """Return the first matching backend name, or *default_backend*."""
        for r in self.rules:
            if r.matcher(request):
                return r.backend
        return self.default_backend


def build_frontend(name: str, default_backend: str, rules: List[Dict[str, str]]) -> Frontend:
    parsed: List[ACLRule] = []
    for r in rules:
        matcher = parse_acl(r["if_expr"])
        parsed.append(ACLRule(raw=r["if_expr"], matcher=matcher, backend=r["backend"]))

    return Frontend(name=name, default_backend=default_backend, rules=parsed)

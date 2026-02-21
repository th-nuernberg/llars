"""
Static route protection checks.

Ensures every Flask route is either protected by an auth/permission decorator
or explicitly marked as public.
"""

from __future__ import annotations

import ast
from pathlib import Path


ROUTE_DECORATORS = {"route", "get", "post", "put", "patch", "delete"}
PROTECTION_DECORATORS = {
    "authentik_required",
    "admin_required",
    "roles_required",
    "require_permission",
    "require_any_permission",
    "require_all_permissions",
    "debug_route_protected",
    "system_api_key_required",
    "jwt_required",
    "optional_auth",
    "public_endpoint",
}

IGNORED_ROUTE_FILES = {
    Path("RatingRoutes.py"),
    Path("RankingRoutes.py"),
    Path("PermissionRoutes.py"),
    Path("LLMComparisonRoutes.py"),
    Path("UserPromptRoutes.py"),
    Path("llm_routes.py"),
    Path("routes.py"),
}


def _decorator_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Call):
        return _decorator_name(node.func)
    return None


def _is_route_decorator(node: ast.AST) -> bool:
    name = _decorator_name(node)
    return name in ROUTE_DECORATORS


def _has_protection(decorators: list[ast.AST]) -> bool:
    for decorator in decorators:
        name = _decorator_name(decorator)
        if name in PROTECTION_DECORATORS:
            return True
    return False


def test_routes_are_protected_or_public():
    repo_root = Path(__file__).resolve().parents[2]
    routes_root = repo_root / "app" / "routes"

    missing = []

    for path in routes_root.rglob("*.py"):
        rel_path = path.relative_to(routes_root)
        if rel_path in IGNORED_ROUTE_FILES:
            continue
        if path.name == "__init__.py":
            continue

        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(rel_path))

        for node in tree.body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if not node.decorator_list:
                continue

            if not any(_is_route_decorator(dec) for dec in node.decorator_list):
                continue

            if not _has_protection(node.decorator_list):
                missing.append(f"{rel_path}:{node.name}")

    assert not missing, (
        "Routes missing protection decorators:\n" + "\n".join(sorted(missing))
    )

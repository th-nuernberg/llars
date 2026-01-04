"""Admin DB explorer helpers (read-only)."""

from __future__ import annotations

import re
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import inspect, text

from db.database import db


class DbExplorerService:
    """Read-only helpers for inspecting and sampling the LLARS MariaDB database."""

    _TABLE_RE = re.compile(r"^[A-Za-z0-9_]+$")

    @classmethod
    def list_tables(cls) -> List[str]:
        inspector = inspect(db.engine)
        tables = inspector.get_table_names() or []
        # Filter obvious internal tables but keep migrations for debugging if needed.
        return sorted([t for t in tables if t])

    @classmethod
    def _validate_table(cls, table: str) -> str:
        name = str(table or "").strip()
        if not name or not cls._TABLE_RE.match(name):
            raise ValueError("Invalid table name")
        if name not in cls.list_tables():
            raise ValueError("Unknown table")
        return name

    @staticmethod
    def _json_safe(value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, (bool, int, float, str)):
            return value
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        if isinstance(value, Decimal):
            try:
                return float(value)
            except Exception:
                return str(value)
        if isinstance(value, (bytes, bytearray, memoryview)):
            try:
                return bytes(value).hex()
            except Exception:
                return "<bytes>"
        return str(value)

    @classmethod
    def get_table_snapshot(
        cls,
        *,
        table: str,
        limit: int = 50,
    ) -> Dict[str, Any]:
        name = cls._validate_table(table)
        limit = max(1, min(200, int(limit or 50)))

        inspector = inspect(db.engine)
        columns_info = inspector.get_columns(name) or []
        columns = [c.get("name") for c in columns_info if c.get("name")]

        pk_cols: List[str] = []
        try:
            pk = inspector.get_pk_constraint(name) or {}
            pk_cols = [c for c in (pk.get("constrained_columns") or []) if c]
        except Exception:
            pk_cols = []

        order_by = pk_cols[0] if pk_cols else None

        sql = f"SELECT * FROM `{name}`"
        if order_by:
            sql += f" ORDER BY `{order_by}` DESC"
        sql += " LIMIT :limit"

        result = db.session.execute(text(sql), {"limit": limit})
        rows = []
        for row in result.mappings().all():
            rows.append({k: cls._json_safe(v) for k, v in dict(row).items()})

        return {
            "ok": True,
            "table": name,
            "columns": columns,
            "rows": rows,
            "order_by": order_by,
            "limit": limit,
            "error": None,
        }


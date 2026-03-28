"""Filter prefix parser for TRCFBaseModule list queries.

Supports prefix syntax: [=], [>], [>=], [<], [<=], [!=], [IN], [NOT IN], [LIKE], [BETWEEN]
Example: ?price=[>=]25000 → Column.price >= 25000
"""

from __future__ import annotations

import re
from typing import Any

from sqlalchemy import Column


# Regex pattern for filter prefix syntax: [operator]value
_PREFIX_RE = re.compile(r"^\[(>=?|<=?|!=?|IN|NOT IN|LIKE|BETWEEN)\](.+)$", re.IGNORECASE)


def parse_filter_value(raw_value: str) -> tuple[str, str]:
    """Parse a query parameter value into (operator, value).

    Args:
        raw_value: Raw query string value, e.g. "[>=]25000" or "coffee"

    Returns:
        (operator, cleaned_value) — operator defaults to "=" if no prefix
    """
    match = _PREFIX_RE.match(raw_value)
    if match:
        return match.group(1).upper(), match.group(2)
    return "=", raw_value


def apply_filter(column: Column, operator: str, value: str) -> Any:  # type: ignore[type-arg]
    """Apply a filter operator to a SQLAlchemy column.

    Args:
        column: SQLAlchemy Column object
        operator: One of =, >, >=, <, <=, !=, IN, NOT IN, LIKE, BETWEEN
        value: String value to compare against

    Returns:
        SQLAlchemy filter expression (BinaryExpression)

    All comparisons use parameterized queries (SQLAlchemy column operators).
    NEVER string-concatenated SQL.
    """
    match operator:
        case "=":
            return column == _cast(column, value)
        case ">":
            return column > _cast(column, value)
        case ">=":
            return column >= _cast(column, value)
        case "<":
            return column < _cast(column, value)
        case "<=":
            return column <= _cast(column, value)
        case "!=":
            return column != _cast(column, value)
        case "IN":
            values = [_cast(column, v.strip()) for v in value.split(",")]
            return column.in_(values)
        case "NOT IN":
            values = [_cast(column, v.strip()) for v in value.split(",")]
            return column.notin_(values)
        case "LIKE":
            return column.ilike(f"%{value}%")
        case "BETWEEN":
            parts = value.split(",")
            if len(parts) != 2:
                raise ValueError(f"BETWEEN requires 2 values, got {len(parts)}")
            return column.between(_cast(column, parts[0].strip()), _cast(column, parts[1].strip()))
        case _:
            raise ValueError(f"Unknown filter operator: {operator}")


def _cast(column: Column, value: str) -> Any:  # type: ignore[type-arg]
    """Cast string value to match column type for parameterized comparison."""
    try:
        col_type = str(column.type)
        if "INT" in col_type:
            return int(value)
        if "FLOAT" in col_type or "NUMERIC" in col_type or "DECIMAL" in col_type:
            return float(value)
        if "BOOL" in col_type:
            return value.lower() in ("true", "1", "yes")
        return value
    except (ValueError, TypeError):
        return value

"""Schema factory — convert TRCFBaseModule field definitions to Pydantic models."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, create_model

from base.fields import (
    BaseField,
    BooleanField,
    ComputedField,
    DateField,
    DateTimeField,
    DecimalField,
    ForeignKeyField,
    IntField,
    ManyToManyField,
    SelectionField,
)


def _pydantic_type(field_def: BaseField) -> tuple[type, Any]:
    """Return (type, default) tuple for Pydantic create_model.

    Returns:
        (python_type, default_value_or_ellipsis)
    """
    py_type = field_def.python_type

    # Handle optional fields
    if not field_def.required:
        if isinstance(field_def, ManyToManyField):
            return (list[int], [])
        if isinstance(field_def, BooleanField):
            return (bool, field_def.default if field_def.default is not None else False)
        return (py_type | None, field_def.default)  # type: ignore[return-value]

    # Required fields
    if isinstance(field_def, ManyToManyField):
        return (list[int], ...)
    return (py_type, ...)


def _pydantic_type_for_update(field_def: BaseField) -> tuple[type, Any]:
    """Return (type, default) for Update schema — all fields optional."""
    py_type = field_def.python_type

    if isinstance(field_def, ManyToManyField):
        return (list[int] | None, None)
    if isinstance(field_def, BooleanField):
        return (bool | None, None)
    return (py_type | None, None)  # type: ignore[return-value]


def create_schemas(
    module_name: str,
    fields: dict[str, BaseField],
    *,
    readonly_fields: list[str] | None = None,
) -> tuple[type[BaseModel], type[BaseModel], type[BaseModel]]:
    """Generate Create, Update, and Response Pydantic models.

    Args:
        module_name: Module _name (e.g. "categories")
        fields: dict of field_name -> BaseField instance
        readonly_fields: Fields excluded from Update schema

    Returns:
        (CreateSchema, UpdateSchema, ResponseSchema)
    """
    readonly_fields = readonly_fields or []

    # ── Create Schema ────────────────────────────────────────────────────
    create_fields: dict[str, Any] = {}
    for name, field_def in fields.items():
        create_fields[name] = _pydantic_type(field_def)

    CreateSchema = create_model(
        f"{module_name.title().replace('_', '')}Create",
        **create_fields,
    )

    # ── Update Schema — all optional, exclude readonly ───────────────────
    update_fields: dict[str, Any] = {}
    for name, field_def in fields.items():
        if name in readonly_fields:
            continue
        update_fields[name] = _pydantic_type_for_update(field_def)

    UpdateSchema = create_model(
        f"{module_name.title().replace('_', '')}Update",
        **update_fields,
    )

    # ── Response Schema — includes auto columns ──────────────────────────
    response_fields: dict[str, Any] = {
        "id": (int, ...),
        "created_at": (datetime, ...),
        "updated_at": (datetime, ...),
        "created_by": (int | None, None),
        "updated_by": (int | None, None),
        "active": (bool, True),  # Archive status — frontend needs this
    }

    for name, field_def in fields.items():
        if isinstance(field_def, ManyToManyField):
            response_fields[name] = (list[int], [])
        else:
            py_type = field_def.python_type
            if not field_def.required:
                response_fields[name] = (py_type | None, None)
            else:
                response_fields[name] = (py_type, ...)

    ResponseSchema = create_model(
        f"{module_name.title().replace('_', '')}Response",
        **response_fields,
    )

    return CreateSchema, UpdateSchema, ResponseSchema  # type: ignore[return-value]

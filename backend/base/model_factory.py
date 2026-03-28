"""Model factory — convert TRCFBaseModule field definitions to SQLAlchemy model."""

from __future__ import annotations

from typing import Any

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Table,
    func,
    text,
)

from app.database import Base
from base.fields import BaseField, ForeignKeyField, ManyToManyField


def create_sa_model(
    module_name: str,
    fields: dict[str, BaseField],
    *,
    archive: bool = True,
    optimistic_lock: bool = False,
) -> type:
    """Dynamically create a SQLAlchemy model class.

    Args:
        module_name: Table name / module _name (e.g. "categories")
        fields: dict of field_name -> BaseField instance
        archive: Whether to add `active` column
        optimistic_lock: Whether to add `version` column

    Returns:
        A SQLAlchemy model class inheriting from Base.
    """
    attrs: dict[str, Any] = {
        "__tablename__": module_name,
    }

    # ── Auto columns ─────────────────────────────────────────────────────
    attrs["id"] = Column(Integer, primary_key=True, autoincrement=True)
    attrs["created_at"] = Column(
        DateTime, server_default=func.now(), nullable=False
    )
    attrs["updated_at"] = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
    attrs["created_by"] = Column(Integer, nullable=True)
    attrs["updated_by"] = Column(Integer, nullable=True)

    if archive:
        attrs["active"] = Column(Boolean, default=True, server_default="1", nullable=False)

    if optimistic_lock:
        attrs["version"] = Column(Integer, default=1, server_default="1", nullable=False)

    # ── User-defined fields ──────────────────────────────────────────────
    m2m_tables: dict[str, Table] = {}

    for field_name, field_def in fields.items():
        if isinstance(field_def, ManyToManyField):
            # Create junction table
            junction_name = f"{module_name}_{field_def.to}"
            junction = Table(
                junction_name,
                Base.metadata,
                Column(
                    f"{module_name[:-1]}_id" if module_name.endswith("s") else f"{module_name}_id",
                    Integer,
                    ForeignKey(f"{module_name}.id", ondelete="CASCADE"),
                    primary_key=True,
                ),
                Column(
                    f"{field_def.to[:-1]}_id" if field_def.to.endswith("s") else f"{field_def.to}_id",
                    Integer,
                    ForeignKey(f"{field_def.to}.id", ondelete="CASCADE"),
                    primary_key=True,
                ),
                extend_existing=True,
            )
            m2m_tables[field_name] = junction
            continue

        if isinstance(field_def, ForeignKeyField):
            # FK column with ForeignKey constraint
            fk_target = f"{field_def.to}.id"
            attrs[field_name] = Column(
                field_def.sa_type,
                ForeignKey(fk_target, ondelete=field_def.on_delete),
                nullable=not field_def.required,
                index=True,
            )
            continue

        # Regular field
        sa_type = field_def.sa_type
        if sa_type is not None:
            attrs[field_name] = Column(
                sa_type,
                **field_def.sa_column_kwargs(),
            )

    # Store junction table references for M2M handling
    attrs["_m2m_tables"] = m2m_tables

    # ── Partial unique index for archive + unique (C2) ───────────────────
    # When archive=True and a field has unique=True, create a partial index
    # so that archived records (active=False) don't block unique constraint.
    # PostgreSQL: CREATE UNIQUE INDEX ... WHERE active = true
    # SQLite/others: falls back to regular unique (from sa_column_kwargs)
    table_args: list[Any] = []
    if archive:
        for field_name, field_def in fields.items():
            if isinstance(field_def, (ForeignKeyField, ManyToManyField)):
                continue
            if field_def.unique:
                table_args.append(
                    Index(
                        f"ix_{module_name}_{field_name}_active",
                        field_name,
                        unique=True,
                        postgresql_where=text("active = true"),
                    )
                )
    if table_args:
        attrs["__table_args__"] = tuple(table_args)

    # Create the model class
    model_cls = type(module_name.title().replace("_", ""), (Base,), attrs)
    return model_cls

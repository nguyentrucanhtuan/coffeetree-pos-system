"""Generic async CRUD handler functions for TRCFBaseModule.

T033: Auto-filterable system columns
T035: FK existence validation before create/update
T038: SelectionField options validation
T041: Eager FK eager-load in GET/LIST responses
T046-T047: Computed field integration (non-stored + stored)
T050: Bulk upsert (update if id exists, create if not)
"""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException, Request, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from base.filters import apply_filter, parse_filter_value
from base.fields import ForeignKeyField, SelectionField, BaseField, ComputedField, ManyToManyField, OneToManyField

# System columns that can always be filtered (T033)
_AUTO_FILTER_COLUMNS = {"created_at", "updated_at", "created_by", "updated_by", "active"}


# ─── Response helper ──────────────────────────────────────────────────────────

def _success(
    data: Any = None,
    message: str | None = None,
    *,
    status_code: int = 200,
) -> dict[str, Any]:
    return {"success": True, "data": data, "message": message}


def _error(message: str, errors: list | None = None) -> dict[str, Any]:
    return {"success": False, "data": None, "message": message, "errors": errors or []}


# ─── T035: FK Validation ──────────────────────────────────────────────────────

async def _validate_fk_fields(
    db: AsyncSession,
    data: dict[str, Any],
    module_fields: dict[str, BaseField] | None,
) -> None:
    """Validate ForeignKey fields exist in their target tables (T035).

    Raises HTTPException 422 if any FK value doesn't exist in DB.
    """
    if not module_fields:
        return

    from sqlalchemy import text

    for field_name, field_def in module_fields.items():
        if not isinstance(field_def, ForeignKeyField):
            continue
        value = data.get(field_name)
        if value is None:
            continue  # NULL FK is allowed (checked by required flag in Pydantic)

        target_table = field_def.to  # e.g. "categories"
        # Check existence in target table
        result = await db.execute(
            text(f"SELECT id FROM {target_table} WHERE id = :id LIMIT 1"),
            {"id": value},
        )
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"ForeignKey '{field_name}' = {value} không tồn tại trong '{target_table}'",
            )


# ─── T038: SelectionField Validation ─────────────────────────────────────────

def _validate_selection_fields(
    data: dict[str, Any],
    module_fields: dict[str, BaseField] | None,
) -> None:
    """Validate SelectionField values are within allowed options (T038).

    Raises HTTPException 422 if value not in options.
    """
    if not module_fields:
        return

    for field_name, field_def in module_fields.items():
        if not isinstance(field_def, SelectionField):
            continue
        value = data.get(field_name)
        if value is None:
            continue
        if field_def.options and value not in field_def.options:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Giá trị '{value}' không hợp lệ cho '{field_name}'. "
                       f"Cho phép: {field_def.options}",
            )


# ─── T041: Eager FK Load ──────────────────────────────────────────────────────

async def _eager_load_fk(
    db: AsyncSession,
    row_dict: dict[str, Any],
    module_fields: dict[str, BaseField] | None,
) -> dict[str, Any]:
    """Eager-load FK related records and attach as nested objects (T041).

    For each ForeignKeyField, attempts to load {field_name without _id} object.
    E.g. category_id=2 → category: {id: 2, name: "Coffee"}
    """
    if not module_fields:
        return row_dict

    from sqlalchemy import text

    for field_name, field_def in module_fields.items():
        if not isinstance(field_def, ForeignKeyField):
            continue
        fk_value = row_dict.get(field_name)
        if fk_value is None:
            continue

        target_table = field_def.to
        display_field = field_def.display_field  # default "name"

        # Derive the nested key: "category_id" → "category"
        nested_key = field_name[:-3] if field_name.endswith("_id") else field_name + "_obj"

        try:
            result = await db.execute(
                text(f"SELECT id, {display_field} FROM {target_table} WHERE id = :id LIMIT 1"),
                {"id": fk_value},
            )
            related_row = result.mappings().first()
            if related_row:
                row_dict[nested_key] = dict(related_row)
            else:
                row_dict[nested_key] = None
        except Exception:
            # If display_field doesn't exist or table missing, skip silently
            pass

    return row_dict


# ─── T046-T047: Computed Fields ───────────────────────────────────────────────

def _apply_computed_fields(
    row_dict: dict[str, Any],
    computed_fields: dict[str, ComputedField] | None,
    record: Any,
) -> dict[str, Any]:
    """Apply non-stored computed fields to a row dict (T046).

    Calls each ComputedField.fn(record) and adds result to row_dict.
    """
    if not computed_fields:
        return row_dict

    for field_name, cf in computed_fields.items():
        if cf.store:
            continue  # stored computed → already in DB, already in row_dict
        if cf.fn is None:
            continue
        try:
            value = cf.fn(record)
            # Serialize if needed
            from datetime import date, datetime
            from decimal import Decimal
            if isinstance(value, datetime):
                value = value.isoformat()
            elif isinstance(value, date):
                value = value.isoformat()
            elif isinstance(value, Decimal):
                value = float(value)
            row_dict[field_name] = value
        except Exception:
            row_dict[field_name] = None

    return row_dict


async def _recompute_stored_fields(
    data: dict[str, Any],
    computed_fields: dict[str, ComputedField] | None,
    record: Any,
) -> dict[str, Any]:
    """Recompute stored computed fields when their dependencies change (T047).

    Adds recomputed values to `data` so they get saved to DB.
    """
    if not computed_fields:
        return data

    for field_name, cf in computed_fields.items():
        if not cf.store or cf.fn is None:
            continue
        # Check if any dependency changed
        if cf.depends and not any(dep in data for dep in cf.depends):
            continue  # No dependency changed, skip recompute
        try:
            value = cf.fn(record)
            data[field_name] = value
        except Exception:
            pass

    return data


# ─── LIST ─────────────────────────────────────────────────────────────────────

async def handle_list(
    db: AsyncSession,
    model: type,
    *,
    search: str | None = None,
    search_fields: list[str] | None = None,
    filter_fields: list[str] | None = None,
    module_fields: dict[str, BaseField] | None = None,
    computed_fields: dict[str, ComputedField] | None = None,
    query_params: dict[str, str] | None = None,
    sort_by: str | None = None,
    sort_desc: bool = False,
    skip: int = 0,
    limit: int = 20,
    max_page_size: int = 100,
    archive: bool = True,
    with_archived: bool = False,
    user_id: int | None = None,
) -> dict[str, Any]:
    """Generic list handler with search, filter, sort, pagination."""
    # Cap limit
    limit = min(limit, max_page_size)

    query = select(model)

    # Archive filter
    if archive and hasattr(model, "active"):
        if not with_archived or user_id is None:
            query = query.where(model.active == True)  # noqa: E712

    # Search (ILIKE OR across search_fields)
    if search and search_fields:
        conditions = []
        for field_name in search_fields:
            col = getattr(model, field_name, None)
            if col is not None:
                conditions.append(col.ilike(f"%{search}%"))
        if conditions:
            query = query.where(or_(*conditions))

    # Filters — user-defined filter_fields + auto system columns (T033)
    all_filterable = set(filter_fields or []) | _AUTO_FILTER_COLUMNS
    if all_filterable and query_params:
        for field_name in all_filterable:
            raw_value = query_params.get(field_name)
            if raw_value is None:
                continue
            col = getattr(model, field_name, None)
            if col is None:
                continue
            operator, value = parse_filter_value(raw_value)
            try:
                query = query.where(apply_filter(col, operator, value))
            except ValueError:
                pass  # Skip invalid filter values silently

    # Total count (before pagination)
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    # Sort
    if sort_by:
        col = getattr(model, sort_by, None)
        if col is not None:
            query = query.order_by(col.desc() if sort_desc else col.asc())

    # Pagination
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    items = result.scalars().all()

    # Build response with FK eager load + computed fields
    item_dicts = []
    for item in items:
        row = _row_to_dict(item)
        row = await _eager_load_fk(db, row, module_fields)  # T041
        row = _apply_computed_fields(row, computed_fields, item)  # T046
        item_dicts.append(row)

    return _success(data={
        "total": total,
        "items": item_dicts,
        "skip": skip,
        "limit": limit,
    })


# ─── GET ──────────────────────────────────────────────────────────────────────

async def handle_get(
    db: AsyncSession,
    model: type,
    record_id: int,
    *,
    archive: bool = True,
    module_fields: dict[str, BaseField] | None = None,
    computed_fields: dict[str, ComputedField] | None = None,
) -> dict[str, Any]:
    """Get a single record by ID with FK eager load + computed fields."""
    query = select(model).where(model.id == record_id)

    # Don't return archived records by default
    if archive and hasattr(model, "active"):
        query = query.where(model.active == True)  # noqa: E712

    result = await db.execute(query)
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Record không tồn tại",
        )

    row = _row_to_dict(record)
    row = await _eager_load_fk(db, row, module_fields)  # T041
    row = _apply_computed_fields(row, computed_fields, record)  # T046

    return _success(data=row)


# ─── CREATE ───────────────────────────────────────────────────────────────────

async def handle_create(
    db: AsyncSession,
    model: type,
    data: dict[str, Any],
    *,
    user_id: int | None = None,
    module_fields: dict[str, BaseField] | None = None,
    computed_fields: dict[str, ComputedField] | None = None,
) -> dict[str, Any]:
    """Create a new record with FK validation + SelectionField validation."""
    # Inject audit fields
    if user_id is not None:
        data["created_by"] = user_id
        data["updated_by"] = user_id

    # T038: Validate SelectionField options
    _validate_selection_fields(data, module_fields)

    # T035: Validate FK existence
    await _validate_fk_fields(db, data, module_fields)

    # Remove M2M and OneToMany fields (handled separately)
    m2m_data = {}
    o2m_data: dict[str, list[dict[str, Any]]] = {}
    m2m_tables = getattr(model, "_m2m_tables", {})
    
    for field_name, field_def in (module_fields or {}).items():
        if isinstance(field_def, ManyToManyField):
            if field_name in data:
                m2m_data[field_name] = data.pop(field_name)
        elif isinstance(field_def, OneToManyField):
            if field_name in data:
                o2m_data[field_name] = data.pop(field_name)

    # T047: Compute stored fields for new record (mock record with data attrs)
    if computed_fields:
        class _MockRecord:
            def __init__(self, d): self.__dict__.update(d)
        mock = _MockRecord(data)
        for field_name, cf in computed_fields.items():
            if cf.store and cf.fn is not None:
                try:
                    data[field_name] = cf.fn(mock)
                except Exception:
                    pass

    record = model(**data)
    db.add(record)
    await db.flush()

    # Handle M2M inserts
    for m2m_field, ids in m2m_data.items():
        if ids and m2m_field in m2m_tables:
            junction = m2m_tables[m2m_field]
            source_col = list(junction.c)[0]
            target_col = list(junction.c)[1]
            for target_id in ids:
                await db.execute(
                    junction.insert().values(
                        **{source_col.name: record.id, target_col.name: target_id}
                    )
                )

    await db.commit()
    await db.refresh(record)

    row = _row_to_dict(record)
    row = _apply_computed_fields(row, computed_fields, record)  # T046

    return _success(data=row, message="Tạo thành công")


# ─── UPDATE ───────────────────────────────────────────────────────────────────

async def handle_update(
    db: AsyncSession,
    model: type,
    record_id: int,
    data: dict[str, Any],
    *,
    user_id: int | None = None,
    optimistic_lock: bool = False,
    module_fields: dict[str, BaseField] | None = None,
    computed_fields: dict[str, ComputedField] | None = None,
) -> dict[str, Any]:
    """Update an existing record with FK + SelectionField validation."""
    result = await db.execute(select(model).where(model.id == record_id))
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Record không tồn tại",
        )

    # Optimistic lock check
    if optimistic_lock and hasattr(record, "version"):
        client_version = data.pop("version", None)
        if client_version is not None and record.version != client_version:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Conflict — record đã được sửa bởi người khác",
            )
        record.version += 1

    # T038: Validate SelectionField options
    _validate_selection_fields(data, module_fields)

    # T035: Validate FK existence
    await _validate_fk_fields(db, data, module_fields)

    # Inject audit
    if user_id is not None:
        data["updated_by"] = user_id

    # Remove M2M and OneToMany fields
    m2m_data = {}
    o2m_data: dict[str, list[dict[str, Any]]] = {}
    m2m_tables = getattr(model, "_m2m_tables", {})
    
    for field_name, field_def in (module_fields or {}).items():
        if isinstance(field_def, ManyToManyField):
            if field_name in data:
                m2m_data[field_name] = data.pop(field_name)
        elif isinstance(field_def, OneToManyField):
            if field_name in data:
                o2m_data[field_name] = data.pop(field_name)

    # T047: Recompute stored fields if dependencies changed
    data = await _recompute_stored_fields(data, computed_fields, record)

    # Apply updates (skip None values for partial update)
    for key, value in data.items():
        if value is not None and hasattr(record, key):
            setattr(record, key, value)

    # Handle M2M updates (replace all)
    for m2m_field, ids in m2m_data.items():
        if ids is not None and m2m_field in m2m_tables:
            junction = m2m_tables[m2m_field]
            source_col = list(junction.c)[0]
            target_col = list(junction.c)[1]
            # Delete existing
            await db.execute(
                junction.delete().where(source_col == record.id)
            )
            # Insert new
            for target_id in ids:
                await db.execute(
                    junction.insert().values(
                        **{source_col.name: record.id, target_col.name: target_id}
                    )
                )

    await db.commit()
    await db.refresh(record)

    row = _row_to_dict(record)
    row = _apply_computed_fields(row, computed_fields, record)  # T046

    return _success(data=row, message="Cập nhật thành công")


# ─── ARCHIVE ──────────────────────────────────────────────────────────────────

async def handle_archive(
    db: AsyncSession,
    model: type,
    record_id: int,
) -> dict[str, Any]:
    """Archive a record (set active=False)."""
    result = await db.execute(select(model).where(model.id == record_id))
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Record không tồn tại",
        )

    record.active = False
    await db.commit()

    return _success(message="Đã lưu trữ")


# ─── RESTORE ──────────────────────────────────────────────────────────────────

async def handle_restore(
    db: AsyncSession,
    model: type,
    record_id: int,
) -> dict[str, Any]:
    """Restore an archived record (set active=True)."""
    result = await db.execute(
        select(model).where(model.id == record_id)
    )
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Record không tồn tại",
        )

    record.active = True
    await db.commit()

    return _success(message="Đã khôi phục")


# ─── DELETE ───────────────────────────────────────────────────────────────────

async def handle_delete(
    db: AsyncSession,
    model: type,
    record_id: int,
) -> dict[str, Any]:
    """Permanently delete a record."""
    result = await db.execute(select(model).where(model.id == record_id))
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Record không tồn tại",
        )

    await db.delete(record)
    await db.commit()

    return _success(message="Đã xóa vĩnh viễn")


# ─── BULK (T050: upsert support) ──────────────────────────────────────────────

async def handle_bulk(
    db: AsyncSession,
    model: type,
    items: list[dict[str, Any]],
    *,
    user_id: int | None = None,
    bulk_fields: list[str] | None = None,
    upsert: bool = False,
    module_fields: dict[str, BaseField] | None = None,
) -> dict[str, Any]:
    """Bulk create/upsert records with atomic transaction (T050).

    If upsert=True and item has 'id' that exists → UPDATE, else → CREATE.
    Validates SelectionField + FK for each row.
    """
    created = 0
    updated = 0
    errors: list[dict[str, Any]] = []

    try:
        for idx, item_data in enumerate(items):
            # Filter to allowed fields
            if bulk_fields:
                item_data = {k: v for k, v in item_data.items() if k in bulk_fields or k == "id"}

            # Inject audit
            if user_id is not None:
                item_data["created_by"] = user_id
                item_data["updated_by"] = user_id

            # T038 + T035 validation per row
            try:
                _validate_selection_fields(item_data, module_fields)
                await _validate_fk_fields(db, item_data, module_fields)
            except HTTPException as e:
                errors.append({"row": idx + 1, "detail": str(e.detail)})
                continue

            # T050: Upsert logic
            existing_id = item_data.get("id")
            if upsert and existing_id:
                result = await db.execute(select(model).where(model.id == existing_id))
                existing = result.scalar_one_or_none()
                if existing:
                    for key, value in item_data.items():
                        if key != "id" and hasattr(existing, key):
                            setattr(existing, key, value)
                    updated += 1
                    continue

            # Strip id for new records
            item_data.pop("id", None)
            record = model(**item_data)
            db.add(record)
            created += 1

        await db.flush()
        await db.commit()

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Import thất bại — đã rollback: {str(e)}",
        )

    return _success(
        data={"created": created, "updated": updated, "errors": errors},
        message=f"Import thành công: {created} tạo mới, {updated} cập nhật"
        + (f", {len(errors)} lỗi" if errors else ""),
    )


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _row_to_dict(record: Any) -> dict[str, Any]:
    """Convert a SQLAlchemy model instance to a JSON-safe dict."""
    from datetime import date, datetime
    from decimal import Decimal

    result = {}
    for col in record.__table__.columns:
        value = getattr(record, col.name, None)
        # Serialize non-JSON-native types
        if isinstance(value, datetime):
            value = value.isoformat()
        elif isinstance(value, date):
            value = value.isoformat()
        elif isinstance(value, Decimal):
            value = float(value)
        result[col.name] = value
    return result

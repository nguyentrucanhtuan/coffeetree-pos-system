# Research: TRCFBaseModule CRUD Framework

**Date**: 2026-03-26  
**Feature**: 002-trcf-base-module

## No NEEDS CLARIFICATION Items

All unknowns were resolved during the `/speckit.clarify` session:

| Topic | Decision | Rationale | Alternatives Considered |
|---|---|---|---|
| DB Migration | Alembic auto-generate | Convention over configuration; dev runs `alembic revision --autogenerate` | Drop+recreate (loses data), manual migrations (error-prone) |
| Bulk Import Transaction | Rollback all on failure | Data integrity for ERP/POS — no partial imports | Commit partial (risky for accounting data) |
| File/Image Storage | Local filesystem (`uploads/`) | Simplest for Phase 0; easily swappable later | MinIO/S3 (over-engineering for MVP), storage abstraction (premature) |

## Tech Research

### Metaclass vs `__init_subclass__` for Auto-Generation

**Decision**: Use `__init_subclass__` (Python 3.6+)  
**Rationale**: Simpler than metaclass, no metaclass conflict with SQLAlchemy's `DeclarativeMeta`. `__init_subclass__` is called when a class is subclassed, giving us a hook to process field definitions.  
**Alternative rejected**: Full metaclass — conflicts with SQLAlchemy's own metaclass; requires careful MRO handling.

### SQLAlchemy Dynamic Model Generation

**Decision**: Use `type()` to dynamically create model classes with `__tablename__`, `__table_args__`, and column attributes.  
**Rationale**: SQLAlchemy supports dynamic model creation via `type(name, (Base,), attrs)`. This lets us convert field definitions to Column objects at class definition time.

### Pydantic Dynamic Schema Generation

**Decision**: Use `pydantic.create_model()` to generate Create/Update/Response schemas.  
**Rationale**: Pydantic v2 `create_model()` accepts field definitions as kwargs — perfect for auto-generation from our field types.

### Filter Prefix Parsing

**Decision**: Regex-based parser in `filters.py`  
**Rationale**: Simple regex `r'^\[(>=?|<=?|!|!=|\*|!\*|~|-)\](.+)$'` to extract operator and value. Map to SQLAlchemy column operators.

"""TRCFBaseModule — the core base class for all business modules.

Usage:
    from base.module import TRCFBaseModule
    from base import fields

    class Category(TRCFBaseModule):
        _name = "categories"
        _description = "Danh mục sản phẩm"
        _search_fields = ["name"]

        name = fields.CharField(label="Tên danh mục", required=True)
        icon = fields.CharField(label="Icon", max_length=10)

    # In main.py:
    app.include_router(Category.router())
"""

from __future__ import annotations

from typing import Any, ClassVar

from base.fields import BaseField, ComputedField
from base.model_factory import create_sa_model
from base.router_factory import create_router
from base.schema_factory import create_schemas


class TRCFBaseModule:
    """Base class for all business modules.

    Subclass this and declare fields + class attributes.
    Call .router() to get a FastAPI APIRouter with 9 CRUD endpoints.
    """

    # ── Class Attributes (Configuration) ─────────────────────────────────

    _name: ClassVar[str] = ""
    _description: ClassVar[str] = ""
    _search_fields: ClassVar[list[str]] = []
    _filter_fields: ClassVar[list[str]] = []
    _sort_by: ClassVar[str | None] = None
    _sort_desc: ClassVar[bool] = False
    _archive: ClassVar[bool] = True
    _readonly_fields: ClassVar[list[str]] = []
    _bulk_fields: ClassVar[list[str]] = []
    _max_page_size: ClassVar[int] = 100
    _optimistic_lock: ClassVar[bool] = False
    _require_auth: ClassVar[bool] = True
    _public_actions: ClassVar[list[str]] = []
    _seed_data: ClassVar[str] = ""  # Path to JSON file
    _list_columns: ClassVar[list[str] | None] = None  # None = auto (all non-system fields)

    # Menu attributes
    _menu_label: ClassVar[str] = ""
    _menu_icon: ClassVar[str] = ""
    _menu_parent: ClassVar[str] = ""
    _menu_sequence: ClassVar[int] = 100
    _menu_hidden: ClassVar[bool] = False

    # Settings
    _settings: ClassVar[list[dict[str, Any]]] = []

    # ── Internal (populated by __init_subclass__) ────────────────────────

    _fields: ClassVar[dict[str, BaseField]] = {}
    _computed_fields: ClassVar[dict[str, ComputedField]] = {}
    _sa_model: ClassVar[type] = type(None)
    _create_schema: ClassVar[type] = type(None)
    _update_schema: ClassVar[type] = type(None)
    _response_schema: ClassVar[type] = type(None)
    _module_name: ClassVar[str] = ""

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Called when a class inherits TRCFBaseModule.

        Processes field definitions and generates:
        - SQLAlchemy model
        - Pydantic schemas (Create, Update, Response)
        """
        super().__init_subclass__(**kwargs)

        # Skip if this is an intermediate mixin (no _name)
        module_name = getattr(cls, "_name", "") or cls.__name__.lower() + "s"
        cls._module_name = module_name

        # Collect field definitions from class attributes
        user_fields: dict[str, BaseField] = {}
        computed_fields: dict[str, ComputedField] = {}

        for attr_name in list(vars(cls)):
            attr = getattr(cls, attr_name)
            if isinstance(attr, BaseField):
                attr._name = attr_name
                user_fields[attr_name] = attr
            elif isinstance(attr, ComputedField):
                attr._name = attr_name
                computed_fields[attr_name] = attr

        cls._fields = user_fields
        cls._computed_fields = computed_fields

        if not user_fields:
            return  # No fields = abstract base, skip model generation

        # Generate SQLAlchemy model
        cls._sa_model = create_sa_model(
            module_name,
            user_fields,
            archive=cls._archive,
            optimistic_lock=cls._optimistic_lock,
        )

        # Generate Pydantic schemas
        cls._create_schema, cls._update_schema, cls._response_schema = (
            create_schemas(
                module_name,
                user_fields,
                readonly_fields=cls._readonly_fields,
            )
        )

    @classmethod
    def router(cls) -> Any:
        """Generate FastAPI APIRouter with all CRUD endpoints."""
        return create_router(cls)

    @classmethod
    def _meta_schema(cls) -> dict[str, Any]:
        """Return schema metadata for /meta/schema endpoint."""
        field_meta = [f.schema_meta() for f in cls._fields.values()]
        computed_meta = [c.schema_meta() for c in cls._computed_fields.values()]

        return {
            "module": cls._module_name,
            "description": cls._description or cls._module_name,
            "fields": field_meta,
            "computed_fields": computed_meta,
            "search_fields": cls._search_fields,
            "filter_fields": cls._filter_fields,
            "sort_by": cls._sort_by,
            "sort_desc": cls._sort_desc,
            "archive": cls._archive,
            "has_settings": bool(cls._settings),
            "list_columns": cls._list_columns,  # None = auto, list = explicit set
        }

    @classmethod
    def menu_item(cls) -> dict[str, Any] | None:
        """Return menu metadata for /modules/menu endpoint."""
        if cls._menu_hidden:
            return None
        return {
            "name": cls._module_name,
            "menu_label": cls._menu_label or cls._description or cls._module_name,
            "menu_icon": cls._menu_icon,
            "menu_parent": cls._menu_parent,
            "menu_sequence": cls._menu_sequence,
            "has_settings": bool(cls._settings),
        }

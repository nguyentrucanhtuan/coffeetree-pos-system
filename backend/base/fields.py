"""Field type definitions for TRCFBaseModule.

Each field class maps to:
  - SQLAlchemy column type
  - Pydantic field type
  - Frontend schema metadata
"""

from __future__ import annotations

from dataclasses import dataclass, field as dc_field
from datetime import date, datetime
from decimal import Decimal
from typing import Any


@dataclass
class BaseField:
    """Base class for all field types."""

    label: str = ""
    required: bool = False
    default: Any = None
    readonly: bool = False
    unique: bool = False
    index: bool = False
    ui_type: str | None = None  # Override frontend widget (e.g. "textarea", "email")
    help_text: str = ""
    domain: dict[str, Any] | None = None  # Filter for relational fields (e.g. {"type": "service"})

    # Populated automatically by __init_subclass__ processor
    _name: str = ""

    @property
    def schema_type(self) -> str:
        """Return the type string for /meta/schema response."""
        raise NotImplementedError

    def sa_column_kwargs(self) -> dict[str, Any]:
        """Return kwargs for sqlalchemy.Column(...)."""
        return {
            "nullable": not self.required,
            "unique": self.unique,
            "index": self.index,
            "default": self.default,
        }

    def schema_meta(self) -> dict[str, Any]:
        """Return field metadata for /meta/schema response."""
        meta: dict[str, Any] = {
            "name": self._name,
            "type": self.schema_type,
            "label": self.label or self._name,
            "required": self.required,
        }
        if self.readonly:
            meta["readonly"] = True
        if self.default is not None:
            meta["default"] = self.default
        if self.ui_type:
            meta["ui_type"] = self.ui_type
        if self.help_text:
            meta["help_text"] = self.help_text
        if self.domain:
            meta["domain"] = self.domain
        return meta

    @property
    def python_type(self) -> type:
        """Return the Python type for Pydantic schema generation."""
        raise NotImplementedError

    @property
    def sa_type(self) -> Any:
        """Return SQLAlchemy column type class (not instance)."""
        raise NotImplementedError


# ─── String Fields ────────────────────────────────────────────────────────────


@dataclass
class CharField(BaseField):
    max_length: int = 255

    @property
    def schema_type(self) -> str:
        return "string"

    @property
    def python_type(self) -> type:
        return str

    @property
    def sa_type(self) -> Any:
        from sqlalchemy import String
        return String(self.max_length)

    def schema_meta(self) -> dict[str, Any]:
        meta = super().schema_meta()
        meta["max_length"] = self.max_length
        return meta


@dataclass
class TextField(BaseField):
    @property
    def schema_type(self) -> str:
        return "string"

    @property
    def python_type(self) -> type:
        return str

    @property
    def sa_type(self) -> Any:
        from sqlalchemy import Text
        return Text()

    def __post_init__(self) -> None:
        if not self.ui_type:
            self.ui_type = "textarea"


# ─── Numeric Fields ──────────────────────────────────────────────────────────


@dataclass
class IntField(BaseField):
    min_value: int | None = None
    max_value: int | None = None

    @property
    def schema_type(self) -> str:
        return "integer"

    @property
    def python_type(self) -> type:
        return int

    @property
    def sa_type(self) -> Any:
        from sqlalchemy import Integer
        return Integer()

    def schema_meta(self) -> dict[str, Any]:
        meta = super().schema_meta()
        if self.min_value is not None:
            meta["min_value"] = self.min_value
        if self.max_value is not None:
            meta["max_value"] = self.max_value
        return meta


@dataclass
class FloatField(BaseField):
    @property
    def schema_type(self) -> str:
        return "float"

    @property
    def python_type(self) -> type:
        return float

    @property
    def sa_type(self) -> Any:
        from sqlalchemy import Float
        return Float()


@dataclass
class DecimalField(BaseField):
    precision: int = 12
    scale: int = 2

    @property
    def schema_type(self) -> str:
        return "decimal"

    @property
    def python_type(self) -> type:
        return Decimal

    @property
    def sa_type(self) -> Any:
        from sqlalchemy import Numeric
        return Numeric(precision=self.precision, scale=self.scale)

    def schema_meta(self) -> dict[str, Any]:
        meta = super().schema_meta()
        meta["precision"] = self.precision
        meta["scale"] = self.scale
        return meta


# ─── Boolean Field ───────────────────────────────────────────────────────────


@dataclass
class BooleanField(BaseField):
    default: Any = False  # type: ignore[assignment]

    @property
    def schema_type(self) -> str:
        return "boolean"

    @property
    def python_type(self) -> type:
        return bool

    @property
    def sa_type(self) -> Any:
        from sqlalchemy import Boolean
        return Boolean()


# ─── DateTime Fields ─────────────────────────────────────────────────────────


@dataclass
class DateTimeField(BaseField):
    @property
    def schema_type(self) -> str:
        return "datetime"

    @property
    def python_type(self) -> type:
        return datetime

    @property
    def sa_type(self) -> Any:
        from sqlalchemy import DateTime
        return DateTime()


@dataclass
class DateField(BaseField):
    @property
    def schema_type(self) -> str:
        return "date"

    @property
    def python_type(self) -> type:
        return date

    @property
    def sa_type(self) -> Any:
        from sqlalchemy import Date
        return Date()


# ─── JSON Field ──────────────────────────────────────────────────────────────


@dataclass
class JSONField(BaseField):
    @property
    def schema_type(self) -> str:
        return "json"

    @property
    def python_type(self) -> type:
        return dict  # type: ignore[return-value]

    @property
    def sa_type(self) -> Any:
        from sqlalchemy import JSON
        return JSON()


# ─── Relational Fields ───────────────────────────────────────────────────────


@dataclass
class ForeignKeyField(BaseField):
    to: str = ""  # Target module _name (e.g. "categories")
    display_field: str = "name"  # Field to display in frontend dropdown
    on_delete: str = "SET NULL"  # CASCADE, SET NULL, RESTRICT
    depends_on: str | None = None  # Field name it depends on for filtering

    @property
    def schema_type(self) -> str:
        return "foreignkey"

    @property
    def python_type(self) -> type:
        return int

    @property
    def sa_type(self) -> Any:
        from sqlalchemy import Integer
        return Integer()

    def schema_meta(self) -> dict[str, Any]:
        meta = super().schema_meta()
        meta["to"] = self.to
        meta["display_field"] = self.display_field
        if self.depends_on:
            meta["depends_on"] = self.depends_on
        return meta


@dataclass
class ManyToManyField(BaseField):
    to: str = ""  # Target module _name
    display_field: str = "name"  # Field to display in frontend dropdown

    @property
    def schema_type(self) -> str:
        return "m2m"

    @property
    def python_type(self) -> type:
        return list  # type: ignore[return-value]

    @property
    def sa_type(self) -> Any:
        # M2M doesn't create a column — it creates a junction table
        return None

    def schema_meta(self) -> dict[str, Any]:
        meta = super().schema_meta()
        meta["to"] = self.to
        meta["display_field"] = self.display_field
        return meta


@dataclass
class OneToManyField(BaseField):
    to: str = ""  # Target module _name (e.g. "bom_lines")
    related_field: str = ""  # Field in child pointing back (e.g. "bom_id")

    @property
    def schema_type(self) -> str:
        return "one2many"

    @property
    def python_type(self) -> type:
        return list  # List of child objects

    @property
    def sa_type(self) -> Any:
        return None  # Not a direct column on the parent table

    def schema_meta(self) -> dict[str, Any]:
        meta = super().schema_meta()
        meta["to"] = self.to
        meta["related_field"] = self.related_field
        return meta


# ─── Selection Field ─────────────────────────────────────────────────────────


@dataclass
class SelectionField(BaseField):
    options: list[str] = dc_field(default_factory=list)
    max_length: int = 100

    @property
    def schema_type(self) -> str:
        return "selection"

    @property
    def python_type(self) -> type:
        return str

    @property
    def sa_type(self) -> Any:
        from sqlalchemy import String
        return String(self.max_length)

    def schema_meta(self) -> dict[str, Any]:
        meta = super().schema_meta()
        meta["options"] = self.options
        return meta


# ─── File/Image Fields ───────────────────────────────────────────────────────


@dataclass
class FileField(BaseField):
    max_size_mb: int = 5
    allowed_types: list[str] = dc_field(default_factory=list)

    @property
    def schema_type(self) -> str:
        return "file"

    @property
    def python_type(self) -> type:
        return str  # Stores file path

    @property
    def sa_type(self) -> Any:
        from sqlalchemy import String
        return String(500)


@dataclass
class ImageField(BaseField):
    max_size_mb: int = 5
    allowed_types: list[str] = dc_field(
        default_factory=lambda: ["image/jpeg", "image/png", "image/webp"]
    )

    @property
    def schema_type(self) -> str:
        return "image"

    @property
    def python_type(self) -> type:
        return str  # Stores image path

    @property
    def sa_type(self) -> Any:
        from sqlalchemy import String
        return String(500)


# ─── Computed Field ──────────────────────────────────────────────────────────


@dataclass
class ComputedField:
    """Non-stored or stored computed field.

    Usage:
        total = ComputedField(fn=lambda r: r.qty * r.price, depends=["qty", "price"])
        total_stored = ComputedField(fn=..., depends=..., store=True)
    """

    fn: Any = None  # Callable[[record], value]
    depends: list[str] = dc_field(default_factory=list)
    store: bool = False
    label: str = ""
    _name: str = ""

    @property
    def schema_type(self) -> str:
        return "computed"

    def schema_meta(self) -> dict[str, Any]:
        return {
            "name": self._name,
            "type": "computed",
            "label": self.label or self._name,
            "depends": self.depends,
            "store": self.store,
            "readonly": True,
        }


# ─── All field types ─────────────────────────────────────────────────────────

FIELD_TYPES: dict[str, type[BaseField]] = {
    "CharField": CharField,
    "TextField": TextField,
    "IntField": IntField,
    "FloatField": FloatField,
    "DecimalField": DecimalField,
    "BooleanField": BooleanField,
    "DateTimeField": DateTimeField,
    "DateField": DateField,
    "JSONField": JSONField,
    "ForeignKeyField": ForeignKeyField,
    "ManyToManyField": ManyToManyField,
    "OneToManyField": OneToManyField,
    "SelectionField": SelectionField,
    "FileField": FileField,
    "ImageField": ImageField,
}

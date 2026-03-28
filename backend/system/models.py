"""SystemSetting model — stores per-module configurable settings."""

from __future__ import annotations

from sqlalchemy import Boolean, Column, Integer, String, Text

from app.database import Base


class SystemSetting(Base):
    """Stores module settings seeded from _settings class attribute.

    Each row represents one setting key for one module.
    """

    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    module_name = Column(String(100), nullable=False, index=True)
    key = Column(String(100), nullable=False)
    label = Column(String(200), nullable=True)
    value = Column(Text, nullable=True)
    value_type = Column(String(20), default="string")  # string, integer, boolean, json
    is_public = Column(Boolean, default=False)  # Accessible without auth

    __table_args__ = (
        # Unique constraint on (module_name, key)
        {"extend_existing": True},
    )

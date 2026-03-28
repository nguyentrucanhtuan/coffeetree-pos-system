"""File/Image upload handler for TRCFBaseModule (T065).

Handles file validation (type, size) and saves to uploads/{module_name}/{field_name}/.
Updates the record's field_name column with the saved path.
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Any

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Base upload directory — configurable via env var
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "uploads"))


async def handle_upload(
    *,
    db: AsyncSession,
    model: type,
    record_id: int,
    field_name: str,
    file: UploadFile,
    module_name: str,
    allowed_types: list[str] | None = None,
    max_size_mb: int = 5,
) -> dict[str, Any]:
    """Save an uploaded file and update the record's field with the file path.

    Args:
        db: Async SQLAlchemy session.
        model: SQLAlchemy model class.
        record_id: Primary key of the record to update.
        field_name: Column name to save the file path into.
        file: FastAPI UploadFile object.
        module_name: Module name for directory organization.
        allowed_types: List of accepted MIME types (e.g. ["image/jpeg", "image/png"]).
                       If empty, all types are accepted.
        max_size_mb: Maximum allowed file size in megabytes.

    Returns:
        Standard success dict with file_url in data.
    """
    # ── Validate record exists ─────────────────────────────────────────────
    result = await db.execute(select(model).where(model.id == record_id))
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Record {record_id} không tồn tại",
        )

    # ── Validate MIME type ─────────────────────────────────────────────────
    if allowed_types and file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Loại file '{file.content_type}' không được phép. "
                   f"Chỉ chấp nhận: {allowed_types}",
        )

    # ── Read file content (stream) ─────────────────────────────────────────
    contents = await file.read()

    # ── Validate file size ─────────────────────────────────────────────────
    max_bytes = max_size_mb * 1024 * 1024
    if len(contents) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"File vượt quá kích thước tối đa {max_size_mb}MB "
                   f"(hiện tại: {len(contents) / 1024 / 1024:.1f}MB)",
        )

    # ── Generate unique filename ───────────────────────────────────────────
    original_name = file.filename or "upload"
    ext = Path(original_name).suffix.lower()  # e.g. ".jpg"
    unique_name = f"{uuid.uuid4().hex}{ext}"

    # ── Save file ─────────────────────────────────────────────────────────
    save_dir = UPLOAD_DIR / module_name / field_name
    save_dir.mkdir(parents=True, exist_ok=True)
    save_path = save_dir / unique_name

    with open(save_path, "wb") as f:
        f.write(contents)

    # ── Build relative URL (for serving) ──────────────────────────────────
    file_url = f"/uploads/{module_name}/{field_name}/{unique_name}"

    # ── Update record ──────────────────────────────────────────────────────
    setattr(record, field_name, file_url)
    await db.commit()

    return {
        "success": True,
        "data": {
            "file_url": file_url,
            "original_name": original_name,
            "size_bytes": len(contents),
            "content_type": file.content_type,
        },
        "message": "Upload thành công",
    }

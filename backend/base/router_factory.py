"""Router factory — auto-generate FastAPI APIRouter from TRCFBaseModule."""


from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Request

from app.database import DBSession
from base import handlers
from base.permissions import check_permission


def create_router(module_cls: Any) -> APIRouter:
    """Generate a FastAPI APIRouter with 9 CRUD endpoints for a TRCFBaseModule.

    Endpoints:
        GET  /{name}/           — List (search, filter, sort, pagination)
        GET  /{name}/{id}       — Get single record
        POST /{name}/           — Create
        PUT  /{name}/{id}       — Update
        POST /{name}/{id}/archive — Archive (if _archive=True)
        POST /{name}/{id}/restore — Restore (if _archive=True)
        DELETE /{name}/{id}     — Permanent delete
        POST /{name}/bulk       — Bulk import
        GET  /{name}/meta/schema — Field metadata for frontend
    """
    name = module_cls._module_name
    model = module_cls._sa_model
    description = module_cls._description
    archive = module_cls._archive
    search_fields = module_cls._search_fields
    filter_fields = module_cls._filter_fields
    sort_by = module_cls._sort_by
    sort_desc = module_cls._sort_desc
    max_page_size = module_cls._max_page_size
    require_auth = module_cls._require_auth
    public_actions = module_cls._public_actions
    readonly_fields = module_cls._readonly_fields
    bulk_fields = module_cls._bulk_fields
    optimistic_lock = module_cls._optimistic_lock
    create_schema = module_cls._create_schema
    update_schema = module_cls._update_schema
    module_fields = module_cls._fields          # for FK/Selection validation + eager load
    computed_fields = module_cls._computed_fields  # for computed field integration

    router = APIRouter(prefix=f"/{name}", tags=[description or name])

    # ── LIST ──────────────────────────────────────────────────────────────

    @router.get("/")
    async def list_records(
        request: Request,
        db: DBSession,
        search: Annotated[str | None, Query()] = None,
        sort_by_param: Annotated[str | None, Query(alias="sort_by")] = None,
        sort_desc_param: Annotated[bool, Query(alias="sort_desc")] = False,
        skip: Annotated[int, Query(ge=0)] = 0,
        limit: Annotated[int, Query(ge=1, le=500)] = 20,
        with_archived: Annotated[bool, Query()] = False,
    ) -> dict:
        user_id = await check_permission(
            request, db, name, "list",
            require_auth=require_auth, public_actions=public_actions,
        )
        # Collect filter query params
        query_params = dict(request.query_params)

        return await handlers.handle_list(
            db, model,
            search=search,
            search_fields=search_fields,
            filter_fields=filter_fields,
            module_fields=module_fields,
            computed_fields=computed_fields,
            query_params=query_params,
            sort_by=sort_by_param or sort_by,
            sort_desc=sort_desc_param or sort_desc,
            skip=skip,
            limit=limit,
            max_page_size=max_page_size,
            archive=archive,
            with_archived=with_archived,
            user_id=user_id,
        )

    # ── META SCHEMA ── (must be before /{record_id} to avoid routing conflict!) ─

    @router.get("/meta/schema")
    async def meta_schema(request: Request, db: DBSession) -> dict:
        """Return field metadata for frontend dynamic rendering."""
        return handlers._success(data=module_cls._meta_schema())

    # ── GET ────────────────────────────────────────────────────────────────

    @router.get("/{record_id}")
    async def get_record(
        request: Request,
        db: DBSession,
        record_id: int,
    ) -> dict:
        await check_permission(
            request, db, name, "read",
            require_auth=require_auth, public_actions=public_actions,
        )
        return await handlers.handle_get(
            db, model, record_id,
            archive=archive,
            module_fields=module_fields,
            computed_fields=computed_fields,
        )

    # ── CREATE ────────────────────────────────────────────────────────────

    @router.post("/", status_code=201)
    async def create_record(
        request: Request,
        db: DBSession,
        body: create_schema,  # type: ignore[valid-type]
    ) -> dict:
        user_id = await check_permission(
            request, db, name, "create",
            require_auth=require_auth, public_actions=public_actions,
        )
        data = body.model_dump(exclude_unset=True)
        return await handlers.handle_create(
            db, model, data, user_id=user_id,
            module_fields=module_fields,
            computed_fields=computed_fields,
        )

    # ── UPDATE ────────────────────────────────────────────────────────────

    @router.put("/{record_id}")
    async def update_record(
        request: Request,
        db: DBSession,
        record_id: int,
        body: update_schema,  # type: ignore[valid-type]
    ) -> dict:
        user_id = await check_permission(
            request, db, name, "update",
            require_auth=require_auth, public_actions=public_actions,
        )
        data = body.model_dump(exclude_unset=True)
        # Strip readonly fields
        for rf in readonly_fields:
            data.pop(rf, None)
        return await handlers.handle_update(
            db, model, record_id, data,
            user_id=user_id,
            optimistic_lock=optimistic_lock,
            module_fields=module_fields,
            computed_fields=computed_fields,
        )

    # ── ARCHIVE (conditional) ─────────────────────────────────────────────

    if archive:
        @router.post("/{record_id}/archive")
        async def archive_record(
            request: Request,
            db: DBSession,
            record_id: int,
        ) -> dict:
            await check_permission(
                request, db, name, "archive",
                require_auth=require_auth, public_actions=public_actions,
            )
            return await handlers.handle_archive(db, model, record_id)

        @router.post("/{record_id}/restore")
        async def restore_record(
            request: Request,
            db: DBSession,
            record_id: int,
        ) -> dict:
            await check_permission(
                request, db, name, "restore",
                require_auth=require_auth, public_actions=public_actions,
            )
            return await handlers.handle_restore(db, model, record_id)

    # ── DELETE ────────────────────────────────────────────────────────────

    @router.delete("/{record_id}")
    async def delete_record(
        request: Request,
        db: DBSession,
        record_id: int,
    ) -> dict:
        await check_permission(
            request, db, name, "delete",
            require_auth=require_auth, public_actions=public_actions,
        )
        return await handlers.handle_delete(db, model, record_id)

    # ── BULK ──────────────────────────────────────────────────────────────

    @router.post("/bulk", status_code=201)
    async def bulk_import(
        request: Request,
        db: DBSession,
        items: list[dict[str, Any]],
        upsert: Annotated[bool, Query()] = False,
    ) -> dict:
        user_id = await check_permission(
            request, db, name, "bulk",
            require_auth=require_auth, public_actions=public_actions,
        )
        return await handlers.handle_bulk(
            db, model, items,
            user_id=user_id,
            bulk_fields=bulk_fields,
            upsert=upsert,
            module_fields=module_fields,
        )

    # ── UPLOAD (T065) ─────────────────────────────────────────────────────

    from base.fields import ImageField, FileField
    _upload_fields = [
        (fname, fdef)
        for fname, fdef in module_fields.items()
        if isinstance(fdef, (ImageField, FileField))
    ]

    if _upload_fields:
        from fastapi import UploadFile, File as FastAPIFile
        from base.upload import handle_upload

        for _upload_field_name, _upload_field_def in _upload_fields:
            # Capture by default arg
            def _make_upload_endpoint(field_name=_upload_field_name, field_def=_upload_field_def):
                @router.post(f"/{{record_id}}/upload/{field_name}", status_code=200)
                async def upload_file(
                    request: Request,
                    db: DBSession,
                    record_id: int,
                    file: UploadFile = FastAPIFile(...),
                ) -> dict:
                    user_id = await check_permission(
                        request, db, name, "update",
                        require_auth=require_auth, public_actions=public_actions,
                    )
                    return await handle_upload(
                        db=db,
                        model=model,
                        record_id=record_id,
                        field_name=field_name,
                        file=file,
                        module_name=name,
                        allowed_types=getattr(field_def, "allowed_types", []),
                        max_size_mb=getattr(field_def, "max_size_mb", 5),
                    )
            _make_upload_endpoint()

    return router

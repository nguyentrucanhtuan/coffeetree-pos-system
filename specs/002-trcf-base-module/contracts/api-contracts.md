# API Contracts: TRCFBaseModule CRUD Endpoints

**Date**: 2026-03-26  
**Feature**: 002-trcf-base-module

## Per-Module Endpoints (Auto-Generated)

Every TRCFBaseModule generates these 9 endpoints:

### 1. LIST — `GET /{name}/`

**Query Params**: `skip`, `limit`, `search`, `sort_by`, `sort_desc`, `with_archived`, `{filter_field}={prefix}value`  
**Auth**: Required (unless `_public_actions` includes `list`)  
**Permission**: `list`

```json
// Response 200
{
  "success": true,
  "data": {
    "total": 25,
    "items": [{"id": 1, "name": "...", ...}],
    "skip": 0,
    "limit": 10
  },
  "message": null
}
```

### 2. GET — `GET /{name}/{id}`

**Auth**: Required (unless `_public_actions` includes `read`)  
**Permission**: `read`

```json
// Response 200
{"success": true, "data": {"id": 1, "name": "...", ...}, "message": null}

// Response 404
{"success": false, "data": null, "message": "Record không tồn tại"}
```

### 3. CREATE — `POST /{name}/`

**Auth**: Required (unless `_public_actions` includes `create`)  
**Permission**: `create`  
**Body**: JSON matching Create schema

```json
// Response 201
{"success": true, "data": {"id": 1, ...}, "message": "Tạo thành công"}

// Response 422
{"success": false, "data": null, "message": "Validation error", "errors": [...]}
```

### 4. UPDATE — `PUT /{name}/{id}`

**Auth**: Required  
**Permission**: `update`  
**Body**: JSON matching Update schema (partial update)

```json
// Response 200
{"success": true, "data": {"id": 1, ...}, "message": "Cập nhật thành công"}

// Response 409 (optimistic lock)
{"success": false, "data": null, "message": "Conflict — record đã được sửa bởi người khác"}
```

### 5. ARCHIVE — `POST /{name}/{id}/archive`

**Auth**: Required  
**Permission**: `archive`  
**Only if**: `_archive=True`

```json
// Response 200
{"success": true, "data": null, "message": "Đã lưu trữ"}
```

### 6. RESTORE — `POST /{name}/{id}/restore`

**Auth**: Required  
**Permission**: `restore`  
**Only if**: `_archive=True`

```json
// Response 200
{"success": true, "data": null, "message": "Đã khôi phục"}
```

### 7. DELETE — `DELETE /{name}/{id}`

**Auth**: Required  
**Permission**: `delete`

```json
// Response 200
{"success": true, "data": null, "message": "Đã xóa vĩnh viễn"}
```

### 8. BULK — `POST /{name}/bulk`

**Auth**: Required  
**Permission**: `bulk`  
**Body**: JSON array of records  
**Transaction**: Atomic — rollback all on any failure

```json
// Response 201
{"success": true, "data": {"created": 8, "updated": 2}, "message": "Import thành công"}

// Response 422
{"success": false, "data": null, "message": "Import thất bại — đã rollback", "errors": [{"row": 5, "error": "..."}]}
```

### 9. META SCHEMA — `GET /{name}/meta/schema`

**Auth**: Required (or public if module is public)

```json
// Response 200
{
  "success": true,
  "data": {
    "module": "products",
    "description": "Thực đơn",
    "fields": [
      {"name": "id", "type": "integer", "label": "ID", "required": false, "readonly": true},
      {"name": "name", "type": "string", "label": "Tên", "required": true, "max_length": 255}
    ],
    "search_fields": ["name"],
    "filter_fields": ["category_id"],
    "sort_by": "name",
    "sort_desc": false,
    "archive": true,
    "has_settings": false,
    "computed_fields": []
  },
  "message": null
}
```

## System Endpoints (CMS Core — Manual)

### Menu — `GET /modules/menu`

**Auth**: Public (frontend needs this for sidebar)

```json
// Response 200
[
  {"name": "products", "menu_label": "Thực đơn", "menu_icon": "☕", "menu_parent": "inventory", "menu_sequence": 10, "has_settings": false}
]
```

### Settings — `GET /system-settings/?module_name={name}`

**Auth**: Required (superuser)

```json
// Response 200
{
  "success": true,
  "data": [
    {"module_name": "attendances", "key": "late_min", "value": "15", "value_type": "integer", "label": "Cho phép trễ (phút)"}
  ]
}
```

### Settings Update — `PUT /system-settings/{module_name}/{key}`

**Auth**: Required (superuser)  
**Body**: `{"value": "30"}`

```json
// Response 200
{"success": true, "data": null, "message": "Cập nhật thành công"}
```

## Error Codes

| HTTP | When |
|---|---|
| 200 | Success (read, update, archive, restore, delete) |
| 201 | Created (create, bulk) |
| 401 | Not authenticated |
| 403 | No permission |
| 404 | Record not found |
| 409 | Optimistic lock conflict |
| 422 | Validation error |

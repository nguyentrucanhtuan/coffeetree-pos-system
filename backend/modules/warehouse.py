"""Warehouse module — inventory & stock management."""

from base import fields
from base.module import TRCFBaseModule


# ── Warehouse locations ────────────────────────────────────────────────────────

class Warehouse(TRCFBaseModule):
    _name = "warehouses"
    _description = "Kho hàng"
    _search_fields = ["name", "code"]
    _filter_fields = ["is_active"]
    _sort_by = "name"
    _list_columns = ["code", "name", "location", "is_active"]

    _menu_label = "Kho hàng"
    _menu_icon = ""
    _menu_parent = "STOCK"
    _menu_sequence = 1

    # ── Settings ───────────────────────────────────────────────────────────────
    _settings: list[dict] = [
        {
            "key":     "low_stock_threshold",
            "label":   "Ngưỡng cảnh báo tồn kho thấp (%)",
            "type":    "integer",
            "default": "20",
        },
        {
            "key":     "auto_reorder",
            "label":   "Tự động đặt hàng khi hết",
            "type":    "boolean",
            "default": "false",
        },
        {
            "key":     "default_supplier_email",
            "label":   "Email nhà cung cấp mặc định",
            "type":    "string",
            "default": "",
        },
        {
            "key":     "stock_unit",
            "label":   "Đơn vị kho mặc định",
            "type":    "string",
            "default": "kg",
        },
    ]

    code        = fields.CharField(label="Mã kho", max_length=20, unique=True)
    name        = fields.CharField(label="Tên kho", required=True)
    location    = fields.TextField(label="Địa điểm")
    is_active   = fields.BooleanField(label="Hoạt động", default=True)
    notes       = fields.TextField(label="Ghi chú")

# ── Stock movement (import/export) ─────────────────────────────────────────────
class StockMovement(TRCFBaseModule):
    _name = "stock-movements"
    _description = "Nhập/Xuất kho"
    _search_fields = ["reference", "notes"]
    _filter_fields = ["movement_type", "warehouse_id", "product_id"]
    _sort_by = "created_at"
    _sort_desc = True
    _list_columns = ["reference", "movement_type", "product_id", "quantity", "unit_price", "warehouse_id", "created_at"]

    _menu_label = "Nhập/Xuất kho"
    _menu_icon = ""
    _menu_parent = "REPORT"
    _menu_sequence = 6

    reference       = fields.CharField(label="Số phiếu", max_length=50)
    movement_type   = fields.SelectionField(
        label="Loại",
        options=["import", "export", "adjustment", "transfer", "scrap"],
        required=True,
    )
    product_id     = fields.ForeignKeyField(label="Nguyên liệu", to="products", required=True)
    warehouse_id    = fields.ForeignKeyField(label="Kho", to="warehouses", required=True)
    quantity        = fields.DecimalField(label="Số lượng", precision=14, scale=3, required=True)
    unit_price      = fields.DecimalField(label="Đơn giá", precision=14, scale=2)
    total_value     = fields.DecimalField(label="Tổng giá trị", precision=14, scale=2)
    notes           = fields.TextField(label="Ghi chú")

"""Floor/Zone & Table management modules for POS seating."""

from base import fields
from base.module import TRCFBaseModule


# ── Khu vực / Tầng ────────────────────────────────────────────────────────────

class Zone(TRCFBaseModule):
    _name = "zones"
    _description = "Khu vực / Tầng"
    _search_fields = ["name", "code"]
    _filter_fields = ["zone_type", "sales_point_id", "is_active"]
    _sort_by = "sequence"
    _list_columns = ["code", "name", "zone_type", "floor_number", "sales_point_id", "is_active", "sequence"]

    _menu_label = "Khu vực"
    _menu_icon = ""
    _menu_parent = "SALE"
    _menu_sequence = 13

    code            = fields.CharField(label="Mã khu vực", max_length=20, unique=True)
    name            = fields.CharField(label="Tên khu vực", required=True)
    zone_type       = fields.SelectionField(
        label="Loại khu vực",
        options=["indoor", "outdoor", "rooftop", "vip", "bar", "takeaway", "other"],
        default="indoor",
    )
    floor_number    = fields.IntField(label="Số tầng", default=1)
    sales_point_id  = fields.ForeignKeyField(label="Điểm bán", to="sales-points")
    capacity        = fields.IntField(label="Sức chứa (người)")
    description     = fields.TextField(label="Mô tả")
    sequence        = fields.IntField(label="Thứ tự hiển thị", default=10)
    is_active       = fields.BooleanField(label="Đang hoạt động", default=True)


# ── Bàn ───────────────────────────────────────────────────────────────────────

class DiningTable(TRCFBaseModule):
    _name = "tables"
    _description = "Bàn"
    _search_fields = ["name", "code"]
    _filter_fields = ["zone_id", "table_status", "is_active"]
    _sort_by = "sequence"
    _list_columns = ["code", "name", "zone_id", "seats", "table_status", "is_active"]

    _menu_label = "Bàn"
    _menu_icon = ""
    _menu_parent = "SALE"
    _menu_sequence = 14

    code            = fields.CharField(label="Mã bàn", max_length=20, unique=True)
    name            = fields.CharField(label="Số bàn / Tên bàn", required=True)
    zone_id         = fields.ForeignKeyField(label="Khu vực", to="zones", required=True)
    seats           = fields.IntField(label="Số chỗ ngồi", default=4)
    table_status    = fields.SelectionField(
        label="Trạng thái",
        options=["available", "occupied", "reserved", "cleaning", "disabled"],
        default="available",
    )
    shape           = fields.SelectionField(
        label="Hình dạng bàn",
        options=["round", "square", "rectangle", "other"],
        default="square",
    )
    min_spend       = fields.DecimalField(label="Chi tiêu tối thiểu", precision=12, scale=2)
    notes           = fields.TextField(label="Ghi chú")
    sequence        = fields.IntField(label="Thứ tự", default=10)
    is_active       = fields.BooleanField(label="Đang dùng", default=True)
    qr_code         = fields.CharField(label="Mã QR (URL)", max_length=500)

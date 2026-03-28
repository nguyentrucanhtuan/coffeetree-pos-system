from base import fields
from base.module import TRCFBaseModule


# ── Warehouse locations ────────────────────────────────────────────────────────

class WorkShift(TRCFBaseModule):
    _name = "work-shifts"
    _description = "Ca làm việc"
    _search_fields = ["name"]
    _filter_fields = ["is_active"]
    _sort_by = "name"
    _list_columns = ["name"]

    _menu_label = "Ca làm việc"
    _menu_icon = ""
    _menu_parent = "STAFF"
    _menu_sequence = 1

    name        = fields.CharField(label="Tên Ca", required=True)
    checkin     = fields.TextField(label="Giờ vào")
    checkout    = fields.TextField(label="Giờ ra")
    notes       = fields.TextField(label="Ghi chú")
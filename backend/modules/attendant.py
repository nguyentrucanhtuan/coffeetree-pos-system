from base import fields
from base.module import TRCFBaseModule


# ── Warehouse locations ────────────────────────────────────────────────────────

class Attendant(TRCFBaseModule):
    _name = "attendants"
    _description = "Chấm công"
    _search_fields = ["employee_id"]
    _filter_fields = ["employee_id"]
    _sort_by = "employee_id"
    _list_columns = ["employee_id", "checkin", "checkout"]

    _menu_label = "Chấm công"
    _menu_icon = ""
    _menu_parent = "STAFF"
    _menu_sequence = 11

    # Settings
    _settings: list[dict] = [
        {
            "key":     "zktec_ip",
            "label":   "Địa chỉ IP máy chấm công",
            "type":    "string",
            "default": "192.168.1.234",
        },
        {
            "key":     "zktec_port",
            "label":   "Port máy chấm công",
            "type":    "integer",
            "default": "9091",
        },
        {
            "key":     "zktec_date_from",
            "label":   "Ngày bắt đầu",
            "type":    "date",
            "default": "01-03-2026",
        },
        {
            "key":     "zktec_date_to",
            "label":   "Ngày kết thúc",
            "type":    "date",
            "default": "31-03-2026",
        },
    ]
    employee_id = fields.ForeignKeyField(label="Nhân viên", to="employees", display_field="full_name")
    checkin     = fields.TextField(label="Thời gian vào")
    checkout    = fields.TextField(label="Thời gian ra")

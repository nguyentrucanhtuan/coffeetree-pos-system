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
    _menu_sequence = 8

    name        = fields.CharField(label="Tên Ca", required=True)
    checkin     = fields.TextField(label="Giờ vào")
    checkout    = fields.TextField(label="Giờ ra")
    notes       = fields.TextField(label="Ghi chú")

class WorkShiftRegister(TRCFBaseModule): 
    _name = "work-shift-registers"
    _description = "Đăng ký ca làm việc"
    _search_fields = ["employee", "date"]
    _filter_fields = ["employee", "date"]
    _sort_by = "date"
    _list_columns = ["employee", "date", "work_shift"]

    _menu_label = "Đăng ký ca"
    _menu_icon = ""
    _menu_parent = "STAFF"
    _menu_sequence = 9

    employee        = fields.ForeignKeyField(label="Nhân viên", to="employees", display_field="full_name")
    date            = fields.DateField(label="Ngày")
    work_shift      = fields.ForeignKeyField(label="Ca làm việc", to="work-shifts", display_field="name")
    status          = fields.SelectionField(label="Trạng thái", options=["pending", "approved", "rejected"])
    notes           = fields.TextField(label="Ghi chú")

class TaskTemplate(TRCFBaseModule): 
    _name = "task-templates"
    _description = "Mẫu công việc"
    _search_fields = ["name"]
    _sort_by = "name"
    _list_columns = ["name", "cycle_type", "time_from", "time_to", "is_active"]

    _menu_label = "Mẫu công việc"
    _menu_icon = ""
    _menu_parent = "STAFF"
    _menu_sequence = 10

    name               = fields.CharField(label="Tên công việc", required=True)
    description        = fields.TextField(label="Mô tả / Hướng dẫn")
    cycle_type         = fields.SelectionField(label="Chu kỳ", options=["daily", "weekly", "monthly"])
    time_from          = fields.TimeField(label="Từ giờ")
    time_to            = fields.TimeField(label="Đến giờ")
    is_active          = fields.BooleanField(label="Hoạt động", default=True)
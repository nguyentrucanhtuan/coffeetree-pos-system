"""Employee module — Human Resources management."""

from base import fields
from base.module import TRCFBaseModule


class Department(TRCFBaseModule):
    _name = "departments"
    _description = "Phòng ban"
    _search_fields = ["name"]
    _filter_fields = ["is_active"]
    _sort_by = "name"
    _list_columns = ["name", "is_active"]
    _archive = True

    # Menu
    _menu_label = "Phòng ban"
    _menu_icon = ""
    _menu_parent = "STAFF"
    _menu_sequence = 2

    # Fields
    name        = fields.CharField(label="Tên phòng ban", required=True, unique=True)
    is_active   = fields.BooleanField(label="Đang hoạt động", default=True)
    notes       = fields.TextField(label="Ghi chú")

class Employee(TRCFBaseModule):
    _name = "employees"
    _description = "Nhân viên"
    _search_fields = ["full_name", "code", "phone", "email"]
    _filter_fields = ["department", "position", "is_active"]
    _sort_by = "full_name"
    _list_columns = ["code", "full_name", "department", "position", "phone", "is_active"]
    _archive = True

    # Menu
    _menu_label = "Nhân viên"
    _menu_icon = ""
    _menu_parent = "STAFF"
    _menu_sequence = 3

    # Basic info
    code        = fields.CharField(label="Mã NV", max_length=20, unique=True)
    full_name   = fields.CharField(label="Họ tên", required=True)
    phone       = fields.CharField(label="Số điện thoại", max_length=20, ui_type="phone")
    email       = fields.CharField(label="Email", max_length=254, ui_type="email")
    address     = fields.TextField(label="Địa chỉ")
    birth_date  = fields.DateField(label="Ngày sinh")
    gender      = fields.SelectionField(label="Giới tính", options=["male", "female", "other"])
    id_number   = fields.CharField(label="CCCD/CMND", max_length=20)

    # Work info
    department          = fields.ForeignKeyField(label="Phòng ban", to="departments", display_field="name")
    position            = fields.CharField(label="Chức vụ")
    
    base_salary         = fields.DecimalField(label="Lương cơ bản", precision=14, scale=2)
    bank_account        = fields.CharField(label="Số tài khoản ngân hàng", max_length=50)
    bank_name           = fields.CharField(label="Ngân hàng", max_length=100)

    # Status
    is_active   = fields.BooleanField(label="Đang làm việc", default=True)
    avatar      = fields.ImageField(label="Ảnh đại diện")
    notes       = fields.TextField(label="Ghi chú nội bộ")

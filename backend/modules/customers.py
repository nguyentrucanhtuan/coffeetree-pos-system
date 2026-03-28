"""Customer module — CRM / loyalty management."""

from base import fields
from base.module import TRCFBaseModule


class Customer(TRCFBaseModule):
    _name = "customers"
    _description = "Khách hàng"
    _search_fields = ["full_name", "phone", "email", "code"]
    _filter_fields = ["customer_type", "is_active"]
    _sort_by = "full_name"
    _list_columns = ["code", "full_name", "phone", "customer_type", "loyalty_points", "total_spent", "is_active"]
    _archive = True

    # Menu
    _menu_label = "Khách hàng"
    _menu_icon = ""
    _menu_parent = "SALE"
    _menu_sequence = 17

    # Basic info
    code            = fields.CharField(label="Mã KH", max_length=20, unique=True)
    full_name       = fields.CharField(label="Họ tên khách hàng", required=True)
    phone           = fields.CharField(label="Số điện thoại", max_length=20, ui_type="phone")
    email           = fields.CharField(label="Email", max_length=254, ui_type="email")
    address         = fields.TextField(label="Địa chỉ")
    birth_date      = fields.DateField(label="Ngày sinh")
    gender          = fields.SelectionField(label="Giới tính", options=["male", "female", "other"])
    id_number       = fields.CharField(label="CCCD/CMND", max_length=20)

    # Segmentation
    customer_type   = fields.SelectionField(
        label="Loại khách hàng",
        options=["regular", "vip", "wholesale", "staff"],
        default="regular",
    )

    # Loyalty
    loyalty_points  = fields.IntField(label="Điểm tích lũy", default=0)
    total_spent     = fields.DecimalField(label="Tổng chi tiêu", precision=14, scale=2, default=0)
    first_visit     = fields.DateField(label="Ngày đầu tiên")
    last_visit      = fields.DateField(label="Ngày ghé gần nhất")
    visit_count     = fields.IntField(label="Số lần ghé", default=0)

    # Other
    is_active   = fields.BooleanField(label="Đang hoạt động", default=True)
    notes       = fields.TextField(label="Ghi chú")

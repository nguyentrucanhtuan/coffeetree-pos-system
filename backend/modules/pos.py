"""POS module — Point of Sale management."""

from base import fields
from base.module import TRCFBaseModule


# ── Sales locations ────────────────────────────────────────────────────────────

class SalesPoint(TRCFBaseModule):
    _name = "sales-points"
    _description = "POS"
    _search_fields = ["name", "code", "address"]
    _filter_fields = ["is_active"]
    _sort_by = "name"
    _list_columns = ["code", "name", "address", "phone", "is_active"]

    _menu_label = "POS"
    _menu_icon = ""
    _menu_parent = "SALE"
    _menu_sequence = 12

    code        = fields.CharField(label="Mã cửa hàng", max_length=20, unique=True)
    name        = fields.CharField(label="Tên điểm bán", required=True)
    address     = fields.TextField(label="Địa chỉ")
    phone       = fields.CharField(label="Điện thoại", max_length=20, ui_type="phone")
    manager     = fields.CharField(label="Quản lý")
    open_time   = fields.CharField(label="Giờ mở cửa", max_length=10)
    close_time  = fields.CharField(label="Giờ đóng cửa", max_length=10)
    is_active   = fields.BooleanField(label="Đang hoạt động", default=True)
    notes       = fields.TextField(label="Ghi chú")


# ── Orders ─────────────────────────────────────────────────────────────────────

class Order(TRCFBaseModule):
    _name = "orders"
    _description = "Đơn hàng"
    _search_fields = ["order_number", "customer_name", "customer_phone"]
    _filter_fields = ["status", "payment_method", "sales_point_id"]
    _sort_by = "created_at"
    _sort_desc = True
    _list_columns = [
        "order_number", "customer_name", "status", "total_amount",
        "payment_method", "sales_point_id", "created_at",
    ]
    _archive = True

    _menu_label = "Đơn hàng"
    _menu_icon = ""
    _menu_parent = "SALE"
    _menu_sequence = 17

    order_number        = fields.CharField(label="Số đơn hàng", max_length=50, unique=True)
    customer_name       = fields.CharField(label="Tên khách hàng")
    customer_phone      = fields.CharField(label="SĐT khách", max_length=20)
    customer_id         = fields.ForeignKeyField(label="Khách hàng", to="customers")
    sales_point_id      = fields.ForeignKeyField(label="Điểm bán", to="sales-points")
    cashier_id          = fields.ForeignKeyField(label="Thu ngân", to="employees")

    status              = fields.SelectionField(
        label="Trạng thái",
        options=["pending", "confirmed", "preparing", "ready", "completed", "cancelled", "refunded"],
        default="pending",
    )
    payment_method      = fields.SelectionField(
        label="Phương thức TT",
        options=["cash", "card", "momo", "vnpay", "bank_transfer", "loyalty_points"],
    )

    subtotal            = fields.DecimalField(label="Tạm tính", precision=14, scale=2)
    discount_amount     = fields.DecimalField(label="Giảm giá", precision=14, scale=2, default=0)
    tax_amount          = fields.DecimalField(label="Thuế", precision=14, scale=2, default=0)
    total_amount        = fields.DecimalField(label="Tổng cộng", precision=14, scale=2)

    loyalty_points_used = fields.IntField(label="Điểm TL dùng", default=0)
    loyalty_points_earned = fields.IntField(label="Điểm TL cộng", default=0)

    notes               = fields.TextField(label="Ghi chú")
    table_number        = fields.CharField(label="Số bàn", max_length=20)


# ── Order line items ───────────────────────────────────────────────────────────

class OrderItem(TRCFBaseModule):
    _name = "order-items"
    _description = "Chi tiết đơn hàng"
    _search_fields = []
    _filter_fields = ["order_id", "product_id"]
    _sort_by = "order_id"
    _sort_desc = True
    _list_columns = ["order_id", "product_id", "quantity", "unit_price", "discount", "line_total"]

    _menu_label = "Chi tiết đơn"
    _menu_icon = ""
    _menu_parent = "SALE"
    _menu_sequence = 18

    order_id        = fields.ForeignKeyField(label="Đơn hàng", to="orders", required=True)
    product_id      = fields.ForeignKeyField(label="Sản phẩm", to="products", required=True)
    product_name    = fields.CharField(label="Tên SP (snapshot)", max_length=200)
    quantity        = fields.IntField(label="Số lượng", required=True, default=1)
    unit_price      = fields.DecimalField(label="Đơn giá", precision=14, scale=2, required=True)
    discount        = fields.DecimalField(label="Giảm giá", precision=14, scale=2, default=0)
    line_total      = fields.DecimalField(label="Thành tiền", precision=14, scale=2)
    notes           = fields.CharField(label="Ghi chú dòng", max_length=200)

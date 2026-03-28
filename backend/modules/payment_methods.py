"""Payment Method module — manage accepted payment methods for POS."""

from base import fields
from base.module import TRCFBaseModule


class PaymentMethod(TRCFBaseModule):
    _name = "payment-methods"
    _description = "Phương thức thanh toán"
    _search_fields = ["name", "code"]
    _filter_fields = ["method_type", "is_active"]
    _sort_by = "sequence"
    _list_columns = ["code", "name", "method_type", "fee_percent", "is_active", "sequence"]
    _archive = False

    # Menu
    _menu_label = "Phương thức TT"
    _menu_icon = "💳"
    _menu_parent = "pos"
    _menu_sequence = 5

    # Core
    code        = fields.CharField(label="Mã", max_length=30, unique=True)
    name        = fields.CharField(label="Tên phương thức", required=True)
    method_type = fields.SelectionField(
        label="Loại",
        options=["cash", "card", "ewallet", "bank_transfer", "qr_code", "loyalty_points", "other"],
        required=True,
    )
    description = fields.TextField(label="Mô tả")
    icon        = fields.CharField(label="Icon (emoji)", max_length=10)
    sequence    = fields.IntField(label="Thứ tự hiển thị", default=10)

    # Fee / config
    fee_percent     = fields.DecimalField(label="Phí giao dịch (%)", precision=5, scale=2, default=0)
    min_amount      = fields.DecimalField(label="Số tiền tối thiểu", precision=14, scale=2, default=0)
    max_amount      = fields.DecimalField(label="Số tiền tối đa", precision=14, scale=2)

    # Provider / integration
    provider_name   = fields.CharField(label="Nhà cung cấp", max_length=100)
    merchant_id     = fields.CharField(label="Merchant ID", max_length=100)
    api_key         = fields.CharField(label="API Key (masked)", max_length=200)
    webhook_url     = fields.CharField(label="Webhook URL", max_length=500, ui_type="url")

    # Status
    is_active       = fields.BooleanField(label="Đang hoạt động", default=True)
    is_default      = fields.BooleanField(label="Mặc định", default=False)
    require_approval = fields.BooleanField(label="Cần duyệt thủ công", default=False)

    # Settings
    _settings: list[dict] = [
        {
            "key":     "default_payment_method",
            "label":   "Phương thức thanh toán mặc định",
            "type":    "string",
            "default": "cash",
        },
        {
            "key":     "allow_partial_payment",
            "label":   "Cho phép thanh toán một phần",
            "type":    "boolean",
            "default": "false",
        },
        {
            "key":     "round_to_nearest",
            "label":   "Làm tròn đến (0=tắt)",
            "type":    "integer",
            "default": "1000",
        },
    ]

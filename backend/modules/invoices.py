"""Product module — comprehensive canary with all field types."""

from base import fields
from base.module import TRCFBaseModule


class Tax(TRCFBaseModule):
    _name = "taxes"
    _description = "Thuế"
    _search_fields = ["name"]
    _filter_fields = ["tax_type"]
    _sort_by = "name"

    # Menu
    _menu_label = "Thuế"
    _menu_icon = ""
    _menu_parent = "INVOICE"
    _menu_sequence = 10

    # Fields
    name = fields.CharField(label="Tên thuế", required=True, unique=True)
    tax_type = fields.SelectionField(label="Loại thuế", options=["purchase_tax", "sales_tax"])
    percent = fields.DecimalField(label="Phần trăm thuế", precision=14, scale=2)
    is_active = fields.BooleanField(label="Hoạt động", default=True)

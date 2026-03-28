"""Bill of Materials (BoM) module — manage product recipes and component requirements."""

from base import fields
from base.module import TRCFBaseModule


# ── BoM Header ────────────────────────────────────────────────────────────────

class BoM(TRCFBaseModule):
    _name = "bom_headers"
    _description = "Định mức nguyên liệu (BoM)"
    _search_fields = ["code", "product_id"]
    _filter_fields = ["product_id", "is_active"]
    _sort_by = "product_id"
    _list_columns = ["code", "product_id", "quantity", "uom_id", "is_active"]

    _menu_label = "BoM"
    # Icon for BoM: Manufacturing/Recipe style
    _menu_icon = ""
    _menu_parent = "STOCK"
    _menu_sequence = 4

    code        = fields.CharField(label="Mã BoM", max_length=20, unique=True)
    product_id  = fields.ForeignKeyField(label="Sản phẩm thành phẩm", to="products", required=True)
    quantity    = fields.DecimalField(label="Số lượng thành phẩm", precision=12, scale=3, default=1, required=True)
    uom_id      = fields.ForeignKeyField(label="Đơn vị tính thành phẩm", to="units", required=True)
    
    lines       = fields.OneToManyField(label="Thành phần nguyên liệu", to="bom_lines", related_field="bom_id")

    is_active   = fields.BooleanField(label="Hoạt động", default=True)
    notes       = fields.TextField(label="Ghi chú công thức")


# ── BoM Line (Components) ─────────────────────────────────────────────────────

class BoMLine(TRCFBaseModule):
    _name = "bom_lines"
    _description = "Chi tiết định mức nguyên liệu"
    _search_fields = ["product_id"]
    _filter_fields = ["bom_id", "product_id"]
    _sort_by = "sequence"
    _list_columns = ["bom_id", "product_id", "quantity", "uom_id", "sequence"]

    _menu_label = "Chi tiết BoM"
    _menu_icon = ""
    _menu_parent = "STOCK"
    _menu_sequence = 41
    _menu_hidden = True # Hidden from main menu as it's usually managed within BoM

    bom_id      = fields.ForeignKeyField(label="Công thức BoM", to="bom_headers", required=True, on_delete="CASCADE")
    product_id  = fields.ForeignKeyField(label="Nguyên liệu/Thành phần", to="products", required=True)
    quantity    = fields.DecimalField(label="Số lượng tiêu hao", precision=12, scale=4, required=True)
    uom_id      = fields.ForeignKeyField(
        label="Đơn vị tính nguyên liệu",
        to="units",
        required=True,
        depends_on="product_id",
        help_text="Chọn đơn vị tính phù hợp cho nguyên liệu này"
    )
    
    sequence    = fields.IntField(label="Thứ tự", default=10)
    notes       = fields.CharField(label="Ghi chú dòng", max_length=200)

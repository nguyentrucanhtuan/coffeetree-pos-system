"""Product module — comprehensive canary with all field types."""

from base import fields
from base.module import TRCFBaseModule

class Unit(TRCFBaseModule):
    _name = "units"
    _description = "Đơn vị tính"
    _search_fields = ["name"]
    _sort_by = "name"

    # Menu
    _menu_label = "Đơn vị tính"
    _menu_icon = ""
    _menu_parent = "STOCK"
    _menu_sequence = 1

    # Fields
    name = fields.CharField(label="Tên đơn vị tính", required=True, unique=True)
    relative_factor = fields.FloatField(label="Hệ số quy đổi", required=True)
    relative_uom_id = fields.ForeignKeyField(label="Đơn vị tính quy đổi", to="units")
    is_active = fields.BooleanField(label="Hoạt động", default=True)


class Category(TRCFBaseModule):
    _name = "categories"
    _description = "Danh mục sản phẩm"
    _search_fields = ["name"]
    _sort_by = "name"

    # Menu
    _menu_label = "Danh mục"
    _menu_icon = ""
    _menu_parent = "STOCK"
    _menu_sequence = 2

    # Fields
    name = fields.CharField(label="Tên danh mục", required=True, unique=True)
    image = fields.ImageField(label="Ảnh danh mục")
    is_active = fields.BooleanField(label="Hoạt động", default=True)

class Product(TRCFBaseModule):
    _name = "products"
    _description = "Sản phẩm"
    _search_fields = ["name", "sku"]
    _filter_fields = ["category_id", "is_active"]
    _list_columns = ["name", "sku", "price", "category_id", "is_active", "image", "tracking_stock"]
    _sort_by = "name"
    _readonly_fields = ["sku"]

    # Menu
    _menu_label = "Sản phẩm"
    _menu_icon = ""
    _menu_parent = "STOCK"
    _menu_sequence = 3

    # Fields
    name = fields.CharField(label="Tên sản phẩm", required=True)
    sku = fields.CharField(label="SKU", max_length=50, unique=True)
    price = fields.DecimalField(label="Giá bán", precision=12, scale=2, required=True)
    cost_price = fields.DecimalField(label="Giá vốn", precision=12, scale=2)
    category_id = fields.ForeignKeyField(label="Danh mục", to="categories", required=True)
    is_active = fields.BooleanField(label="Hoạt động", default=True)
    image = fields.ImageField(label="Ảnh sản phẩm")
    description = fields.TextField(label="Mô tả")
    tracking_stock = fields.BooleanField(label="Theo dõi hàng tồn", default=True)

    purchase_check = fields.BooleanField(label="Có thể mua", default=True)
    sale_check = fields.BooleanField(label="Có thể bán", default=True)
    manufacture_check = fields.BooleanField(label="Có thể chế biến", default=True)

    purchase_taxes = fields.ManyToManyField(label="Thuế mua hàng", to="taxes", domain={"tax_type": "purchase_tax"})
    sale_taxes = fields.ManyToManyField(label="Thuế bán hàng", to="taxes", domain={"tax_type": "sales_tax"})

    unit_id = fields.ForeignKeyField(label="Đơn vị tính chính", to="units", required=True)
    unit_ids = fields.ManyToManyField(label="Đơn vị tính phụ", to="units")
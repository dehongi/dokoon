from django.contrib import admin
from .models import (
    Warehouse,
    StockItem,
    InventoryTransaction,
    Supplier,
    PurchaseOrder,
    PurchaseOrderItem,
    InventoryAdjustment,
    InventoryAdjustmentItem,
    InventoryTransfer,
    InventoryTransferItem,
)


class StockItemInline(admin.TabularInline):
    model = StockItem
    extra = 0
    readonly_fields = ("total_value",)


class WarehouseAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "code",
        "city",
        "country",
        "total_stock_items",
        "total_inventory_value",
        "is_active",
    )
    list_filter = ("is_active", "country", "city")
    search_fields = ("name", "code", "address", "city")
    readonly_fields = ("total_inventory_value", "total_stock_items")
    inlines = [StockItemInline]
    fieldsets = (
        (None, {"fields": ("name", "code", "is_active")}),
        (
            "Location Information",
            {"fields": ("address", "city", "state", "country", "postal_code")},
        ),
        ("Contact Information", {"fields": ("phone", "email")}),
        (
            "Inventory Summary",
            {"fields": ("total_inventory_value", "total_stock_items")},
        ),
        ("Additional Information", {"fields": ("notes",)}),
    )


class InventoryTransactionInline(admin.TabularInline):
    model = InventoryTransaction
    extra = 0
    readonly_fields = ("timestamp",)


class StockItemAdmin(admin.ModelAdmin):
    list_display = (
        "product",
        "variation",
        "warehouse",
        "quantity",
        "min_stock_level",
        "max_stock_level",
        "is_low_stock",
        "is_over_stock",
        "total_value",
    )
    list_filter = ("warehouse",)
    search_fields = ("product__name", "variation__value", "location_code")
    readonly_fields = ("total_value", "is_low_stock", "is_over_stock")
    inlines = [InventoryTransactionInline]

    def is_low_stock(self, obj):
        return obj.is_low_stock

    is_low_stock.boolean = True
    is_low_stock.short_description = "Low Stock"

    def is_over_stock(self, obj):
        return obj.is_over_stock

    is_over_stock.boolean = True
    is_over_stock.short_description = "Over Stock"


class InventoryTransactionAdmin(admin.ModelAdmin):
    list_display = (
        "stock_item",
        "transaction_type",
        "quantity",
        "unit_cost",
        "reference_number",
        "performed_by",
        "timestamp",
    )
    list_filter = ("transaction_type", "timestamp")
    search_fields = ("stock_item__product__name", "reference_number", "notes")
    readonly_fields = ("timestamp",)
    date_hierarchy = "timestamp"


class SupplierAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "code",
        "contact_person",
        "email",
        "phone",
        "lead_time_days",
        "is_active",
    )
    list_filter = ("is_active", "lead_time_days")
    search_fields = ("name", "code", "contact_person", "email", "phone")
    fieldsets = (
        (None, {"fields": ("name", "code", "is_active")}),
        (
            "Contact Information",
            {"fields": ("contact_person", "email", "phone", "address", "website")},
        ),
        ("Business Terms", {"fields": ("payment_terms", "lead_time_days")}),
        ("Additional Information", {"fields": ("notes",)}),
    )


class PurchaseOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 0
    readonly_fields = ("subtotal",)


class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = (
        "order_number",
        "supplier",
        "warehouse",
        "status",
        "order_date",
        "total_with_tax_shipping",
        "items_count",
    )
    list_filter = ("status", "order_date", "warehouse")
    search_fields = ("order_number", "supplier__name", "notes")
    readonly_fields = (
        "total_with_tax_shipping",
        "items_count",
        "created_at",
        "updated_at",
    )
    inlines = [PurchaseOrderItemInline]
    date_hierarchy = "order_date"
    fieldsets = (
        (None, {"fields": ("order_number", "supplier", "warehouse", "status")}),
        (
            "Dates",
            {"fields": ("order_date", "expected_delivery_date", "delivery_date")},
        ),
        (
            "Financial Details",
            {
                "fields": (
                    "total_amount",
                    "shipping_cost",
                    "tax_amount",
                    "total_with_tax_shipping",
                )
            },
        ),
        ("Users", {"fields": ("created_by", "approved_by")}),
        ("Additional Information", {"fields": ("notes",)}),
        (
            "System Fields",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


class InventoryAdjustmentItemInline(admin.TabularInline):
    model = InventoryAdjustmentItem
    extra = 0
    readonly_fields = ("quantity_change",)


class InventoryAdjustmentAdmin(admin.ModelAdmin):
    list_display = (
        "adjustment_number",
        "warehouse",
        "adjustment_type",
        "date",
        "created_by",
        "approved_by",
    )
    list_filter = ("adjustment_type", "date", "warehouse")
    search_fields = ("adjustment_number", "notes")
    inlines = [InventoryAdjustmentItemInline]
    date_hierarchy = "date"
    fieldsets = (
        (
            None,
            {"fields": ("adjustment_number", "warehouse", "adjustment_type", "date")},
        ),
        ("Users", {"fields": ("created_by", "approved_by")}),
        ("Additional Information", {"fields": ("notes",)}),
    )


class InventoryTransferItemInline(admin.TabularInline):
    model = InventoryTransferItem
    extra = 0


class InventoryTransferAdmin(admin.ModelAdmin):
    list_display = (
        "transfer_number",
        "source_warehouse",
        "destination_warehouse",
        "status",
        "shipping_date",
        "arrival_date",
    )
    list_filter = (
        "status",
        "shipping_date",
        "source_warehouse",
        "destination_warehouse",
    )
    search_fields = ("transfer_number", "notes")
    inlines = [InventoryTransferItemInline]
    date_hierarchy = "shipping_date"
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "transfer_number",
                    "source_warehouse",
                    "destination_warehouse",
                    "status",
                )
            },
        ),
        (
            "Dates",
            {"fields": ("shipping_date", "expected_arrival_date", "arrival_date")},
        ),
        ("Users", {"fields": ("created_by",)}),
        ("Additional Information", {"fields": ("notes",)}),
    )


admin.site.register(Warehouse, WarehouseAdmin)
admin.site.register(StockItem, StockItemAdmin)
admin.site.register(InventoryTransaction, InventoryTransactionAdmin)
admin.site.register(Supplier, SupplierAdmin)
admin.site.register(PurchaseOrder, PurchaseOrderAdmin)
admin.site.register(InventoryAdjustment, InventoryAdjustmentAdmin)
admin.site.register(InventoryTransfer, InventoryTransferAdmin)

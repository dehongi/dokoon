from django.contrib import admin
from .models import (
    VendorCategory,
    Vendor,
    VendorContact,
    VendorProduct,
    VendorPriceList,
    VendorPriceListItem,
    PurchaseRequisition,
    PurchaseRequisitionItem,
    RFQ,
    RFQItem,
    RFQVendor,
    RFQVendorItem,
    ProcurementAttachment,
    VendorPerformance,
)


class VendorContactInline(admin.TabularInline):
    model = VendorContact
    extra = 1


class VendorProductInline(admin.TabularInline):
    model = VendorProduct
    extra = 1
    fields = (
        "product",
        "variation",
        "vendor_product_code",
        "standard_price",
        "minimum_order_quantity",
        "lead_time_days",
        "is_preferred_vendor",
    )


class VendorAttachmentInline(admin.TabularInline):
    model = ProcurementAttachment
    extra = 1
    fields = ("name", "attachment_type", "file", "description")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(vendor__isnull=False)


class VendorPerformanceInline(admin.TabularInline):
    model = VendorPerformance
    extra = 0
    fields = (
        "evaluation_date",
        "evaluator",
        "quality_rating",
        "delivery_rating",
        "price_rating",
        "service_rating",
        "overall_rating",
    )
    readonly_fields = ("overall_rating",)


class VendorCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name", "description")


class VendorAdmin(admin.ModelAdmin):
    list_display = (
        "supplier",
        "vendor_type",
        "status",
        "overall_rating",
        "onboarding_date",
    )
    list_filter = ("vendor_type", "status", "categories")
    search_fields = ("supplier__name", "supplier__code", "tax_id", "account_number")
    readonly_fields = ("overall_rating",)
    inlines = [
        VendorContactInline,
        VendorProductInline,
        VendorAttachmentInline,
        VendorPerformanceInline,
    ]
    fieldsets = (
        (None, {"fields": ("supplier", "vendor_type", "status", "categories")}),
        (
            "Financial Information",
            {"fields": ("tax_id", "account_number", "credit_terms", "credit_limit")},
        ),
        (
            "Ratings",
            {
                "fields": (
                    "quality_rating",
                    "delivery_rating",
                    "price_rating",
                    "overall_rating",
                )
            },
        ),
        (
            "Additional Information",
            {
                "fields": (
                    "certifications",
                    "onboarding_date",
                    "last_review_date",
                    "notes",
                )
            },
        ),
    )


class VendorContactAdmin(admin.ModelAdmin):
    list_display = ("name", "vendor", "contact_type", "email", "phone", "is_primary")
    list_filter = ("contact_type", "is_primary")
    search_fields = ("name", "vendor__supplier__name", "email", "phone")


class VendorProductAdmin(admin.ModelAdmin):
    list_display = (
        "product",
        "variation",
        "vendor",
        "standard_price",
        "minimum_order_quantity",
        "lead_time_days",
        "is_preferred_vendor",
    )
    list_filter = ("is_preferred_vendor", "vendor")
    search_fields = ("product__name", "vendor__supplier__name", "vendor_product_code")


class VendorPriceListItemInline(admin.TabularInline):
    model = VendorPriceListItem
    extra = 1


class VendorPriceListAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "vendor",
        "effective_date",
        "expiration_date",
        "is_active",
        "is_expired",
    )
    list_filter = ("is_active", "vendor")
    search_fields = ("name", "vendor__supplier__name")
    readonly_fields = ("is_expired",)
    inlines = [VendorPriceListItemInline]


class PurchaseRequisitionItemInline(admin.TabularInline):
    model = PurchaseRequisitionItem
    extra = 1
    fields = (
        "product",
        "variation",
        "quantity",
        "estimated_unit_price",
        "subtotal",
        "suggested_vendor",
    )
    readonly_fields = ("subtotal",)


class RequisitionAttachmentInline(admin.TabularInline):
    model = ProcurementAttachment
    extra = 0
    fields = ("name", "attachment_type", "file", "description")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(requisition__isnull=False)


class PurchaseRequisitionAdmin(admin.ModelAdmin):
    list_display = (
        "requisition_number",
        "status",
        "requester",
        "warehouse",
        "date_required",
        "total_estimated_cost",
        "created_at",
    )
    list_filter = ("status", "warehouse", "requester")
    search_fields = ("requisition_number", "requester__email", "notes")
    readonly_fields = ("created_at", "updated_at")
    inlines = [PurchaseRequisitionItemInline, RequisitionAttachmentInline]
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "requisition_number",
                    "status",
                    "requester",
                    "department",
                    "warehouse",
                )
            },
        ),
        (
            "Details",
            {
                "fields": (
                    "date_required",
                    "total_estimated_cost",
                    "justification",
                    "notes",
                )
            },
        ),
        ("Approval", {"fields": ("approver", "approval_date", "rejection_reason")}),
        (
            "System Fields",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


class RFQItemInline(admin.TabularInline):
    model = RFQItem
    extra = 1


class RFQVendorInline(admin.TabularInline):
    model = RFQVendor
    extra = 1
    fields = (
        "vendor",
        "status",
        "contact",
        "date_invited",
        "date_quote_received",
        "total_quoted_amount",
        "quoted_lead_time_days",
    )


class RFQAttachmentInline(admin.TabularInline):
    model = ProcurementAttachment
    extra = 0
    fields = ("name", "attachment_type", "file", "description")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(rfq__isnull=False)


class RFQAdmin(admin.ModelAdmin):
    list_display = (
        "rfq_number",
        "title",
        "status",
        "requisition",
        "issue_date",
        "response_deadline",
        "requester",
    )
    list_filter = ("status", "issue_date", "requester")
    search_fields = ("rfq_number", "title", "description")
    readonly_fields = ("created_at", "updated_at")
    inlines = [RFQItemInline, RFQVendorInline, RFQAttachmentInline]
    fieldsets = (
        (None, {"fields": ("rfq_number", "title", "status", "requisition")}),
        ("Description", {"fields": ("description", "terms_and_conditions")}),
        (
            "Dates",
            {"fields": ("issue_date", "response_deadline", "expected_delivery_date")},
        ),
        ("Responsible Persons", {"fields": ("requester", "assigned_to")}),
        ("Additional Information", {"fields": ("notes",)}),
        (
            "System Fields",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


class RFQVendorItemInline(admin.TabularInline):
    model = RFQVendorItem
    extra = 1
    fields = ("rfq_item", "unit_price", "lead_time_days", "subtotal", "is_selected")
    readonly_fields = ("subtotal",)


class RFQVendorAttachmentInline(admin.TabularInline):
    model = ProcurementAttachment
    extra = 0
    fields = ("name", "attachment_type", "file", "description")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(rfq_vendor__isnull=False)


class RFQVendorAdmin(admin.ModelAdmin):
    list_display = (
        "rfq",
        "vendor",
        "status",
        "date_invited",
        "date_quote_received",
        "total_quoted_amount",
        "quoted_lead_time_days",
    )
    list_filter = ("status", "date_invited", "date_quote_received")
    search_fields = ("rfq__rfq_number", "vendor__supplier__name", "notes")
    inlines = [RFQVendorItemInline, RFQVendorAttachmentInline]


class VendorPerformanceAdmin(admin.ModelAdmin):
    list_display = (
        "vendor",
        "evaluation_date",
        "quality_rating",
        "delivery_rating",
        "price_rating",
        "service_rating",
        "overall_rating",
    )
    list_filter = ("evaluation_date", "vendor")
    search_fields = ("vendor__supplier__name", "comments")
    readonly_fields = ("overall_rating",)
    fieldsets = (
        (None, {"fields": ("vendor", "evaluation_date", "evaluator")}),
        (
            "Ratings",
            {
                "fields": (
                    "quality_rating",
                    "delivery_rating",
                    "price_rating",
                    "service_rating",
                    "overall_rating",
                )
            },
        ),
        (
            "Performance Metrics",
            {
                "fields": (
                    "on_time_delivery_rate",
                    "quality_rejection_rate",
                    "response_time_days",
                )
            },
        ),
        (
            "Evaluation Details",
            {"fields": ("comments", "areas_of_improvement", "recommendations")},
        ),
    )


admin.site.register(VendorCategory, VendorCategoryAdmin)
admin.site.register(Vendor, VendorAdmin)
admin.site.register(VendorContact, VendorContactAdmin)
admin.site.register(VendorProduct, VendorProductAdmin)
admin.site.register(VendorPriceList, VendorPriceListAdmin)
admin.site.register(PurchaseRequisition, PurchaseRequisitionAdmin)
admin.site.register(RFQ, RFQAdmin)
admin.site.register(RFQVendor, RFQVendorAdmin)
admin.site.register(VendorPerformance, VendorPerformanceAdmin)

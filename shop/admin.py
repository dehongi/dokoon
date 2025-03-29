from django.contrib import admin
from .models import (
    Category,
    Product,
    ProductImage,
    ProductVariation,
    Cart,
    CartItem,
    Order,
    OrderItem,
    Coupon,
    Wishlist,
    Review,
    ShippingMethod,
    PaymentMethod,
)


class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "parent", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


class ProductVariationInline(admin.TabularInline):
    model = ProductVariation
    extra = 1


class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "price",
        "sale_price",
        "availability",
        "quantity",
        "is_featured",
        "is_active",
    )
    list_filter = ("availability", "is_featured", "is_active", "categories")
    search_fields = ("name", "description", "sku")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ProductImageInline, ProductVariationInline]
    filter_horizontal = ("categories",)
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (None, {"fields": ("name", "slug", "sku", "description", "categories")}),
        ("Pricing", {"fields": ("price", "sale_price", "cost_price")}),
        ("Inventory", {"fields": ("quantity", "availability")}),
        ("Shipping", {"fields": ("weight", "dimensions")}),
        ("Display Options", {"fields": ("is_featured", "is_active")}),
        (
            "SEO",
            {"fields": ("meta_keywords", "meta_description"), "classes": ("collapse",)},
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ("total_price",)


class CartAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "session_id",
        "total_items",
        "total_price",
        "created_at",
    )
    list_filter = ("created_at",)
    search_fields = ("user__email", "session_id")
    readonly_fields = ("total_price", "total_items")
    inlines = [CartItemInline]


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("subtotal",)


class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "order_number",
        "user",
        "status",
        "payment_status",
        "total_amount",
        "created_at",
    )
    list_filter = ("status", "payment_status", "created_at")
    search_fields = ("order_number", "user__email", "email", "phone")
    readonly_fields = ("order_number", "final_total", "created_at", "updated_at")
    inlines = [OrderItemInline]
    fieldsets = (
        (None, {"fields": ("order_number", "user", "status", "email", "phone")}),
        (
            "Financial Details",
            {
                "fields": (
                    "total_amount",
                    "shipping_amount",
                    "tax_amount",
                    "discount_amount",
                    "final_total",
                )
            },
        ),
        ("Payment Information", {"fields": ("payment_method", "payment_status")}),
        (
            "Shipping Information",
            {"fields": ("shipping_address", "billing_address", "tracking_number")},
        ),
        ("Additional Information", {"fields": ("notes",)}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


class CouponAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "discount_amount",
        "discount_percentage",
        "valid_from",
        "valid_to",
        "is_active",
    )
    list_filter = ("is_active", "valid_from", "valid_to")
    search_fields = ("code", "description")
    readonly_fields = ("used_count",)


class WishlistAdmin(admin.ModelAdmin):
    list_display = ("user", "product", "added_at")
    list_filter = ("added_at",)
    search_fields = ("user__email", "product__name")


class ReviewAdmin(admin.ModelAdmin):
    list_display = (
        "product",
        "user",
        "rating",
        "is_verified_purchase",
        "is_approved",
        "created_at",
    )
    list_filter = ("rating", "is_verified_purchase", "is_approved", "created_at")
    search_fields = ("product__name", "user__email", "title", "comment")
    actions = ["approve_reviews"]

    def approve_reviews(self, request, queryset):
        queryset.update(is_approved=True)

    approve_reviews.short_description = "Approve selected reviews"


class ShippingMethodAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "estimated_days", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "description")


class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "description")


admin.site.register(Category, CategoryAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Cart, CartAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(Coupon, CouponAdmin)
admin.site.register(Wishlist, WishlistAdmin)
admin.site.register(Review, ReviewAdmin)
admin.site.register(ShippingMethod, ShippingMethodAdmin)
admin.site.register(PaymentMethod, PaymentMethodAdmin)

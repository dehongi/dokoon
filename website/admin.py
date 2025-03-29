from django.contrib import admin
from django.utils.html import format_html
from .models import (
    SiteSettings,
    Page,
    FAQ,
    Testimonial,
    ContactMessage,
    TeamMember,
    Banner,
)


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    """Admin for site settings (singleton)"""

    fieldsets = (
        (
            "General Information",
            {
                "fields": (
                    "site_name",
                    "site_description",
                    "contact_email",
                    "contact_phone",
                    "address",
                )
            },
        ),
        (
            "Social Media",
            {
                "fields": (
                    "facebook_url",
                    "twitter_url",
                    "instagram_url",
                    "linkedin_url",
                    "youtube_url",
                )
            },
        ),
        (
            "SEO & Analytics",
            {"fields": ("meta_keywords", "meta_description", "google_analytics_id")},
        ),
    )

    def has_add_permission(self, request):
        # Only allow one site settings instance
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of the site settings
        return False


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    """Admin for static pages"""

    list_display = ("title", "page_type", "slug", "is_active", "updated_at")
    list_filter = ("page_type", "is_active")
    search_fields = ("title", "content")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (None, {"fields": ("title", "slug", "page_type", "content", "is_active")}),
        (
            "SEO",
            {"fields": ("meta_title", "meta_description"), "classes": ("collapse",)},
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    """Admin for FAQs"""

    list_display = ("question", "category", "order", "is_active")
    list_filter = ("category", "is_active")
    search_fields = ("question", "answer")
    list_editable = ("order", "is_active")
    fieldsets = (
        (None, {"fields": ("question", "answer", "category", "order", "is_active")}),
    )


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    """Admin for testimonials"""

    list_display = (
        "name",
        "position",
        "rating",
        "display_on_homepage",
        "order",
        "is_active",
    )
    list_filter = ("rating", "display_on_homepage", "is_active")
    search_fields = ("name", "position", "content")
    list_editable = ("order", "display_on_homepage", "is_active")

    fieldsets = (
        (None, {"fields": ("name", "position", "photo", "content", "rating")}),
        ("Display Options", {"fields": ("is_active", "display_on_homepage", "order")}),
    )

    def photo_preview(self, obj):
        """Display photo thumbnail in admin"""
        if obj.photo:
            return format_html(
                '<img src="{}" width="50" height="50" style="border-radius: 50%;" />',
                obj.photo.url,
            )
        return "-"

    photo_preview.short_description = "Photo"


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    """Admin for contact messages"""

    list_display = ("name", "email", "subject", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("name", "email", "subject", "message")
    readonly_fields = (
        "name",
        "email",
        "phone",
        "subject",
        "message",
        "ip_address",
        "created_at",
    )

    fieldsets = (
        (
            "Message Information",
            {"fields": ("name", "email", "phone", "subject", "message")},
        ),
        ("Admin", {"fields": ("status", "admin_notes", "ip_address", "created_at")}),
    )

    def has_add_permission(self, request):
        # Prevent adding contact messages manually
        return False


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    """Admin for team members"""

    list_display = ("name", "position", "photo_preview", "order", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "position", "bio")
    list_editable = ("order", "is_active")

    fieldsets = (
        (None, {"fields": ("name", "position", "photo", "bio")}),
        ("Contact Information", {"fields": ("email", "linkedin", "twitter")}),
        ("Display Options", {"fields": ("order", "is_active")}),
    )

    def photo_preview(self, obj):
        """Display photo thumbnail in admin"""
        if obj.photo:
            return format_html(
                '<img src="{}" width="50" height="50" style="border-radius: 50%;" />',
                obj.photo.url,
            )
        return "-"

    photo_preview.short_description = "Photo"


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    """Admin for banners"""

    list_display = ("title", "image_preview", "display_on", "order", "is_active")
    list_filter = ("display_on", "is_active")
    search_fields = ("title", "subtitle")
    list_editable = ("order", "is_active")

    fieldsets = (
        (None, {"fields": ("title", "subtitle", "image")}),
        ("Link", {"fields": ("link", "button_text")}),
        ("Display Options", {"fields": ("display_on", "order", "is_active")}),
    )

    def image_preview(self, obj):
        """Display image thumbnail in admin"""
        if obj.image:
            return format_html(
                '<img src="{}" width="100" height="50" style="object-fit: cover;" />',
                obj.image.url,
            )
        return "-"

    image_preview.short_description = "Banner Preview"

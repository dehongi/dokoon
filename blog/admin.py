from django.contrib import admin
from .models import Category, Tag, Author, Post, Comment, PostView


class PostInline(admin.TabularInline):
    model = Post.categories.through
    extra = 1
    verbose_name = "Post"
    verbose_name_plural = "Posts"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "post_count", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [PostInline]

    def post_count(self, obj):
        return obj.posts.count()

    post_count.short_description = "Posts"


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "post_count", "created_at")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}

    def post_count(self, obj):
        return obj.posts.count()

    post_count.short_description = "Posts"


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    readonly_fields = ("author_name", "author_email", "content", "created_at")
    fields = ("author_name", "content", "is_approved", "created_at")
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ("full_name", "user_email", "post_count", "website")
    search_fields = ("user__first_name", "user__last_name", "user__email", "bio")
    readonly_fields = ("post_count",)
    fieldsets = (
        (None, {"fields": ("user", "bio", "profile_picture")}),
        (
            "Social Media",
            {"fields": ("website", "facebook", "twitter", "instagram", "linkedin")},
        ),
    )

    def full_name(self, obj):
        return obj.full_name

    def user_email(self, obj):
        return obj.user.email

    def post_count(self, obj):
        return obj.post_count

    user_email.short_description = "Email"
    full_name.short_description = "Name"
    post_count.short_description = "Posts"


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "author",
        "post_type",
        "status",
        "published_at",
        "comment_count",
        "is_featured",
    )
    list_filter = ("status", "post_type", "is_featured", "categories", "created_at")
    search_fields = ("title", "content", "excerpt")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("created_at", "updated_at", "reading_time")
    date_hierarchy = "created_at"
    filter_horizontal = ("categories", "tags", "related_products")

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "title",
                    "slug",
                    "author",
                    "content",
                    "excerpt",
                    "featured_image",
                )
            },
        ),
        (
            "Categorization",
            {"fields": ("categories", "tags", "post_type", "related_products")},
        ),
        (
            "Publication",
            {"fields": ("status", "is_featured", "allow_comments", "published_at")},
        ),
        (
            "Promotion Settings",
            {
                "classes": ("collapse",),
                "fields": ("promotion_code", "promotion_end_date"),
            },
        ),
        (
            "SEO",
            {
                "classes": ("collapse",),
                "fields": ("meta_title", "meta_description", "meta_keywords"),
            },
        ),
        (
            "Meta",
            {
                "classes": ("collapse",),
                "fields": ("created_at", "updated_at", "reading_time"),
            },
        ),
    )

    inlines = [CommentInline]

    def comment_count(self, obj):
        return obj.comment_count

    comment_count.short_description = "Comments"

    def save_model(self, request, obj, form, change):
        if not change:  # If creating a new post
            if not obj.author:
                # Create author if one doesn't exist for the current user
                author, created = Author.objects.get_or_create(
                    user=request.user,
                    defaults={
                        "bio": request.user.bio if hasattr(request.user, "bio") else ""
                    },
                )
                obj.author = author
        super().save_model(request, obj, form, change)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("author_name", "post", "created_at", "is_approved", "has_parent")
    list_filter = ("is_approved", "created_at")
    search_fields = ("author_name", "author_email", "content", "post__title")
    readonly_fields = (
        "post",
        "author_name",
        "author_email",
        "content",
        "parent",
        "created_at",
        "ip_address",
    )
    actions = ["approve_comments", "unapprove_comments"]

    def has_parent(self, obj):
        return obj.parent is not None

    has_parent.boolean = True
    has_parent.short_description = "Reply"

    def approve_comments(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f"{updated} comments approved.")

    def unapprove_comments(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, f"{updated} comments unapproved.")

    approve_comments.short_description = "Approve selected comments"
    unapprove_comments.short_description = "Unapprove selected comments"


@admin.register(PostView)
class PostViewAdmin(admin.ModelAdmin):
    list_display = ("post", "viewed_at", "ip_address", "user")
    list_filter = ("viewed_at",)
    search_fields = ("post__title", "ip_address", "user_agent")
    readonly_fields = ("post", "ip_address", "user", "user_agent", "viewed_at")
    date_hierarchy = "viewed_at"

    def has_add_permission(self, request):
        return False

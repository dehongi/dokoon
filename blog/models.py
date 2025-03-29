from django.db import models
from django.utils import timezone
from django.urls import reverse
from django.utils.text import slugify
from accounts.models import CustomUser


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("blog:category_detail", kwargs={"slug": self.slug})


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=70, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("blog:tag_detail", kwargs={"slug": self.slug})


class Author(models.Model):
    user = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, related_name="author_profile"
    )
    bio = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(
        upload_to="blog/authors/", blank=True, null=True
    )
    website = models.URLField(blank=True, null=True)
    facebook = models.URLField(blank=True, null=True)
    twitter = models.URLField(blank=True, null=True)
    instagram = models.URLField(blank=True, null=True)
    linkedin = models.URLField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"

    def get_absolute_url(self):
        return reverse("blog:author_detail", kwargs={"pk": self.pk})

    @property
    def full_name(self):
        return f"{self.user.first_name} {self.user.last_name}"

    @property
    def post_count(self):
        return self.posts.count()


class Post(models.Model):
    STATUS_CHOICES = (
        ("draft", "Draft"),
        ("published", "Published"),
        ("archived", "Archived"),
    )

    POST_TYPES = (
        ("article", "Article"),
        ("news", "News"),
        ("promotion", "Promotion"),
        ("announcement", "Announcement"),
        ("tutorial", "Tutorial"),
    )

    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, unique=True)
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="posts")
    content = models.TextField()
    excerpt = models.TextField(
        blank=True,
        null=True,
        help_text="A short description of the post. If left empty, it will be auto-generated from content.",
    )
    featured_image = models.ImageField(
        upload_to="blog/featured_images/", blank=True, null=True
    )
    categories = models.ManyToManyField(Category, related_name="posts")
    tags = models.ManyToManyField(Tag, related_name="posts", blank=True)
    post_type = models.CharField(max_length=20, choices=POST_TYPES, default="article")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")

    # Promotion-specific fields
    promotion_end_date = models.DateTimeField(
        blank=True, null=True, help_text="End date for promotions"
    )
    promotion_code = models.CharField(max_length=50, blank=True, null=True)

    # Meta fields
    is_featured = models.BooleanField(default=False)
    allow_comments = models.BooleanField(default=True)

    # Related products (if promoting specific products)
    related_products = models.ManyToManyField(
        "shop.Product", blank=True, related_name="blog_posts"
    )

    # SEO fields
    meta_title = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        help_text="SEO meta title (if different from post title)",
    )
    meta_description = models.TextField(
        blank=True, null=True, help_text="SEO meta description"
    )
    meta_keywords = models.CharField(
        max_length=255, blank=True, null=True, help_text="Comma-separated keywords"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-published_at", "-created_at"]
        indexes = [
            models.Index(fields=["-published_at"]),
            models.Index(fields=["status"]),
            models.Index(fields=["post_type"]),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)

        # Auto-generate excerpt if not provided
        if not self.excerpt and self.content:
            if len(self.content) > 250:
                self.excerpt = self.content[:250] + "..."
            else:
                self.excerpt = self.content

        # Set published_at when post is published
        if self.status == "published" and not self.published_at:
            self.published_at = timezone.now()

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("blog:post_detail", kwargs={"slug": self.slug})

    @property
    def reading_time(self):
        """Estimate reading time in minutes based on average reading speed of 200 words per minute"""
        word_count = len(self.content.split())
        minutes = word_count / 200
        if minutes < 1:
            return "Less than a minute"
        return f"{round(minutes)} min read"

    @property
    def comment_count(self):
        return self.comments.filter(is_approved=True).count()

    @property
    def is_promotion_active(self):
        if self.post_type != "promotion":
            return False
        if not self.promotion_end_date:
            return True
        return self.promotion_end_date > timezone.now()


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    author_name = models.CharField(max_length=100)
    author_email = models.EmailField()
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="blog_comments",
    )
    content = models.TextField()
    is_approved = models.BooleanField(default=False)
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="replies"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Comment by {self.author_name} on {self.post.title}"


class PostView(models.Model):
    """Track post views for analytics"""

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="views")
    ip_address = models.GenericIPAddressField()
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="post_views",
    )
    user_agent = models.CharField(max_length=255, blank=True, null=True)
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-viewed_at"]

    def __str__(self):
        return f"View on {self.post.title} at {self.viewed_at}"

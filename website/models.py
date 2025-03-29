from django.db import models
from django.utils.translation import gettext_lazy as _


class SiteSettings(models.Model):
    """Model for storing site-wide settings"""

    site_name = models.CharField(max_length=100)
    site_description = models.TextField(blank=True, null=True)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    # Social media links
    facebook_url = models.URLField(blank=True, null=True)
    twitter_url = models.URLField(blank=True, null=True)
    instagram_url = models.URLField(blank=True, null=True)
    linkedin_url = models.URLField(blank=True, null=True)
    youtube_url = models.URLField(blank=True, null=True)

    # SEO fields
    meta_keywords = models.CharField(max_length=255, blank=True, null=True)
    meta_description = models.TextField(blank=True, null=True)

    # Analytics
    google_analytics_id = models.CharField(max_length=50, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Site Settings")
        verbose_name_plural = _("Site Settings")

    def __str__(self):
        return self.site_name

    def save(self, *args, **kwargs):
        # Make sure we only have one instance of SiteSettings
        if not self.pk and SiteSettings.objects.exists():
            return SiteSettings.objects.first()
        return super().save(*args, **kwargs)


class Page(models.Model):
    """Model for static pages like About, Terms, Privacy, etc."""

    TYPES = (
        ("about", _("About Us")),
        ("terms", _("Terms and Conditions")),
        ("privacy", _("Privacy Policy")),
        ("faq", _("FAQ")),
        ("help", _("Help Center")),
        ("custom", _("Custom Page")),
    )

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    content = models.TextField()
    page_type = models.CharField(max_length=10, choices=TYPES, default="custom")

    # SEO fields
    meta_title = models.CharField(max_length=150, blank=True, null=True)
    meta_description = models.TextField(blank=True, null=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Page")
        verbose_name_plural = _("Pages")
        ordering = ["title"]

    def __str__(self):
        return self.title


class FAQ(models.Model):
    """Frequently Asked Questions"""

    CATEGORIES = (
        ("general", _("General")),
        ("account", _("Account")),
        ("orders", _("Orders & Shipping")),
        ("payment", _("Payment")),
        ("returns", _("Returns & Refunds")),
        ("products", _("Products")),
        ("technical", _("Technical")),
        ("other", _("Other")),
    )

    question = models.CharField(max_length=255)
    answer = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORIES, default="general")
    order = models.PositiveIntegerField(default=0, help_text=_("Order of display"))
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("FAQ")
        verbose_name_plural = _("FAQs")
        ordering = ["category", "order"]

    def __str__(self):
        return self.question


class Testimonial(models.Model):
    """Customer testimonials"""

    name = models.CharField(max_length=100)
    position = models.CharField(
        max_length=100, blank=True, null=True, help_text=_("Job title or company")
    )
    photo = models.ImageField(upload_to="testimonials/", blank=True, null=True)
    content = models.TextField()
    rating = models.PositiveSmallIntegerField(default=5, help_text=_("Rating from 1-5"))
    is_active = models.BooleanField(default=True)
    display_on_homepage = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Testimonial")
        verbose_name_plural = _("Testimonials")
        ordering = ["order", "-created_at"]

    def __str__(self):
        return f"Testimonial from {self.name}"


class ContactMessage(models.Model):
    """Messages from contact form"""

    STATUS_CHOICES = (
        ("new", _("New")),
        ("in_progress", _("In Progress")),
        ("resolved", _("Resolved")),
        ("spam", _("Spam")),
    )

    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True, null=True)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default="new")
    admin_notes = models.TextField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Contact Message")
        verbose_name_plural = _("Contact Messages")
        ordering = ["-created_at"]

    def __str__(self):
        return f"Message from {self.name} - {self.subject}"


class TeamMember(models.Model):
    """Team members for about page"""

    name = models.CharField(max_length=100)
    position = models.CharField(max_length=100)
    bio = models.TextField()
    photo = models.ImageField(upload_to="team/")
    email = models.EmailField(blank=True, null=True)
    linkedin = models.URLField(blank=True, null=True)
    twitter = models.URLField(blank=True, null=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = _("Team Member")
        verbose_name_plural = _("Team Members")
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class Banner(models.Model):
    """Hero banners for homepage and other pages"""

    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=255, blank=True, null=True)
    image = models.ImageField(upload_to="banners/")
    link = models.URLField(blank=True, null=True)
    button_text = models.CharField(max_length=50, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    display_on = models.CharField(
        max_length=20, default="home", help_text=_("Page to display this banner on")
    )
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Banner")
        verbose_name_plural = _("Banners")
        ordering = ["order"]

    def __str__(self):
        return self.title

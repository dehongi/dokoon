from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils.text import slugify
from django.conf import settings
from .models import Post, Author, Category, Tag


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_or_update_author_profile(sender, instance, created, **kwargs):
    """
    Create an Author profile automatically when a new user is created,
    or update it when the user is updated.
    """
    if created:
        # Only create Author profile for staff users by default
        if instance.is_staff:
            Author.objects.get_or_create(user=instance)
    else:
        # Update the Author profile if it exists
        try:
            author = Author.objects.get(user=instance)
            # If user's name or profile pic has changed, update the author profile
            has_changes = False

            # If user has profile picture and author doesn't, copy it
            if (
                hasattr(instance, "profile_picture")
                and instance.profile_picture
                and not author.profile_picture
            ):
                author.profile_picture = instance.profile_picture
                has_changes = True

            # If user has bio and author doesn't, copy it
            if hasattr(instance, "bio") and instance.bio and not author.bio:
                author.bio = instance.bio
                has_changes = True

            if has_changes:
                author.save()
        except Author.DoesNotExist:
            # Don't auto-create for existing users unless they're staff
            pass


@receiver(pre_save, sender=Post)
def ensure_unique_slug(sender, instance, **kwargs):
    """
    Ensure that each post has a unique slug. If the slug already exists,
    append a number to the end.
    """
    if not instance.slug:
        # Generate slug from title
        instance.slug = slugify(instance.title)

    # Check if this slug already exists, excluding the current instance
    query = Post.objects.filter(slug=instance.slug)
    if instance.pk:
        query = query.exclude(pk=instance.pk)

    if query.exists():
        # Slug exists, generate a unique one
        original_slug = instance.slug
        counter = 1
        while Post.objects.filter(slug=instance.slug).exclude(pk=instance.pk).exists():
            instance.slug = f"{original_slug}-{counter}"
            counter += 1


@receiver(pre_save, sender=Category)
def ensure_unique_category_slug(sender, instance, **kwargs):
    """Ensure unique slug for categories"""
    if not instance.slug:
        instance.slug = slugify(instance.name)

    # Check if this slug already exists, excluding the current instance
    query = Category.objects.filter(slug=instance.slug)
    if instance.pk:
        query = query.exclude(pk=instance.pk)

    if query.exists():
        # Slug exists, generate a unique one
        original_slug = instance.slug
        counter = 1
        while (
            Category.objects.filter(slug=instance.slug).exclude(pk=instance.pk).exists()
        ):
            instance.slug = f"{original_slug}-{counter}"
            counter += 1


@receiver(pre_save, sender=Tag)
def ensure_unique_tag_slug(sender, instance, **kwargs):
    """Ensure unique slug for tags"""
    if not instance.slug:
        instance.slug = slugify(instance.name)

    # Check if this slug already exists, excluding the current instance
    query = Tag.objects.filter(slug=instance.slug)
    if instance.pk:
        query = query.exclude(pk=instance.pk)

    if query.exists():
        # Slug exists, generate a unique one
        original_slug = instance.slug
        counter = 1
        while Tag.objects.filter(slug=instance.slug).exclude(pk=instance.pk).exists():
            instance.slug = f"{original_slug}-{counter}"
            counter += 1

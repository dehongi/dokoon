from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Count, Q
from django.utils import timezone
from django.http import JsonResponse
from .models import Post, Category, Tag, Author, Comment, PostView
from .forms import CommentForm, PostSearchForm, AuthorProfileForm


class PostListView(ListView):
    model = Post
    template_name = "blog/post_list.html"
    context_object_name = "posts"
    paginate_by = 10

    def get_queryset(self):
        queryset = Post.objects.filter(status="published").select_related(
            "author__user"
        )

        # Filter by category
        category_slug = self.kwargs.get("category_slug")
        if category_slug:
            queryset = queryset.filter(categories__slug=category_slug)

        # Filter by tag
        tag_slug = self.kwargs.get("tag_slug")
        if tag_slug:
            queryset = queryset.filter(tags__slug=tag_slug)

        # Filter by author
        author_id = self.kwargs.get("author_id")
        if author_id:
            queryset = queryset.filter(author_id=author_id)

        # Filter by post type
        post_type = self.kwargs.get("post_type")
        if post_type:
            queryset = queryset.filter(post_type=post_type)

        # Search query
        search_query = self.request.GET.get("search")
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query)
                | Q(content__icontains=search_query)
                | Q(excerpt__icontains=search_query)
            )

        return queryset.prefetch_related("categories", "tags")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Add category to context if filtering by category
        category_slug = self.kwargs.get("category_slug")
        if category_slug:
            context["category"] = get_object_or_404(Category, slug=category_slug)

        # Add tag to context if filtering by tag
        tag_slug = self.kwargs.get("tag_slug")
        if tag_slug:
            context["tag"] = get_object_or_404(Tag, slug=tag_slug)

        # Add author to context if filtering by author
        author_id = self.kwargs.get("author_id")
        if author_id:
            context["author"] = get_object_or_404(Author, id=author_id)

        # Add search query to context
        context["search_query"] = self.request.GET.get("search", "")

        # Add categories and popular tags for sidebar
        context["categories"] = (
            Category.objects.filter(is_active=True)
            .annotate(post_count=Count("posts"))
            .order_by("-post_count")[:10]
        )

        context["popular_tags"] = Tag.objects.annotate(
            post_count=Count("posts")
        ).order_by("-post_count")[:20]

        # Add featured posts
        context["featured_posts"] = Post.objects.filter(
            status="published", is_featured=True
        ).order_by("-published_at")[:5]

        return context


class PostDetailView(DetailView):
    model = Post
    template_name = "blog/post_detail.html"
    context_object_name = "post"

    def get_queryset(self):
        if self.request.user.is_staff:
            # Staff can preview any post
            return Post.objects.all()
        # Public can only see published posts
        return Post.objects.filter(status="published")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = self.object

        # Get related posts
        post_tags_ids = post.tags.values_list("id", flat=True)
        post_categories_ids = post.categories.values_list("id", flat=True)

        # First try to find related posts by tags and categories
        if post_tags_ids.exists():
            related_posts = (
                Post.objects.filter(
                    status="published",
                    tags__in=post_tags_ids,
                    categories__in=post_categories_ids,
                )
                .exclude(id=post.id)
                .distinct()
            )
        else:
            # If no tags, just find by categories
            related_posts = Post.objects.filter(
                status="published", categories__in=post_categories_ids
            ).exclude(id=post.id)

        context["related_posts"] = related_posts.order_by("-published_at")[:3]

        # Get approved comments
        context["comments"] = (
            post.comments.filter(is_approved=True, parent__isnull=True)
            .order_by("-created_at")
            .select_related("user")
        )

        # Add comment form
        context["comment_form"] = CommentForm()

        # Record post view
        if not self.request.user.is_staff:  # Don't count staff views
            self._record_view()

        return context

    def _record_view(self):
        """Record a view for this post"""
        post = self.object
        user = self.request.user if self.request.user.is_authenticated else None
        ip_address = self.request.META.get("REMOTE_ADDR", "")
        user_agent = self.request.META.get("HTTP_USER_AGENT", "")

        # Create PostView record
        PostView.objects.create(
            post=post, user=user, ip_address=ip_address, user_agent=user_agent
        )


def add_comment(request, slug):
    """Add a comment to a post"""
    post = get_object_or_404(Post, slug=slug, status="published")

    # Check if comments are allowed
    if not post.allow_comments:
        messages.error(request, "Comments are not allowed for this post.")
        return redirect("blog:post_detail", slug=slug)

    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            # Create a new comment object
            comment = form.save(commit=False)
            comment.post = post

            # If user is authenticated, associate the comment with them
            if request.user.is_authenticated:
                comment.user = request.user
                comment.author_name = (
                    f"{request.user.first_name} {request.user.last_name}"
                )
                comment.author_email = request.user.email

            # Handle reply to comment
            parent_id = request.POST.get("parent_id")
            if parent_id:
                try:
                    parent = Comment.objects.get(id=parent_id, post=post)
                    comment.parent = parent
                except Comment.DoesNotExist:
                    pass

            # Record IP address
            comment.ip_address = request.META.get("REMOTE_ADDR", "")

            # Auto-approve comments from authenticated users
            if request.user.is_authenticated:
                comment.is_approved = True

            comment.save()

            messages.success(
                request,
                (
                    "Your comment has been submitted. It will be visible after moderation."
                    if not comment.is_approved
                    else "Your comment has been published."
                ),
            )
        else:
            messages.error(request, "There was a problem with your comment submission.")

    return redirect("blog:post_detail", slug=slug)


class CategoryListView(ListView):
    model = Category
    template_name = "blog/category_list.html"
    context_object_name = "categories"

    def get_queryset(self):
        return (
            Category.objects.filter(is_active=True)
            .annotate(post_count=Count("posts", filter=Q(posts__status="published")))
            .order_by("name")
        )


class TagListView(ListView):
    model = Tag
    template_name = "blog/tag_list.html"
    context_object_name = "tags"

    def get_queryset(self):
        return Tag.objects.annotate(
            post_count=Count("posts", filter=Q(posts__status="published"))
        ).order_by("name")


class AuthorDetailView(DetailView):
    model = Author
    template_name = "blog/author_detail.html"
    context_object_name = "author"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        author = self.object

        # Get author's published posts
        context["posts"] = Post.objects.filter(
            author=author, status="published"
        ).order_by("-published_at")

        return context

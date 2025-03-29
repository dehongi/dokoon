from django.urls import path
from . import views

app_name = "blog"

urlpatterns = [
    # Post listing views
    path("", views.PostListView.as_view(), name="post_list"),
    path(
        "category/<slug:category_slug>/",
        views.PostListView.as_view(),
        name="category_posts",
    ),
    path("tag/<slug:tag_slug>/", views.PostListView.as_view(), name="tag_posts"),
    path("author/<int:author_id>/", views.PostListView.as_view(), name="author_posts"),
    path("type/<str:post_type>/", views.PostListView.as_view(), name="post_type_list"),
    # Post detail view
    path("post/<slug:slug>/", views.PostDetailView.as_view(), name="post_detail"),
    path("post/<slug:slug>/comment/", views.add_comment, name="add_comment"),
    # Category and tag listing views
    path("categories/", views.CategoryListView.as_view(), name="category_list"),
    path("tags/", views.TagListView.as_view(), name="tag_list"),
    # Author detail view
    path(
        "author/profile/<int:pk>/",
        views.AuthorDetailView.as_view(),
        name="author_detail",
    ),
]

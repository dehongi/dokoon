from django.urls import path
from . import views

app_name = "shop"

urlpatterns = [
    # Product URLs
    path("", views.product_list, name="product_list"),
    path(
        "category/<slug:category_slug>/",
        views.product_list,
        name="product_list_by_category",
    ),
    path("product/<slug:slug>/", views.product_detail, name="product_detail"),
    # Cart URLs
    path("cart/", views.cart_detail, name="cart_detail"),
    path("cart/add/<int:product_id>/", views.add_to_cart, name="add_to_cart"),
    path("cart/update/<int:item_id>/", views.update_cart, name="update_cart"),
    path("cart/remove/<int:item_id>/", views.remove_from_cart, name="remove_from_cart"),
    # Wishlist URLs
    path("wishlist/", views.wishlist, name="wishlist"),
    path(
        "wishlist/add/<int:product_id>/", views.add_to_wishlist, name="add_to_wishlist"
    ),
    path(
        "wishlist/remove/<int:wishlist_id>/",
        views.remove_from_wishlist,
        name="remove_from_wishlist",
    ),
]
